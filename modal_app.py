"""Modal deployment for Geopol Forecaster wargaming simulator.

Architecture:
  - Webhook endpoint receives authenticated POST to trigger simulations
  - run_simulation function does the heavy lifting (SITREP + sim + report)
  - Results returned to caller or stored in persistent volume

Deploy:   modal deploy modal_app.py
Trigger:  POST https://carrotcakeai--geopol-webhook.modal.run
          Header: X-Webhook-Secret: <secret>
          Body: {"scenario": "iran-israel-war", "pool": "deepseek", "refs": [...]}
"""

import modal

app = modal.App("geopol")

# --- Image ---

geopol_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("wget", "fontconfig")
    # Install Typst binary
    .run_commands(
        "wget -qO- https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
        " | tar xJf - --wildcards --strip-components=1 -C /usr/local/bin/ '*/typst'",
    )
    # Install IBM Plex Sans font
    .run_commands(
        "mkdir -p /usr/share/fonts/ibm-plex",
        "for w in Regular Bold Medium Light; do"
        "  wget -qO /usr/share/fonts/ibm-plex/IBMPlexSans-${w}.ttf"
        "  https://github.com/google/fonts/raw/main/ofl/ibmplexsans/IBMPlexSans-${w}.ttf"
        "  || true;"
        " done",
        "fc-cache -f",
    )
    .pip_install(
        "langgraph",
        "openai",
        "tavily-python",
        "trafilatura",
        "ruamel.yaml",
        "rich",
        "edge-tts",
        "fastapi",
        "uvicorn",
        "httpx",
        "watchfiles",
        "nicegui",
        "markdown2",
        "pydantic",
        "platformdirs",
    )
    .add_local_dir("src/geopol_forecaster", remote_path="/root/src/geopol_forecaster", copy=True)
    .add_local_dir("config", remote_path="/root/config", copy=True)
    .run_commands(
        # Remove stale llm_snowglobe package if cached from a previous image
        "rm -rf /root/src/llm_snowglobe",
        "cd /root && PYTHONPATH=/root/src python -c 'import geopol_forecaster; print(\"package OK\")'",
    )
)

# --- Secrets ---
# modal secret create geopol-secrets \
#   OPENROUTER_API_KEY=... \
#   TAVILY_API_KEY=... \
#   SNOWGLOBE_WEBHOOK_SECRET=...

secrets = modal.Secret.from_name("geopol-secrets")

# --- Persistent volume for reports ---

reports_volume = modal.Volume.from_name("geopol-reports", create_if_missing=True)


# --- Simulation function (long-running) ---

@app.function(
    image=geopol_image,
    secrets=[secrets],
    volumes={"/data/reports": reports_volume},
    timeout=1800,  # 30 min max
    memory=1024,
)
async def run_simulation(scenario_name: str, pool_name: str,
                         reference_urls: list[str] | None = None,
                         timeframes: list[str] | None = None) -> dict:
    """Run a full geopol simulation and return results."""
    import sys
    import os
    import shutil

    # Ensure stale llm_snowglobe package (old name) doesn't shadow geopol_forecaster
    stale = "/root/src/llm_snowglobe"
    if os.path.isdir(stale):
        shutil.rmtree(stale)

    sys.path.insert(0, "/root/src")
    os.chdir("/root")

    os.makedirs("/data/reports", exist_ok=True)
    os.makedirs(".geopol_data/reports", exist_ok=True)

    from geopol_forecaster.scenario_runner import run_scenario
    from geopol_forecaster.core.llm import load_pools

    scenario_path = f"/root/config/scenarios/{scenario_name}.yaml"
    pools_path = "/root/config/pools.yaml"

    pools, _, base_url = load_pools(pools_path)
    pool = pools.get(pool_name)
    if not pool:
        return {"error": f"Pool not found: {pool_name}",
                "available_pools": list(pools.keys())}

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
        track_predictions=False,
    )

    # Copy report to persistent volume
    import shutil
    from pathlib import Path
    reports_dir = Path(".geopol_data/reports")
    pdf_filename = None
    if reports_dir.exists():
        for pdf in reports_dir.glob("*.pdf"):
            shutil.copy2(pdf, f"/data/reports/{pdf.name}")
            pdf_filename = pdf.name
        reports_volume.commit()

    return {
        "status": "complete",
        "title": result.get("title", ""),
        "assessments": result.get("assessments", []),
        "history": [
            {"name": e.get("name", ""), "text": e.get("text", "")}
            for e in result.get("history", [])
            if e.get("name") not in ("Narrator", "Briefing")
        ],
        "briefing": result.get("briefing", ""),
        "pdf_filename": pdf_filename,
        "moves_total": result.get("moves_total"),
        "timestep": result.get("timestep"),
    }


