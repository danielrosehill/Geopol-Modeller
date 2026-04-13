![Geopol Modeller Banner](assets/banner.png)

# Geopol Modeller

**Multi-actor LLM simulation for geopolitical forecasting, policy modelling, and contingency planning**

Geopol Modeller is a fork of [Geopol Forecaster](https://github.com/IQTLabs/geopol) by [IQTLabs](https://github.com/IQTLabs) (In-Q-Tel). The original project demonstrated that every stage of a text-based wargame -- from scenario preparation through post-game analysis -- can be carried out by LLMs. Read the original paper [here](https://arxiv.org/abs/2404.11446).

This fork rewrites the stack, adds a scenario/actor system designed for real-world crisis forecasting, and introduces prediction tracking with accuracy grading against ground truth.

> **Note:** This is a different simulator from [danielrosehill/Geopol-Forecaster](https://github.com/danielrosehill/Geopol-Forecaster), which combines the original Snow Globe wargaming methodology with an LLM Council model (multiple LLM "advisors" deliberating in structured rounds). This repo (Geopol Modeller) uses the pure multi-actor simulation approach — LLM agents with geopolitical personas interact through a LangGraph state machine, producing emergent outcomes rather than structured council deliberation.

## Stack Comparison

Forked 12 April 2026 from [IQTLabs/geopol](https://github.com/IQTLabs/geopol).

| Component | Original Geopol Forecaster | This Fork (Geopol Modeller) |
|-----------|--------------------|-----------------------------|
| **LLM access** | LangChain + local models (llama-cpp, transformers/torch) | OpenRouter gateway (any provider via OpenAI SDK) |
| **Model selection** | Single model, configured in code | Model pools (YAML config, selectable at runtime) |
| **Simulation loop** | Imperative Python for-loop | LangGraph state graph (inspectable, pausable) |
| **Pre-sim intelligence** | None | Tavily web search + reference URL ingestion → SITREP |
| **Actor system** | Hardcoded in Python | YAML actor clusters with personas, red lines, constraints |
| **Scenario system** | Hardcoded | YAML scenarios with timeframe presets, assessment questions |
| **Scenario subgraphs** | None | Per-scenario graph configs (visibility, shocks, escalation) |
| **Progress reporting** | Print statements | Rich terminal UI with progress bars |
| **Checkpointing** | None | Auto-save after each move, resume from checkpoint |
| **Report output** | None | LLM-generated Typst PDF reports |
| **Audio output** | None | Edge-TTS podcast generation |
| **Prediction tracking** | None | SQLite DB with structured predictions, horizons, probabilities |
| **Accuracy grading** | None | Automated grading against real-world outcomes (Tavily) |
| **Self-healing** | None | Feedback loop: grade predictions → analyse variance → improve |
| **Deployment** | Docker (local) | Local CLI + Modal (serverless cloud) + FastAPI web dashboard |
| **Dependencies** | LangChain, torch, transformers, llama-cpp | OpenAI SDK, LangGraph, Tavily, Typst, Rich |

## Architecture

```
                                    ┌─────────────────────┐
                                    │   Scenario YAML     │
                                    │   + Actor Cluster   │
                                    │   + Graph Config    │
                                    └─────────┬───────────┘
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │   SITREP Agent                │
                              │   Tavily search + ref URLs    │
                              │   → military-format briefing  │
                              └───────────────┬───────────────┘
                                              │
                                              ▼
               ┌──────────────────────────────────────────────────────┐
               │              LangGraph Simulation Loop               │
               │                                                      │
               │   ┌───────┐    ┌──────────┐    ┌─────────────┐      │
               │   │ Setup │───▶│ Players  │───▶│ Adjudicate  │──┐   │
               │   └───────┘    │ respond  │    │ (narrator)  │  │   │
               │                │  (×N)    │    └─────────────┘  │   │
               │                └──────────┘          ▲          │   │
               │                                      │          │   │
               │                     next move ───────┘          │   │
               │                                                 │   │
               │                                    all moves    │   │
               │                                    done         │   │
               │                                                 ▼   │
               │                                          ┌────────┐ │
               │                                          │ Assess │ │
               │                                          └────────┘ │
               └──────────────────────────────────────────────────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                      ┌──────────────┐ ┌────────────┐ ┌────────────┐
                      │  Prediction  │ │ Typst PDF  │ │  Podcast   │
                      │  Extraction  │ │  Report    │ │  (TTS)     │
                      │  + SQLite DB │ └────────────┘ └────────────┘
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   Accuracy   │
                      │   Grading    │
                      │  (vs. real   │
                      │   world)     │
                      └──────────────┘
```

### Actor Decomposition (Iran-Israel Example)

The simulation avoids monolithic state actors. Internal dynamics drive
real-world outcomes:

```
  IRANIAN BLOC                    ISRAELI BLOC              EXTERNAL
  ───────────                     ────────────              ────────
  ┌──────────────┐                ┌──────────────┐
  │  Khamenei    │                │  Netanyahu   │          ┌─────────┐
  │  (Supreme    │                │  (PM)        │          │  Trump  │
  │   Leader)    │                └──────┬───────┘          └────┬────┘
  └──────┬───────┘                       │                       │
         │                        ┌──────┴───────┐          ┌────┴────┐
  ┌──────┴───────┐                │  Coalition   │          │ CENTCOM │
  │  IRGC        │                │  Right       │          └─────────┘
  │  Command     │                │  (Ben-Gvir,  │
  └──────┬───────┘                │   Smotrich)  │          ┌─────────┐
         │                        └──────────────┘          │  China  │
  ┌──────┴───────┐                                          └─────────┘
  │  Basij       │                ┌──────────────┐
  │  (internal   │                │  Opposition  │          ┌─────────┐
  │   security)  │                │  (Gantz,     │          │ Pakistan│
  └──────────────┘                │   Lapid)     │          │(mediator│
                                  └──────────────┘          └─────────┘
  IRANIAN OPPOSITION
  ──────────────────              ┌──────────────┐          ┌─────────┐
  ┌──────────────┐                │  IDF General │          │ Turkey  │
  │  Street      │                │  Staff       │          └─────────┘
  │  Movement    │                └──────────────┘
  └──────────────┘                                          ┌─────────┐
  ┌──────────────┐                ┌──────────────┐          │  Russia │
  │  Silent      │                │  Mossad      │          └─────────┘
  │  Majority    │                └──────────────┘
  └──────────────┘                                          ┌─────────┐
  ┌──────────────┐                                          │  MBS    │
  │  Pahlavi     │               LEBANESE                   │ (Saudi) │
  │  Diaspora    │               ────────                   └─────────┘
  └──────────────┘                ┌──────────────┐
                                  │  LAF         │          ┌─────────┐
  AXIS OF RESISTANCE              └──────────────┘          │  UN SG  │
  ──────────────────              ┌──────────────┐          └─────────┘
  ┌──────────────┐                │  Gov of      │
  │  Hezbollah   │                │  Lebanon     │
  └──────────────┘                └──────────────┘
  ┌──────────────┐
  │  Houthis     │               KURDISH
  └──────────────┘               ──────
  ┌──────────────┐                ┌──────────────┐
  │  Iraqi PMF   │                │  Kurdish     │
  └──────────────┘                │  Factions    │
                                  └──────────────┘
```

### Scenario Subgraph System

Each scenario can define its own simulation behaviour without modifying
the core engine. Graph configs live in `config/graphs/` and inject:

- **Information asymmetry** -- actors only see their own bloc's
  deliberations + public narrative, not adversary internals
- **Exogenous shocks** -- domain-specific unexpected events (e.g.,
  "Hezbollah opens northern front") with weighted probabilities
- **Escalation ladder** -- structured 0-9 scale tracked alongside
  narrative output for quantitative cross-run comparison
- **Adaptive tempo** -- timesteps compress during kinetic escalation,
  expand during diplomatic phases

Scenarios without a graph config use the default generic loop unchanged.

## Quick Start

```bash
# Install
pip install -e .

# Set API keys
export OPENROUTER_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here  # optional, for current-events research

# Run with interactive model pool menu
geopol

# Run a specific scenario with a specific pool
geopol --scenario iran-israel-war --pool deepseek --report

# List available scenarios
geopol --list-scenarios
```

## Model Pools

Pools define which models handle each role. Edit `config/pools.yaml` or pass a pool name at runtime.

| Pool | Planner/Narrator | Player/Advisor |
|------|-----------------|----------------|
| `deepseek` | deepseek-v3.2 | deepseek-v3.2 |
| `anthropic` | claude-sonnet-4.6 | claude-haiku-4.5 |
| `google` | gemini-3-flash | gemini-3.1-flash-lite |
| `openai` | gpt-5-mini | gpt-5-nano |
| `xai` | grok-4 | grok-4.1-fast |
| `llama` | llama-4-maverick | llama-4-maverick |
| `minimax-mixed` | minimax-m2.7 | minimax-m2-her (roleplay) |
| `qwen` | qwen3.6-plus | qwen3.5-flash |
| `moonshot` | kimi-k2.5 | kimi-k2.5 |
| `zhipu` | glm-5 | glm-4.7-flash |

See [docs/model-selection.md](docs/model-selection.md) for benchmark links and guidance on choosing models.

## Scenario System

Scenarios are YAML files in `config/scenarios/`. Each defines actors (inline or via reusable clusters in `config/actors/`), timeframes, assessment questions, and a nature parameter controlling narrator unpredictability.

Actor clusters follow a [formal schema](docs/actor-schema-spec.md) supporting personas, red lines, constraints, capabilities, internal factions, and influence models.

```bash
geopol --list-scenarios            # see available scenarios
geopol --scenario iran-israel-war --pool deepseek --report
```

## Prediction Tracking & Accuracy

Every simulation run automatically extracts structured predictions from the assessment phase and stores them in `.geopol_data/predictions.db`. Each prediction includes:

- **Prediction text** -- a specific, falsifiable claim
- **Probability** -- numeric confidence (0.0-1.0)
- **Horizon** -- time window (24h, 72h, 1w, 1m, 3m, 6m, 1y)
- **Window opens/closes** -- computed dates for when the prediction can be evaluated

### Accuracy Grading

Predictions are graded against real-world outcomes using a 4-point rubric aligned with the [Geopol Forecasts Index](https://github.com/danielrosehill/Geopol-Forecasts-Index):

| Grade | Score | Criteria |
|-------|-------|----------|
| `correct` | 1.0 | Core prediction matched reality in direction and approximate magnitude/timing |
| `largely_correct` | 0.75 | Direction right, magnitude or timing off by modest margin |
| `partially_correct` | 0.5 | General direction right but significantly off on timing/magnitude/mechanism |
| `incorrect` | 0.0 | Prediction contradicted by what actually happened |
| `not_yet_testable` | -- | Window still open or insufficient data to assess |

```bash
geopol assess --all                # grade all predictions with closed windows
geopol assess --run-id abc123      # grade a specific run
geopol predictions list            # list stored predictions
geopol predictions summary         # accuracy summary
geopol changelog                   # pipeline version history
```

### Self-Healing Loop

The self-healing loop is a feedback cycle that uses accuracy data to improve the simulation pipeline:

```
Run simulation -> Extract predictions -> Wait for windows to close
    -> Grade against reality -> Analyse variance -> Suggest changes
    -> Implement approved changes -> Run again
```

## Use Cases

While the current focus is Iran-Israel conflict simulation, the engine is
domain-agnostic. See [planning/use-cases.md](planning/use-cases.md) for
the full roadmap, including:

- **Geopolitical forecasting** -- conflict simulation, crisis escalation modelling
- **Foreign policy simulation** -- sanctions testing, alliance stress-testing, treaty negotiation rehearsal
- **Worst-case planning** -- chokepoint disruption, nuclear escalation ladders, multi-front war pre-mortems
- **International institutional modelling** -- UNSC voting, OPEC+ dynamics, IAEA compliance disputes
- **Domestic policy simulation** -- noise regulation, housing policy, healthcare reform, transit planning
- **Predictive forecasting** -- election outcomes, ceasefire durability, treaty compliance monitoring
- **Democratic resilience** -- constitutional crisis red-teaming, power-sharing design
- **Ideological lens analysis** -- IR theory, economic schools, ethical frameworks applied as analytical agents

## Claude Code Slash Commands

| Command | Purpose |
|---------|---------|
| `/run-sim` | Run a simulation on Modal cloud backend via MCP |
| `/run-scenario <name> [pool]` | Run a simulation locally via CLI |
| `/run-deepseek`, `/run-anthropic`, `/run-openai`, `/run-google`, `/run-xai`, `/run-llama` | Run with a specific model pool |
| `/run-all-pools` | Run the same scenario across all pools sequentially |
| `/post-run-analysis [run-id]` | Score a run's predictions against real-world outcomes |
| `/self-heal` | Analyse prediction variance and suggest pipeline improvements |
| `/backfill <scenario> [pools] [count]` | Seed the predictions DB with multiple runs |
| `/add-pool` | Add a new model pool |
| `/edit-scenario` | Edit the active scenario |
| `/check-models` | Check availability and pricing of models in current pools |
| `/research` | Research a topic and save findings |

## Related Projects

This fork consolidates ideas and patterns from several prior experiments
by the same author:

| Project | What It Contributed |
|---------|-------------------|
| [AI-Agent-UN](https://github.com/danielrosehill/AI-Agent-UN) | 195-country agent roster, structured voting simulation, bilateral impact analysis |
| [Peace-In-The-Middle-East](https://github.com/danielrosehill/Peace-In-The-Middle-East) | 150+ actor decomposition with sub-factions, chamber/working-group structure, facilitator agent pattern, faith and civil society actors |
| [Panel-Of-Claude](https://github.com/danielrosehill/Panel-Of-Claude) | Two-round deliberation (independent analysis then cross-pollination), tension mapping, motion decomposition, moderator synthesis |
| [Claude-AI-Conference](https://github.com/danielrosehill/Claude-AI-Conference) | Agent clustering by theme, identity generation for generic roles, broadcast mode (independent speeches with post-hoc synthesis) |
| [Geopol-Forecasts-Index](https://github.com/danielrosehill/Geopol-Forecasts-Index) | Accuracy grading rubric, prediction tracking schema |
| [AI-Ideation-Runs](https://github.com/danielrosehill/AI-Ideation-Runs) | Use-case brainstorming: 60+ ideas for multi-actor simulation across geopolitics, policy, economics, and humanitarian response |

## Upstream

- **Original project:** [IQTLabs/geopol](https://github.com/IQTLabs/geopol)
- **Paper:** [arxiv.org/abs/2404.11446](https://arxiv.org/abs/2404.11446)
- **Original authors:** Daniel Hogan et al. (IQTLabs / In-Q-Tel)

## License

Released under the [Apache License Version 2.0](LICENSE).
