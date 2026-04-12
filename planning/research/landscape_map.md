# Snow Globe: Competitive Landscape Map

> LLM-based wargaming, policy simulation, and adjacent multi-agent simulation tools.
>
> Last updated: 2026-04-12

---

## 1. Direct Competitors and Alternatives

These are frameworks specifically built for LLM-driven wargaming or political/geopolitical simulation.

| Project | Origin | Year | Open Source | Focus | Architecture |
|---------|--------|------|-------------|-------|-------------|
| **Snow Globe** | IQT Labs | 2024 | Yes (Apache 2.0) | Open-ended qualitative wargames, political/seminar games | LLM agents with personas, control/player/team roles, LangGraph loop |
| **WarAgent** | AGI Research (Rutgers) | 2023 | Yes | Historical conflict simulation (WWI, WWII, Warring States) | Country-as-agent, action selection from predefined set, GPT-4/Claude |
| **LLMWargaming** | Stanford HAI / ancorso | 2024 | Yes | Crisis escalation research (US-China scenarios) | Wargame with 107 human experts as baseline, LLM vs human comparison |
| **WargamesAI** | user1342 | 2024 | Yes | General-purpose professional wargaming toolkit | LLM umpiring, dice/card mechanics, PDF persona extraction |
| **TIDE2024 LLMwargame** | NATO TIDE Hackathon | 2024 | Yes | Military wargame simulations | Hackathon prototype, team CARD |
| **SIM-1 (Fable Studio)** | Fable Studio | 2024 | No | Narrative conflict simulation (corporate/political) | Multi-agent competition, GPT-4o reasoning, turn-based |
| **GenWar** | Johns Hopkins APL | 2025 | No (classified versions in development) | Defense tabletop exercises, scenario generation | LLM-powered scenario generation, human-AI hybrid play |

### Key Academic Papers