# --- Webhook endpoint ---

@app.function(
    image=geopol_image,
    secrets=[secrets],
    volumes={"/data/reports": reports_volume},
)
@modal.concurrent(max_inputs=5)
@modal.asgi_app()
def webhook():
    """Authenticated webhook for triggering simulations."""
    import os
    import json
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    from pathlib import Path

    api = FastAPI(title="Geopol Forecaster Webhook")
    WEBHOOK_SECRET = os.environ.get("SNOWGLOBE_WEBHOOK_SECRET", "")

    def _check_auth(request: Request):
        secret = (
            request.headers.get("x-webhook-secret")
            or request.query_params.get("secret")
        )
        if WEBHOOK_SECRET and secret != WEBHOOK_SECRET:
            raise HTTPException(401, "Unauthorized")

    class SimRequest(BaseModel):
        scenario: str
        pool: str = "deepseek"
        refs: list[str] = []
        timeframes: list[str] | None = None

    @api.get("/health")
    async def health():
        return {"status": "ok", "app": "geopol"}

    @api.post("/run")
    async def trigger_run(req: SimRequest, request: Request):
        """Trigger a simulation. Returns a call_id for polling."""
        _check_auth(request)

        call = run_simulation.spawn(
            scenario_name=req.scenario,
            pool_name=req.pool,
            reference_urls=req.refs or None,
            timeframes=req.timeframes,
        )

        return {
            "status": "spawned",
            "call_id": call.object_id,
            "scenario": req.scenario,
            "pool": req.pool,
        }

    @api.post("/run/sync")
    async def trigger_run_sync(req: SimRequest, request: Request):
        """Trigger a simulation and wait for results (blocks until complete)."""
        _check_auth(request)

        result = await run_simulation.remote.aio(
            scenario_name=req.scenario,
            pool_name=req.pool,
            reference_urls=req.refs or None,
            timeframes=req.timeframes,
        )

        return result

    @api.get("/run/{call_id}")
    async def poll_run(call_id: str, request: Request):
        """Poll a spawned simulation for completion."""
        _check_auth(request)

        from modal.functions import FunctionCall
        try:
            fc = FunctionCall.from_id(call_id)
            try:
                result = fc.get(timeout=1)
                return {"status": "complete", "result": result}
            except TimeoutError:
                return {"status": "running"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @api.get("/scenarios")
    async def list_scenarios(request: Request):
        """List available scenarios."""
        _check_auth(request)

        from ruamel.yaml import YAML
        yaml = YAML(typ="safe")
        config_dir = Path("/root/config/scenarios")
        results = []
        for f in sorted(config_dir.iterdir()):
            if f.suffix in (".yaml", ".yml"):
                try:
                    data = yaml.load(f.read_text())
                    results.append({
                        "id": f.stem,
                        "title": data.get("title", f.stem),
                        "actor_cluster": data.get("actor_cluster", "inline"),
                    })
                except Exception:
                    results.append({"id": f.stem, "title": f.stem})
        return results

    @api.get("/pools")
    async def list_pools(request: Request):
        """List available model pools."""
        _check_auth(request)

        import sys
        sys.path.insert(0, "/root/src")
        from geopol_forecaster.core.llm import load_pools as lp
        pools, active, _ = lp("/root/config/pools.yaml")
        return [
            {"name": n, "active": n == active, "player": p.player}
            for n, p in pools.items()
        ]

    @api.get("/reports/{filename}")
    async def get_report(filename: str, request: Request):
        """Download a generated PDF report."""
        _check_auth(request)

        filename = Path(filename).name  # sanitize
        pdf_path = Path("/data/reports") / filename
        if not pdf_path.exists():
            reports_volume.reload()
            if not pdf_path.exists():
                raise HTTPException(404, "Report not found")
        return FileResponse(str(pdf_path), media_type="application/pdf")

    return api
