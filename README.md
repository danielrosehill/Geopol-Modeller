# Snow Globe
***Open-Ended Wargames with Large Language Models***

Snow Globe uses large language models (LLMs) for automated play of "open-ended" text-based wargames, such as seminar games and political wargames. LLMs enable a light, flexible architecture in which player actions are not restricted to predefined options. The system allows humans to play against or alongside AI agents with specific personas.

This fork adds:
- **OpenRouter integration** — access any model from any provider through a single API
- **Model pools** — predefined configurations for 14+ providers (DeepSeek, Anthropic, OpenAI, Google, Qwen, xAI, MiniMax, Meta, Zhipu, Moonshot)
- **Tavily-powered planning agent** — researches current events before simulation begins, producing a shared briefing for all agents
- **LangGraph simulation loop** — inspectable, pausable state graph replacing the imperative loop
- **Stripped dependencies** — removed LangChain, torch, transformers, llama-cpp in favor of direct OpenAI SDK calls

Read the original paper [here](https://arxiv.org/abs/2404.11446).

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

## License

Released under the [Apache License Version 2.0](LICENSE).
