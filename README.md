# Geopol Modeller

**Open-ended geopolitical wargames with large language models**

Geopol Modeller is a fork of [Snow Globe](https://github.com/IQTLabs/snowglobe) by [IQTLabs](https://github.com/IQTLabs) (In-Q-Tel). The original project demonstrated that every stage of a text-based wargame — from scenario preparation through post-game analysis — can be carried out by LLMs, humans, or a combination of both. Read the original paper [here](https://arxiv.org/abs/2404.11446).

## What This Fork Changes

The original Snow Globe used LangChain, local model support (llama-cpp, transformers/torch), and a bespoke imperative game loop. This fork strips that stack and replaces it with:

- **OpenRouter as the single LLM gateway** — access any model from any provider (DeepSeek, Anthropic, OpenAI, Google, Qwen, xAI, MiniMax, Meta, Zhipu, Moonshot) through a unified OpenAI-compatible SDK
- **Model pools** — predefined configurations mapping roles (planner, player) to specific models, selectable at runtime via an interactive CLI menu or by name
- **Tavily-powered planning agent** — an optional pre-simulation stage that searches current events and ingests reference URLs to produce a shared briefing for all agents
- **LangGraph simulation loop** — an inspectable, pausable state graph replacing the imperative loop
- **Rich progress reporting** — live terminal UI with progress bars and status updates
- **Checkpointing** — simulation state is saved at each turn, allowing recovery from interruptions
- **Typst PDF reports** — automatic generation of formatted PDF reports from simulation output
- **Edge-TTS podcast generation** — text-to-speech audio summaries of simulation results
- **Stripped dependencies** — removed LangChain, torch, transformers, llama-cpp in favor of direct OpenAI SDK calls through OpenRouter

## Quick Start

```bash
# Install
pip install -e .

# Set API keys
export OPENROUTER_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here  # optional, for current-events research

# Run with interactive model pool menu
snowglobe
```

The CLI presents a menu to choose your model pool:

```
  ========================================
    SNOWGLOBE — Model Pool Selection
  ========================================

   #  Pool              Planner                        Player
   ------------------------------------------------------------------------------
   1. deepseek          deepseek/deepseek-v3.2         deepseek/deepseek-v3.2        *
   2. minimax-mixed     minimax/minimax-m2.7           minimax/minimax-m2-her
   3. anthropic         anthropic/claude-sonnet-4.6    anthropic/claude-haiku-4.5
   4. google            google/gemini-3-flash-preview  google/gemini-3.1-flash-lite
   ...

  Select pool [1-14, or Enter for 'deepseek']:
```

Or run directly with a pool name:

```bash
python examples/ac_sim.py anthropic
python examples/ac_sim.py minimax-mixed
```

## Model Pools

Pools define which models handle each role. Edit `config/pools.yaml` or pass a pool name at runtime.

| Pool | Planner/Narrator | Player/Advisor |
|------|-----------------|----------------|
| `deepseek` | deepseek-v3.2 | deepseek-v3.2 |
| `minimax-mixed` | minimax-m2.7 | minimax-m2-her (roleplay) |
| `anthropic` | claude-sonnet-4.6 | claude-haiku-4.5 |
| `google` | gemini-3-flash | gemini-3.1-flash-lite |
| `qwen` | qwen3.6-plus | qwen3.5-flash |
| `openai` | gpt-5-mini | gpt-5-nano |
| `xai` | grok-4 | grok-4.1-fast |
| `llama` | llama-4-maverick | llama-4-maverick |
| `moonshot` | kimi-k2.5 | kimi-k2.5 |
| `zhipu` | glm-5 | glm-4.7-flash |

See [docs/model-selection.md](docs/model-selection.md) for benchmark links and guidance on choosing models.

## Architecture

```
1. PLANNING AGENT (runs once)
   - Searches current events via Tavily
   - Loads reference documents
   - Produces a BRIEFING shared by all agents

2. LANGGRAPH SIMULATION LOOP
   setup → player_respond (×N) → adjudicate → repeat
   Each agent receives: persona + briefing + game history
```

## Custom Scenarios

Edit `config/game.yaml` to define your scenario (title, scenario text, goals, players, advisors). See the existing file for the full schema.

## Upstream

- **Original project:** [IQTLabs/snowglobe](https://github.com/IQTLabs/snowglobe)
- **Paper:** [arxiv.org/abs/2404.11446](https://arxiv.org/abs/2404.11446)
- **Original authors:** Daniel Hogan et al. (IQTLabs / In-Q-Tel)

## License

Released under the [Apache License Version 2.0](LICENSE).