| Paper | Authors | Venue | Key Finding |
|-------|---------|-------|-------------|
| [Open-Ended Wargames with Large Language Models](https://arxiv.org/abs/2404.11446) | Hogan & Brennen (IQT Labs) | arXiv 2024 | Snow Globe's foundational paper; demonstrates AI-human hybrid wargaming |
| [Escalation Risks from Language Models in Military and Diplomatic Decision-Making](https://arxiv.org/abs/2401.03408) | Rivera et al. (Stanford/Georgia Tech) | FAccT 2024 | All five tested LLMs show escalation tendencies; GPT-3.5 and Llama-2 most escalation-prone |
| [War and Peace (WarAgent)](https://arxiv.org/html/2403.13433v1) | Hua et al. (Rutgers) | OpenReview 2024 | LLM agents replicate macro outcomes of historical wars (alliances, war declarations) |
| [Human vs. Machine: Language Models and Wargames](https://arxiv.org/html/2403.03407v1) | Multiple authors | arXiv 2024 | Compares LLM and human decision-making in structured wargame scenarios |
| [AI Arms and Influence](https://arxiv.org/pdf/2602.14740) | Multiple authors | arXiv 2026 | Frontier models exhibit sophisticated reasoning in military/diplomatic contexts |

---

## 2. Adjacent Multi-Agent Simulation Tools

### 2a. General Multi-Agent Frameworks

These are not wargaming-specific but provide the underlying orchestration patterns that wargaming tools build on.

| Framework | Maintainer | Architecture | Relevance to Wargaming |
|-----------|-----------|-------------|----------------------|
| **LangGraph** | LangChain | State graph with cycles, checkpointing, human-in-the-loop | Snow Globe's simulation loop engine; inspectable/pausable state |
| **AutoGen (AG2)** | Microsoft Research | Conversational GroupChat, multi-turn agent debate | Natural for negotiation/deliberation simulations; expensive at scale (20+ LLM calls per round) |
| **CrewAI** | CrewAI Inc. | Role-based crews, sequential/hierarchical processes | Good for structured workflows; 30-60% faster than AutoGen, 34% fewer tokens |
| **OpenAI Agents SDK** | OpenAI | Tool-calling agents with handoffs | Simpler but less flexible for multi-party simulation |
| **Google ADK** | Google | Agent Development Kit | Emerging framework, tightly coupled with Gemini |
| **Anthropic Agent SDK** | Anthropic | Agent SDK alongside Claude 4.6 | Emerging, production-focused |

### 2b. Agent-vs-Agent and Social Simulation Frameworks

| Framework | Maintainer | Focus | Architecture |
|-----------|-----------|-------|-------------|
| **Generative Agents ("Smallville")** | Stanford (Park et al.) | Social simulation of 25 agents in a virtual town | Memory stream + retrieval + reflection + planning; emergent social behaviors (party planning, relationship formation) |
| **Concordia** | Google DeepMind | Generative agent-based modeling in physical/social/digital spaces | Game Master + player entities pattern inspired by tabletop RPGs; v2.0 released post-NeurIPS 2024 |
| **ChatArena** | Farama Foundation | Multi-agent language game environments | MDP-based, includes classroom sims, board games, multi-player conversations |
| **LLM-Deliberation** | NeurIPS 2024 | Stakeholder negotiation with cooperation/competition/maliciousness | Benchmarks LLM behavior in structured negotiation scenarios |
| **DiploBench** | sam-paech | Benchmark for LLMs playing full-press Diplomacy | Board game as proxy for geopolitical negotiation |
| **Outsmart** | ed-donner | LLM arena for diplomacy and deception | Model-vs-model competitive format |

### 2c. Benchmarks and Evaluation

| Benchmark | Focus | Notes |
|-----------|-------|-------|
| **AgentBench** (THUDM) | LLM-as-agent across 8 environments | ICLR 2024; 29 models tested; large gap between commercial and open-source |
| **MultiAgentBench** | Collaboration and competition among LLM agents | Milestone-based KPIs for multi-agent task completion |
| **CFPD Benchmark** (Scale AI + CSIS) | Foreign policy decision-making by LLMs | Evaluates LLM responses to complex geopolitical prompts |

---

## 3. Government and Defense Adoption

### United States

| Organization | Initiative | Status | Details |
|-------------|-----------|--------|---------|
| **CIA / Intelligence Community** | Snow Globe adoption | Published Dec 2025 in *Studies in Intelligence* (Vol. 69, No. 4) | CIA-IQT joint wargame conducted April 2025; lessons from human-AI teaming in war games |
| **Johns Hopkins APL** | GenWar Lab | Lab opening 2026 | Generative AI wargaming lab; classified versions being built for DoD and IC; plain-English scenario specification |
| **U.S. Army CGSC** | AI-Enabled Wargaming | Mandated default method starting AY 2026-2027 | Custom Vantage agent with 128K context window; joint task force exercises |
| **U.S. Air Force** | WarEngine concept + Decision Advantage Sprints | RFI stage (2025) | Human-machine teaming in wargames; accessible simulation platform |
| **CSIS Futures Lab** | Democratize Wargaming initiative | Active research | Advocates generative AI to reduce cost and increase access to analytical wargaming |
| **Scale AI + CSIS** | CFPD Benchmark | Published | Evaluates LLM national security decision-making tendencies |

### NATO

| Initiative | Status | Details |
|-----------|--------|---------|
| **SAGA (Scenario-Aided Game Analysis)** | Active | LLM-based scenario generation augmenting NATO's WISDOM platform |
| **TIDE Hackathon 2024** | Completed | Produced LLMwargame prototype (team CARD) |
| **NATO Responsible AI Principles** | Policy framework | All AI wargaming applications developed under human oversight, transparency, and reliability requirements |

### Other Nations

| Country | Activity |
|---------|----------|
| **Finland** | Applying AI to military simulators and wargaming (published in ScienceDirect, 2025) |
| **U.S. State Department** | Leveraging AI in strategic games (documented on PAXsims, April 2025) |

### Key Cautionary Findings

- All five LLMs tested by Stanford/Georgia Tech showed escalation tendencies in military simulations, with some choosing nuclear strikes.
- RAND cautions against using AI to "impersonate" adversary decision-makers, warning of a "dangerous mirage of knowledge."
- Axios reported (Feb 2026) that AI models disproportionately choose violence and escalate to nuclear strikes in simulated war scenarios.

---

## 4. Snow Globe's Key Differentiators

| Feature | Snow Globe | WarAgent | WargamesAI | GenWar | Concordia |
|---------|-----------|----------|------------|--------|-----------|
| **Open-ended play** (no predefined action menus) | Yes | No (predefined actions) | Partial | Unknown | Yes |
| **Persona-based agents** | Yes (detailed persona documents) | Country-level only | Yes (PDF extraction) | Yes | Yes |
| **Human-AI hybrid play** | Yes (any role can be human or AI) | No (fully automated) | Yes | Yes | Limited |
| **Current events integration** | Yes (Tavily planning agent) | No | No | Unknown | No |
| **Multi-provider model access** | Yes (14+ providers via OpenRouter) | GPT-4/Claude only | Varies | Likely restricted | Google models |
| **Inspectable state graph** | Yes (LangGraph) | No | No | Unknown | No |
| **Scenario-agnostic** | Yes (YAML config) | Historical conflicts only | Yes | Defense-focused | Yes |
| **Published academic paper** | Yes (arXiv 2024) | Yes | No | Yes (JHU APL) | Yes |
| **Intelligence community adoption** | Yes (CIA, *Studies in Intelligence* Dec 2025) | No | No | Yes (DoD/IC classified) | No |

### What makes Snow Globe unique

1. **Truly open-ended**: Player actions are not restricted to predefined options. Most competitors (WarAgent, escalation studies) use structured action spaces. Snow Globe agents generate free-form natural language responses, closer to real seminar wargaming.

2. **Persona depth**: Each agent receives a detailed written persona that shapes its responses, going beyond simple role labels (e.g., "China") to nuanced characterizations of individual decision-makers.

3. **Current events grounding**: The Tavily-powered planning agent researches real-world events before simulation begins, producing a shared briefing. No other open-source wargaming framework does this.

4. **Model-agnostic via OpenRouter**: Access to 14+ model providers through a single API. Competitors are typically locked to one or two providers. This enables cross-model comparison and cost optimization.

5. **Hybrid human-AI participation**: Any role (control, player, advisor) can be filled by a human or AI agent. This mirrors real seminar wargame practice where some participants are subject matter experts.

6. **IC validation**: The only open-source LLM wargaming framework with documented adoption by a major intelligence agency (CIA, published in *Studies in Intelligence*).

---

## 5. Gaps in the Landscape That Snow Globe Could Fill

### Underserved areas where Snow Globe has or could have an advantage

| Gap | Current State | Opportunity for Snow Globe |
|-----|--------------|---------------------------|
| **Escalation tracking and measurement** | Stanford/Georgia Tech showed LLMs escalate unpredictably, but no open framework includes built-in escalation metrics | Add quantitative escalation scoring to each round; enable systematic escalation analysis across models and scenarios |
| **Scenario libraries** | Most tools ship with one or two scenarios; no shared repository of reusable wargame scenarios exists | Build a community scenario library (YAML configs) covering different crisis types, regions, and complexity levels |
| **Cross-model behavioral comparison** | Research papers compare models but tools do not make this easy | OpenRouter integration already enables this; add structured comparison outputs (e.g., how does DeepSeek vs Claude handle the same Taiwan scenario?) |
| **Reproducibility and replay** | Most frameworks run once and produce a transcript; hard to replay with variations | LangGraph checkpointing already supports this; expose branching/replay in the CLI |
| **Non-defense applications** | Almost all tools focus on military/geopolitical scenarios | Snow Globe's architecture is scenario-agnostic; expand examples to corporate crisis, pandemic response, climate negotiation, election simulation |
| **Accessibility for non-technical users** | GenWar promises plain-English scenario specification but is classified; open tools require Python knowledge | Build a web UI or simplified CLI wizard for scenario creation and game execution |
| **Post-game analysis** | Most tools produce raw transcripts; limited structured analysis | Snow Globe already has report generation; enhance with automated pattern extraction, decision tree visualization, and comparative analysis |
| **Evaluation against human baselines** | Only LLMWargaming (Stanford) has done this systematically | Partner with policy schools or think tanks to collect human baseline data for Snow Globe scenarios |
| **Multi-language support** | All tools operate in English only | OpenRouter's model diversity includes models strong in Chinese, Arabic, Russian -- enable wargames where agents communicate in their "native" language |
| **Real-time data feeds** | Tavily provides pre-game research but not live updates during play | Integrate live news/data feeds that can inject real-world developments mid-simulation |

### Strategic positioning

Snow Globe sits at a unique intersection: it is the only open-source framework that combines truly open-ended play, persona-based agents, current events grounding, and documented intelligence community adoption. The closest competitors are either:

- **Too narrow**: WarAgent only does historical conflicts with predefined actions
- **Too classified**: GenWar is building classified versions for DoD/IC
- **Too general**: Concordia and ChatArena are general social simulation tools not optimized for wargaming
- **Too experimental**: SIM-1 and LLM-Diplomacy are one-off research projects, not maintained frameworks
- **Too simplistic**: WargamesAI includes dice/card mechanics but lacks the sophisticated planning and adjudication pipeline

The primary competitive risk is GenWar (JHU APL), which has significant DoD funding and is building classified capabilities. However, GenWar's classified nature means it cannot serve the broader policy, academic, and think-tank community that CSIS argues needs access to wargaming tools. Snow Globe is well-positioned to be the open-source standard for LLM wargaming outside classified environments.

---

## Sources

### Snow Globe and IQT Labs
- [Open-Ended Wargames with Large Language Models (arXiv)](https://arxiv.org/abs/2404.11446)
- [IQT Labs Snow Globe (GitHub)](https://github.com/IQTLabs/snowglobe)
- [Snow Globe Multi-Player AI System (CIA Studies in Intelligence, Dec 2025)](https://www.cia.gov/resources/csi/studies-in-intelligence/studies-in-intelligence-vol-69-no-4-extracts-december-2025/snow-globe-multi-player-ai-system-lessons-from-human-ai-teaming-in-war-games)
- [Snow Globe on PyPI](https://pypi.org/project/llm-snowglobe/)

### Direct Competitors
- [WarAgent (GitHub)](https://github.com/agiresearch/WarAgent)
- [LLMWargaming (GitHub)](https://github.com/ancorso/LLMWargaming)
- [WargamesAI (GitHub)](https://github.com/user1342/WargamesAI)
- [TIDE2024 LLMwargame (GitHub)](https://github.com/MilaSong/TIDE2024_LLMwargame)
- [SIM-1 Wargames (Fable Studio)](https://fablestudio.github.io/openai-wargames/)

### Escalation and Safety Research
- [Escalation Risks from Language Models (Stanford HAI)](https://hai.stanford.edu/policy-brief-escalation-risks-llms-military-and-diplomatic-contexts)
- [Escalation Risks paper (arXiv)](https://arxiv.org/abs/2401.03408)
- [AI really likes using nuclear weapons (Axios, Feb 2026)](https://www.axios.com/2026/02/26/ai-nuclear-weapons-war-pentagon-scenarios)

### Government and Defense
- [GenWar Lab (JHU APL)](https://www.jhuapl.edu/news/news-releases/251030-genwar-lab)
- [JHU APL building classified AI wargaming tools (Breaking Defense)](https://breakingdefense.com/2025/08/johns-hopkins-is-building-classified-versions-of-its-ai-wargaming-tools-for-dod-ic/)
- [AI-Enabled Wargaming at CGSC (Small Wars Journal)](https://smallwarsjournal.com/2026/01/16/ai-enabled-wargaming-cgsc/)
- [Air Force AI for wargaming (DefenseScoop)](https://defensescoop.com/2025/11/24/air-force-ai-for-advanced-wargaming-integrated-force-design-rfi/)
- [NATO LLM-enhanced wargaming](https://www.sto.nato.int/document/leveraging-large-language-models-for-enhanced-wargaming-in-multi-domain-operations-2/)
- [RAND: Should I Use AI in My Wargame?](https://www.rand.org/pubs/commentary/2025/04/should-i-use-ai-in-my-wargame.html)
- [RAND: AI for Wargaming and Modeling](https://www.rand.org/pubs/external_publications/EP68860.html)

### Think Tanks and Policy
- [CSIS: Democratize Wargaming Using Generative AI](https://www.csis.org/analysis/it-time-democratize-wargaming-using-generative-ai)
- [Scale AI + CSIS Foreign Policy Decision Benchmark](https://scale.com/blog/scale-csis-foreign-policy-benchmark)
- [Leveraging AI in State Department strategic games (PAXsims)](https://paxsims.wordpress.com/2025/04/19/leveraging-ai-in-state-department-strategic-games/)

### Adjacent Frameworks
- [Generative Agents / Smallville (Stanford)](https://github.com/joonspk-research/generative_agents)
- [Concordia (Google DeepMind)](https://github.com/google-deepmind/concordia)
- [ChatArena (Farama Foundation)](https://github.com/Farama-Foundation/chatarena)
- [LLM-Deliberation (NeurIPS 2024)](https://github.com/S-Abdelnabi/LLM-Deliberation)
- [DiploBench](https://github.com/sam-paech/diplobench)
- [AgentBench (THUDM)](https://github.com/THUDM/AgentBench)
