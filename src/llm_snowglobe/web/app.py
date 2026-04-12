#!/usr/bin/env python3

"""FastAPI web application for Snowglobe simulations.

Can run locally (`uvicorn llm_snowglobe.web.app:app`) or be mounted
inside a Modal container via `modal_app.py`.
"""

import asyncio
import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ruamel.yaml import YAML

from ..core.llm import load_pools


def create_app(config_dir: str | Path | None = None):
    """Factory to create the FastAPI app with a given config directory."""

    app = FastAPI(title="Snowglobe", description="LLM Wargaming Simulator")

    # Resolve paths
    pkg_dir = Path(__file__).resolve().parent
    if config_dir is None:
        config_dir = pkg_dir.parent.parent.parent / "config"
    config_dir = Path(config_dir)
    static_dir = pkg_dir / "static"

    # In-memory run storage
    runs: dict[str, dict] = {}

    # --- Models ---

    class RunRequest(BaseModel):
        scenario: str
        pool: str
        refs: list[str] = []

    # --- Static files ---

    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # --- Routes ---

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_dir / "index.html"
        if not index_path.exists():
            return HTMLResponse("<h1>Snowglobe</h1><p>Static files not found.</p>")
        return index_path.read_text()

    @app.get("/api/scenarios")
    async def list_scenarios():
        scenarios_dir = config_dir / "scenarios"
        if not scenarios_dir.is_dir():
            return []

        yaml = YAML(typ="safe")
        results = []
        for f in sorted(scenarios_dir.iterdir()):
            if f.suffix in (".yaml", ".yml"):
                try:
                    data = yaml.load(f.read_text())
                    results.append({
                        "id": f.stem,
                        "title": data.get("title", f.stem),
                        "actor_cluster": data.get("actor_cluster", "inline"),
                        "moves": data.get("moves", "?"),
                        "timestep": data.get("timestep", "?"),
                    })
                except Exception:
                    results.append({"id": f.stem, "title": f.stem, "error": True})
        return results

    @app.get("/api/pools")
    async def list_pools_route():
        pools_path = config_dir / "pools.yaml"
        if not pools_path.exists():
            return []

        pools, active, _ = load_pools(str(pools_path))
        results = []
        for name, pool in pools.items():
            results.append({
                "name": name,
                "active": name == active,
                "planner": pool.planner,
                "player": pool.player,
            })
        return results

    @app.post("/api/run")
    async def start_run(req: RunRequest):
        scenario_path = config_dir / "scenarios" / f"{req.scenario}.yaml"
        if not scenario_path.exists():
            raise HTTPException(404, f"Scenario not found: {req.scenario}")

        pools_path = config_dir / "pools.yaml"
        pools, _, base_url = load_pools(str(pools_path))
        if req.pool not in pools:
            raise HTTPException(404, f"Pool not found: {req.pool}")

        run_id = str(uuid.uuid4())[:8]
        log_queue: asyncio.Queue = asyncio.Queue()

        runs[run_id] = {
            "status": "starting",
            "log": log_queue,
            "result": None,
            "pdf_path": None,
        }

        asyncio.create_task(_run_simulation(
            runs=runs,
            run_id=run_id,
            scenario_path=str(scenario_path),
            pool_name=req.pool,
            pool=pools[req.pool],
            base_url=base_url,
            pools_path=str(pools_path),
            reference_urls=req.refs or None,
            log_queue=log_queue,
        ))

        return {"run_id": run_id}

    @app.get("/api/run/{run_id}/stream")
    async def stream_run(run_id: str):
        if run_id not in runs:
            raise HTTPException(404, "Run not found")

        async def generate():
            queue = runs[run_id]["log"]
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=120)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                    continue
                if event is None:
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.get("/api/run/{run_id}/result")
    async def get_result(run_id: str):
        if run_id not in runs:
            raise HTTPException(404, "Run not found")

        run = runs[run_id]
        if run["status"] in ("starting", "running"):
            return {"status": run["status"]}

        result = run.get("result", {})
        return {
            "status": run["status"],
            "title": result.get("title", ""),
            "assessments": result.get("assessments", []),
            "history": [
                {"name": e.get("name", ""), "text": e.get("text", "")[:500]}
                for e in result.get("history", [])
                if e.get("name") not in ("Narrator", "Briefing")
            ],
            "pdf_filename": run.get("pdf_path"),
        }

    @app.get("/api/reports/{filename}")
    async def serve_report(filename: str):
        # Sanitise
        filename = Path(filename).name
        pdf_path = Path(".snowglobe_data/reports") / filename
        if not pdf_path.exists():
            raise HTTPException(404, "Report not found")
        return FileResponse(str(pdf_path), media_type="application/pdf")

    return app


async def _run_simulation(runs, run_id, scenario_path, pool_name, pool,
                          base_url, pools_path, reference_urls, log_queue):
    """Run a simulation and push log events to the queue."""
    from ..scenario_runner import run_scenario

    run = runs[run_id]
    run["status"] = "running"

    await log_queue.put({"type": "status", "message": f"Starting with pool '{pool_name}'..."})

    try:
        result = await run_scenario(
            scenario_path=scenario_path,
            pool_name=pool_name,
            pool_override=pool,
            base_url=base_url,
            pools_path=pools_path,
            verbosity=0,
            use_rich=False,
            report=True,
            reference_urls=reference_urls,
        )

        run["result"] = result
        run["status"] = "complete"

        reports_dir = Path(".snowglobe_data/reports")
        if reports_dir.exists():
            pdfs = sorted(reports_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pdfs:
                run["pdf_path"] = pdfs[0].name

        await log_queue.put({
            "type": "complete",
            "message": "Simulation complete",
            "assessments": result.get("assessments", []),
        })

    except Exception as e:
        run["status"] = "error"
        await log_queue.put({"type": "error", "message": str(e)})

    await log_queue.put(None)


# Default app instance for local use / uvicorn
app = create_app()


def main():
    """Entry point for snowglobe-web CLI."""
    import uvicorn

    port = int(os.environ.get("SNOWGLOBE_PORT", "8000"))
    print(f"\n  Snowglobe Web GUI")
    print(f"  http://localhost:{port}")
    print()

    uvicorn.run(
        "llm_snowglobe.web.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
