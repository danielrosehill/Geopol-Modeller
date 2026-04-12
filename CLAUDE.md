# Snow Globe — Claude Code Project Instructions

## What This Is

A fork of the Snow Globe LLM wargaming framework. Uses LLMs to run open-ended text-based wargames (seminar games, political wargames). Players are AI agents with personas that interact through a LangGraph simulation loop.

## Key Architecture

```
Planning Agent (Tavily) → Briefing
LangGraph Loop: setup → player_respond (×N) → adjudicate → repeat
All calls go through OpenRouter (OpenAI SDK compatible)
```

## Important Paths

| Path | Purpose |
|------|---------|
| `src/llm_snowglobe/core/` | Core simulation engine (LangGraph, players, LLM calls) |
| `src/llm_snowglobe/planning/` | Tavily-powered pre-simulation research agent |
| `src/llm_snowglobe/cli.py` | CLI entry point with model pool menu |
| `config/game.yaml` | Scenario definition (players, goals, situation) |
| `config/pools.yaml` | Model pool definitions (which LLMs play which roles) |
| `planning/` | Project planning docs and research notes |

## Running

```bash
pip install -e .
export OPENROUTER_API_KEY=...
export TAVILY_API_KEY=...    # optional
snowglobe                    # interactive pool menu
```

## Dev Notes

- All LLM calls route through OpenRouter using the OpenAI SDK
- Model pools are defined in `config/pools.yaml` — each pool maps roles (planner, player) to model IDs
- The planning agent is optional; it runs Tavily searches to build a current-events briefing before simulation starts
- LangGraph manages the simulation state machine (setup → player responses → adjudication → loop)
