#!/usr/bin/env python3
"""Snowglobe MCP Server — exposes the wargaming simulator as MCP tools.

Wraps the Modal webhook backend so any MCP client (Claude Code, Claude Desktop,
etc.) can trigger and manage simulations via formal tool definitions.

Run:
  fastmcp run mcp_server.py                    # stdio (for Claude Code)
  fastmcp run mcp_server.py --transport sse     # SSE (for remote clients)

Requires:
  SNOWGLOBE_WEBHOOK_URL and SNOWGLOBE_WEBHOOK_SECRET env vars,
  or fetches from 1Password via `op` CLI.
"""

import os
import json
import time
from pathlib import Path

import httpx
from fastmcp import FastMCP

# Load .env from repo root if present
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

mcp = FastMCP(
    name="snowglobe",
    instructions=(
        "Snowglobe is a multi-actor LLM wargaming simulator. Use these tools to "
        "run geopolitical simulations, list available scenarios and model pools, "
        "check on running simulations, and download PDF reports."
    ),
)

# --- Config ---

def _get_config():
    """Resolve webhook URL and secret from env (loaded from .env)."""
    url = os.environ.get(
        "SNOWGLOBE_WEBHOOK_URL",
        "https://carrotcakeai--snowglobe-webhook.modal.run",
    )
    secret = os.environ.get("SNOWGLOBE_WEBHOOK_SECRET", "")
    return url, secret


def _headers():
    _, secret = _get_config()
    h = {"Content-Type": "application/json"}
    if secret:
        h["X-Webhook-Secret"] = secret
    return h


def _base_url():
    url, _ = _get_config()
    return url


# --- Tools ---

@mcp.tool()
async def list_scenarios() -> str:
    """List all available simulation scenarios.

    Returns a list of scenario IDs, titles, and actor clusters
    that can be used with run_simulation.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/scenarios", headers=_headers())
        resp.raise_for_status()
        scenarios = resp.json()

    lines = ["Available scenarios:", ""]
    for s in scenarios:
        lines.append(f"  {s['id']:<35} {s.get('title', '')}")
        lines.append(f"  {'':35} actors: {s.get('actor_cluster', 'inline')}")
    return "\n".join(lines)


@mcp.tool()
async def list_pools() -> str:
    """List all available model pools for simulations.

    Each pool defines which LLM models play the planner, narrator,
    player, and advisor roles. Returns pool names and player models.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/pools", headers=_headers())
        resp.raise_for_status()
        pools = resp.json()

    lines = ["Available pools:", ""]
    for p in pools:
        marker = " (active)" if p.get("active") else ""
        lines.append(f"  {p['name']:<20} player: {p.get('player', '?')}{marker}")
    return "\n".join(lines)


@mcp.tool()
async def run_simulation(
    scenario: str,
    pool: str = "deepseek",
    reference_urls: list[str] | None = None,
) -> str:
    """Run a geopolitical wargaming simulation.

    Triggers an async simulation on the cloud backend. Returns a call_id
    that can be polled with check_simulation.

    Args:
        scenario: Scenario ID (e.g. 'iran-israel-war'). Use list_scenarios to see options.
        pool: Model pool name (e.g. 'deepseek', 'anthropic'). Use list_pools to see options.
        reference_urls: Optional list of URLs to fetch and include as intelligence context.
    """
    body = {
        "scenario": scenario,
        "pool": pool,
        "refs": reference_urls or [],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_base_url()}/run",
            headers=_headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

    call_id = data.get("call_id", "unknown")
    return (
        f"Simulation spawned successfully.\n"
        f"  Scenario: {scenario}\n"
        f"  Pool: {pool}\n"
        f"  Call ID: {call_id}\n\n"
        f"Use check_simulation(call_id='{call_id}') to poll for results."
    )


@mcp.tool()
async def run_simulation_sync(
    scenario: str,
    pool: str = "deepseek",
    reference_urls: list[str] | None = None,
) -> str:
    """Run a simulation and wait for results (blocking).

    This will block until the simulation completes, which can take
    several minutes depending on the number of actors and moves.

    Args:
        scenario: Scenario ID (e.g. 'iran-israel-war').
        pool: Model pool name (e.g. 'deepseek', 'anthropic').
        reference_urls: Optional list of URLs for intelligence context.
    """
    body = {
        "scenario": scenario,
        "pool": pool,
        "refs": reference_urls or [],
    }

    async with httpx.AsyncClient(timeout=1800) as client:
        resp = await client.post(
            f"{_base_url()}/run/sync",
            headers=_headers(),
            json=body,
        )
        resp.raise_for_status()
        result = resp.json()

    return _format_result(result)


@mcp.tool()
async def check_simulation(call_id: str) -> str:
    """Check the status of a running simulation.

    Args:
        call_id: The call_id returned by run_simulation.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_base_url()}/run/{call_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    status = data.get("status", "unknown")

    if status == "running":
        return f"Simulation is still running (call_id: {call_id}). Check again in 30 seconds."

    if status == "complete":
        result = data.get("result", data)
        return _format_result(result)

    if status == "error":
        return f"Simulation failed: {data.get('error', 'unknown error')}"

    return f"Status: {status}\n{json.dumps(data, indent=2)}"


@mcp.tool()
async def get_report_url(filename: str) -> str:
    """Get the download URL for a simulation PDF report.

    Args:
        filename: The PDF filename returned in simulation results.
    """
    _, secret = _get_config()
    url = f"{_base_url()}/reports/{filename}?secret={secret}"
    return f"PDF report download URL:\n{url}"


# --- Helpers ---

def _format_result(result: dict) -> str:
    """Format simulation result for display."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = []
    title = result.get("title", "Simulation")
    lines.append(f"# {title} — Results")
    lines.append("")

    # Assessments
    assessments = result.get("assessments", [])
    if assessments:
        lines.append("## Assessments")
        lines.append("")
        for a in assessments:
            lines.append(f"**Q:** {a.get('question', '')}")
            lines.append(f"**A:** {a.get('answer', '')}")
            lines.append("")

    # Narrative highlights
    history = result.get("history", [])
    if history:
        lines.append("## Actor Responses")
        lines.append("")
        for entry in history[:20]:  # cap to avoid huge output
            name = entry.get("name", "")
            text = entry.get("text", "")
            if len(text) > 500:
                text = text[:500] + "..."
            lines.append(f"### {name}")
            lines.append(text)
            lines.append("")

    # PDF
    pdf = result.get("pdf_filename")
    if pdf:
        lines.append(f"**PDF Report:** Use get_report_url(filename='{pdf}') to download.")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
