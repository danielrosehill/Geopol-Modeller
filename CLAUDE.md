# Geopol Forecaster — Claude Code Project Instructions

## What This Is

A fork of the Geopol Forecaster LLM wargaming framework. Uses LLMs to run open-ended text-based wargames (seminar games, political wargames). Players are AI agents with personas that interact through a LangGraph simulation loop.

## Key Architecture

```
SITREP Agent (Tavily + refs) → Structured SITREP
LangGraph Loop: setup → player_respond (×N) → adjudicate → repeat
Report Agent (LLM) → Typst PDF
All LLM calls go through OpenRouter (OpenAI SDK compatible)
```

## Important Paths

| Path | Purpose |
|------|---------|
| `src/geopol_forecaster/core/` | Core simulation engine (LangGraph, players, LLM calls) |
| `src/geopol_forecaster/planning/` | Pre-simulation agents (SITREP + legacy planning) |
| `src/geopol_forecaster/planning/sitrep.py` | SITREP generation agent (military-format situational report) |
| `src/geopol_forecaster/output/report_agent.py` | LLM-driven Typst report generation with fallback |
| `src/geopol_forecaster/output/report.py` | Template-based Typst report (fallback) |
| `src/geopol_forecaster/scenario_runner.py` | Generic scenario runner (loads YAML scenarios + actor clusters) |
| `src/geopol_forecaster/examples_runner.py` | Legacy hardcoded Azuristan/Crimsonia runner |
| `src/geopol_forecaster/cli.py` | CLI entry point with `--scenario` and `--pool` flags |
| `src/geopol_forecaster/web/` | FastAPI web dashboard (local + Modal) |
| `modal_app.py` | Modal deployment (serverless cloud) |
| `config/scenarios/` | Scenario YAML files |
| `config/actors/` | Reusable actor cluster YAML files |
| `config/pools.yaml` | Model pool definitions |

## Running

```bash
# CLI
pip install -e .
export OPENROUTER_API_KEY=...
export TAVILY_API_KEY=...    # optional but recommended
geopol --list-scenarios
geopol --scenario hormuz-blockade-apr2026 --pool deepseek --report

# Web (local)
geopol-web

# Web (Modal)
modal serve modal_app.py     # dev
modal deploy modal_app.py    # production
```

## Scenario System

Scenarios are YAML files in `config/scenarios/`. Each defines:
- `title`, `scenario` (situation text), `timestep`, `moves`, `mode`
- `actor_cluster` — references a file in `config/actors/` (reusable actor sets)
- `actors` — inline actor definitions (alternative to cluster)
- `questions` and `mc_questions` — post-simulation assessment queries

Actor clusters are YAML files in `config/actors/` with rich persona definitions
including red lines, response patterns, and constraints.

## Dev Notes

- All LLM calls route through OpenRouter using the OpenAI SDK
- Model pools in `config/pools.yaml` map roles (planner, narrator, player, advisor) to model IDs
- The SITREP agent produces a military-format situational report before simulation
- The report agent uses an LLM to generate Typst markup; falls back to template on compile failure
- LangGraph manages the simulation state machine
- Modal deployment uses `geopol-secrets` for API keys
