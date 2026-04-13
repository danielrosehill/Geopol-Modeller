# Geopol-Forecaster vs Geopol Forecaster: Integration Analysis

**Date**: 2026-04-12
**Author**: Automated analysis (Claude)

---

## 1. Geopol-Forecaster Overview

**Repository**: https://github.com/danielrosehill/Geopol-Forecaster

Geopol-Forecaster is a two-stage geopolitical forecasting pipeline that takes a natural-language forecast question (e.g., "Will the April 2026 ceasefire hold through +1 month?") and produces a structured analytical report with PDF output.

### Stage A: Actor Simulation

Directly derived from Geopol Forecaster's architecture. A roster of ~40 hard-coded real-world actors (Khamenei, Netanyahu, Biden, etc.) with detailed persona briefs including known red lines, typical response patterns, and institutional constraints. A referee/narrator mediates turns across configurable time horizons (+24h, +72h, +2 weeks). Actors commit privately and independently; the referee narrates world state using authority-precedence conflict resolution. Actors see only the referee-authored state and their own private memory.

### Stage B: LLM Council

Adapted from Karpathy's `llm-council` project. Six "lens" analysts (Neutral, Pessimistic, Optimistic, Blindsides, Probabilistic, Historical) deliberate via a three-stage protocol:

1. **Parallel query** -- each lens answers the forecast question independently, receiving base context + fresh data + Stage A simulation summary.
2. **Blind peer review** -- each lens critiques the other five anonymously, ranking them on specificity, data fidelity, internal consistency, and lens-appropriate sharpness.
3. **Chairman synthesis** -- a chairman LLM writes the final report incorporating all lens answers, peer reviews, and simulation evidence.

### Grounding and Output

- **Grounding**: Tavily web search + RSS/ISW headlines, frozen into a single bundle so every agent reasons from identical data.
- **Pinecone archive**: Past runs are stored and retrieved for longitudinal comparison.
- **Output**: Per-run directory with `chairman_report.md`, three PDFs (intel briefing, full transcript, combined), frozen fresh data, full simulation JSON, and council trace files. Published to a Jekyll site.

### Infrastructure

- Python, async throughout, OpenRouter for all LLM calls (single model: Claude Sonnet 4.5 for all roles currently).
- LangGraph state machine with SQLite checkpointing for crash recovery.
- CLI entry point (`geopol forecast "..."` / `geopol smoketest`).
- Typst-based PDF rendering.

---

## 2. Architectural Comparison

| Dimension | Geopol Forecaster | Geopol-Forecaster |
|-----------|-----------|-------------------|
| **Purpose** | Open-ended wargame simulation (interactive or automated) | Geopolitical forecasting pipeline (automated, one-shot) |
| **Actors** | User-defined via `game.yaml` (fictional or real, any domain) | Hard-coded roster of ~40 real-world geopolitical figures |
| **Actor fidelity** | Lightweight personas (one-line persona + goal references) | Detailed persona briefs with red lines, constraints, response patterns |
| **Human play** | Supported (human players alongside AI) | Not supported (fully automated) |
| **Scenario source** | YAML config file (fictional scenarios like Azuristan/Crimsonia) | Natural-language forecast question about real-world events |
| **Pre-sim research** | Planning agent (Tavily search + URL ingestion + doc loading) | Fresh data bundle (Tavily + RSS/ISW, frozen) |
| **Simulation loop** | LangGraph: setup -> player_respond (x N) -> adjudicate -> repeat | Async loop: actors commit independently -> referee narrates -> repeat |
| **Post-sim analysis** | Assessment questions (free-text + multiple choice) | Six-lens council with peer review and chairman synthesis |
| **Model diversity** | 14+ provider pools (DeepSeek, Anthropic, OpenAI, etc.) | Single model everywhere (Sonnet 4.5 via OpenRouter) |
| **State management** | LangGraph with checkpoint/resume | LangGraph with SQLite checkpointing |
| **Output** | Console/structured history + assessments | PDFs, markdown reports, Jekyll site, Pinecone archive |
| **Upstream** | Fork of IQTLabs/geopol | Original project (cites Geopol Forecaster as inspiration for Stage A) |

### Key Structural Differences

**Geopol Forecaster** is a general-purpose simulation engine. The simulation loop is scenario-agnostic -- it takes any YAML-defined scenario with any players, personas, and goals. The planning agent enriches context but the core loop doesn't care about the domain. The assessment phase asks questions about the simulation outcome but doesn't synthesize a report.

**Geopol-Forecaster** is a domain-specific forecasting product. It hardcodes a geopolitical actor roster, adds a sophisticated analytical layer (the council), and produces publication-quality output. Stage A is essentially a stripped-down Geopol Forecaster simulation reimplemented inline (the codebase explicitly notes the dep on `llm-geopol` is kept in `pyproject.toml` so "a geopol-backed engine can be swapped in later without touching the pipeline boundary").

---

## 3. Overlap Analysis

### What They Share

- **Multi-agent LLM orchestration**: Both use multiple LLM-powered agents with distinct personas operating in a structured turn-based protocol.
- **Geopolitical domain**: Both are designed with geopolitical scenario reasoning as a primary use case.
- **Tavily-powered research phase**: Both use Tavily to ground agents in current events before simulation begins.
- **LangGraph state machines**: Both use LangGraph for their orchestration loops.
- **OpenRouter routing**: Both route LLM calls through OpenRouter.
- **Referee/narrator pattern**: Both have a narrator/referee that synthesizes turn outcomes and mediates between actors.
- **Simulation ancestry**: Geopol-Forecaster's Stage A is explicitly modeled on Geopol Forecaster's `Control`/`Player` pattern and cites it as the inspiration.

### What They Don't Share

