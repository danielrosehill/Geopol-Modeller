# Model Selection Guide

Snowglobe uses [OpenRouter](https://openrouter.ai/) as a unified API gateway, giving access to models from every major provider through a single endpoint.

## Model Pools

Each pool defines 4 roles:

| Role | What it does | Quality needs |
|------|-------------|---------------|
| **Planner** | Runs once — web research + briefing synthesis | High reasoning |
| **Narrator** | Adjudicates rounds, weaves outcomes | Strong creative + analytical |
| **Player** | Responds in-character each round | Good persona adherence |
| **Advisor** | Supports human players with analysis | Basic competence, fast |

See `config/pools.yaml` for all predefined pools. Set `active_pool` or pass the pool name at runtime.

## Browse Models

- [OpenRouter Roleplay Models](https://openrouter.ai/models?fmt=cards&categories=roleplay) — browse models tagged for roleplay
- [OpenRouter Rankings](https://openrouter.ai/rankings) — overall model rankings by category

## Roleplay Benchmarks

Use these to track which models perform best for character simulation and creative interaction:

| Benchmark | What it measures | Link |
|-----------|-----------------|------|
| **EQ-Bench** | Emotional intelligence, empathy, social skills in roleplay scenarios | [eqbench.com](https://eqbench.com/about.html) |
| **LLM Stats Roleplay** | Aggregated roleplay benchmark scores across models | [llm-stats.com/benchmarks/category/roleplay](https://llm-stats.com/benchmarks/category/roleplay) |
| **PingPong Bench** | Dedicated RP benchmark using LLM-as-judge evaluation | [github.com/IlyaGusev/ping_pong_bench](https://github.com/IlyaGusev/ping_pong_bench) |
| **RoleLLM / RoleBench** | Character-level roleplay benchmark (168k samples) | [github.com/InteractiveNLP-Team/RoleLLM-public](https://github.com/InteractiveNLP-Team/RoleLLM-public) |
| **Arena AI** | Crowdsourced side-by-side model comparison | [arena.ai/leaderboard](https://arena.ai/leaderboard) |

## Adding Custom Pools

Edit `config/pools.yaml` to add your own pool. Use any model ID from [OpenRouter's model list](https://openrouter.ai/models):

```yaml
pools:
  my-custom:
    planner:  "provider/model-name"
    narrator: "provider/model-name"
    player:   "provider/model-name"
    advisor:  "provider/model-name"
```

Set `active_pool: my-custom` or pass it as a CLI argument.
