"""Pipeline version tracking — captures git state and config hashes at each run."""

from __future__ import annotations

import hashlib
import os
import subprocess

from .models import PipelineVersion
from .store import PredictionStore


def _file_hash(path: str) -> str | None:
    """SHA256 hash of a file's contents, or None if missing."""
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def _git_info() -> tuple[str | None, bool]:
    """Return (short_hash, is_dirty) from git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        git_hash = result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        git_hash = None

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        dirty = bool(result.stdout.strip()) if result.returncode == 0 else False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        dirty = False

    return git_hash, dirty


def capture_pipeline_version(
    store: PredictionStore,
    run_id: str,
    pools_path: str | None = None,
    scenario_path: str | None = None,
    config_snapshot: dict | None = None,
) -> str:
    """Record the pipeline version at the time of a run."""
    git_hash, git_dirty = _git_info()

    pv = PipelineVersion(
        run_id=run_id,
        git_hash=git_hash,
        git_dirty=git_dirty,
        pools_yaml_hash=_file_hash(pools_path) if pools_path else None,
        scenario_yaml_hash=_file_hash(scenario_path) if scenario_path else None,
        config_snapshot=config_snapshot,
    )
    return store.save_pipeline_version(pv)


def get_changelog(store: PredictionStore, limit: int = 20) -> str:
    """Format pipeline version history as a readable changelog."""
    versions = store.get_pipeline_versions(limit=limit)
    if not versions:
        return "  No pipeline versions recorded yet."

    lines = []
    lines.append("=" * 60)
    lines.append("  PIPELINE CHANGELOG")
    lines.append("=" * 60)
    lines.append("")

    prev_hash = None
    for v in versions:
        run = store.get_run(v["run_id"]) if v.get("run_id") else None
        title = run["scenario_title"] if run else "Unknown"

        dirty_marker = " (dirty)" if v.get("git_dirty") else ""
        git_str = f"{v.get('git_hash', '?')}{dirty_marker}"

        lines.append(f"  {v['recorded_at'][:19]}")
        lines.append(f"    Run:       {title}")
        lines.append(f"    Git:       {git_str}")

        if v.get("pools_yaml_hash"):
            lines.append(f"    Pools:     {v['pools_yaml_hash']}")
        if v.get("scenario_yaml_hash"):
            lines.append(f"    Scenario:  {v['scenario_yaml_hash']}")

        # Show if git hash changed from previous entry
        current_hash = v.get("git_hash")
        if prev_hash and current_hash and current_hash != prev_hash:
            lines.append(f"    ** Code changed: {prev_hash} → {current_hash}")
        prev_hash = current_hash

        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