- **The council layer**: Geopol Forecaster has no equivalent to Geopol-Forecaster's six-lens analytical council. Geopol Forecaster's assessment phase is much simpler (question-answer pairs).
- **Actor modeling depth**: Geopol-Forecaster's actors have detailed persona briefs with red lines, constraints, and response patterns. Geopol Forecaster's are one-line personas with goal references.
- **Report generation**: Geopol-Forecaster produces structured PDF reports. Geopol Forecaster produces raw simulation history.
- **Human interaction**: Geopol Forecaster supports human players. Geopol-Forecaster is fully automated.
- **Scenario flexibility**: Geopol Forecaster is domain-agnostic. Geopol-Forecaster is hard-coded for a specific geopolitical context.
- **Longitudinal memory**: Geopol-Forecaster stores past runs in Pinecone and retrieves them for future forecasts. Geopol Forecaster has no run archive.

---

## 4. Arguments FOR Integration

1. **Shared infrastructure**: Both projects use OpenRouter, LangGraph, and Tavily. A shared library for LLM calls, news gathering, and state management would reduce duplication.

2. **Complementary capabilities**: Geopol Forecaster provides the general simulation engine; Geopol-Forecaster provides the analytical layer. Combining them creates a complete pipeline: `research -> simulate -> analyze -> report`.

3. **Geopol-Forecaster already depends on Geopol Forecaster conceptually**: The Geopol-Forecaster codebase explicitly notes that its simulation engine is modeled on Geopol Forecaster and that the `llm-geopol` dependency is kept for potential future use. Integration would fulfill this latent design intent.

4. **The council as a Geopol Forecaster plugin**: The six-lens council could be implemented as a post-simulation analysis module within Geopol Forecaster, available for any scenario, not just the hardcoded geopolitical one. This would make Geopol Forecaster more useful as a general wargaming tool.

5. **Forecaster scenarios could use Geopol Forecaster's YAML format**: Instead of hardcoding actors, Geopol-Forecaster could define its ~40-actor roster as a Geopol Forecaster game config, gaining the flexibility to swap rosters or run different geopolitical scenarios.

6. **Model pool diversity**: Geopol Forecaster's 14+ provider pools could improve Geopol-Forecaster's simulation quality (currently locked to a single model).

---

## 5. Arguments FOR Keeping Them Separate

1. **Different user bases and goals**: Geopol Forecaster is a research/academic wargaming tool descended from a published paper. Geopol-Forecaster is a personal forecasting product that produces consumer-facing reports. Merging them muddies both value propositions.

2. **Geopol Forecaster is a fork with upstream**: Geopol Forecaster tracks IQTLabs/geopol. Merging in Geopol-Forecaster's code would create massive divergence from upstream, making it harder to pull future improvements or contribute back.

3. **Geopol-Forecaster's simulation is intentionally simplified**: The Geopol-Forecaster engine deliberately avoids Geopol Forecaster's heavier features (human play, model pools, checkpoint/resume complexity) in favor of a streamlined, automated pipeline. Integration would re-introduce complexity that was deliberately removed.

4. **Domain specificity is a feature, not a bug**: Geopol-Forecaster's hardcoded roster and domain-specific prompts are tuned for its use case. Generalizing them to work through Geopol Forecaster's YAML config would lose prompt engineering specificity.

5. **Different release cadences**: Geopol-Forecaster has a skill (`run-geopol-forecast`) and workflow (`new-geopol-forecast-repo`) that are tuned for daily/ad-hoc forecasting. Geopol Forecaster is used for longer research sessions. Coupling them creates coordination overhead.

6. **The council pattern is not simulation**: The llm-council three-stage protocol (parallel query, peer review, chairman synthesis) is fundamentally different from a simulation loop. Forcing it into Geopol Forecaster's architecture would be an awkward fit -- it's better modeled as a downstream consumer of simulation output.

7. **Cleaner dependency graph**: Geopol-Forecaster can import Geopol Forecaster as a library for Stage A without the two being the same project. This is already the stated intent in the Geopol-Forecaster codebase.

---

## 6. Recommendation

**Keep them separate. Formalize the dependency boundary.**

The projects serve different purposes and have different audiences. The strongest integration argument -- shared infrastructure -- is better served by having Geopol-Forecaster depend on Geopol Forecaster as a library rather than merging the codebases. This is already the design direction noted in Geopol-Forecaster's `simulation/engine.py`:

> "the dep is still listed in `pyproject.toml` so a `geopol`-backed engine can be swapped in later without touching the pipeline boundary"

### Concrete next steps

1. **Formalize Geopol Forecaster as Geopol-Forecaster's Stage A engine**: Replace Geopol-Forecaster's inline simulation loop with actual `llm-geopol` calls. This means mapping the Geopol-Forecaster actor roster into Geopol Forecaster's player config format and using Geopol Forecaster's simulation graph for the turn loop. The pipeline boundary (`run_simulation()` returning a `SimulationResult`) is already clean.

2. **Extract the council pattern as a standalone library**: The three-stage llm-council protocol (parallel query, blind peer review, chairman synthesis) is general enough to be useful outside geopolitical forecasting. Consider extracting it into its own package that takes structured input (a question + context bundle) and produces a synthesized report. Geopol-Forecaster and Geopol Forecaster could both optionally use it.

3. **Do not merge the codebases**: Geopol Forecaster should remain a general wargaming engine. Geopol-Forecaster should remain a domain-specific forecasting product that consumes Geopol Forecaster's simulation output and adds its own analytical layer.

4. **Share utility code via a small common package if needed**: If OpenRouter client code, Tavily wrappers, or LangGraph helpers are substantially duplicated, extract them into a shared utility. But the current duplication is modest and may not warrant the coordination cost.
