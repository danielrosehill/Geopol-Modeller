# Policy Applications of LLM-Based Wargaming and Simulation

*Research compiled April 2026*

Snow Globe is an open-ended wargaming framework that uses LLMs as player agents in political and seminar wargames. This document surveys how multi-agent LLM simulation --- and Snow Globe specifically --- could be applied to policy analysis, prediction, and institutional decision-making.

---

## 1. Policy Analysis Applications

### 1.1 Legislative Impact Analysis

Multi-agent LLM simulations can model stakeholder reactions to proposed legislation by instantiating agents representing different interest groups, legislators, lobbyists, affected communities, and regulators.

**Concrete example:** The "Political Actor Agent" system (AAAI 2025) simulates legislative roll-call votes by assigning LLM agents the personas of individual legislators, complete with voting histories and stated positions. It achieves meaningful predictive accuracy on whether bills pass or fail.

**How Snow Globe fits:** A scenario could define agents for key committee chairs, industry lobby groups, grassroots advocacy organizations, and executive branch officials. The planning agent would brief all participants on the bill text and current political dynamics. Multiple simulation runs would reveal which coalitions form, where compromises emerge, and what unintended consequences different stakeholders identify.

### 1.2 Diplomatic Scenario Planning

LLM agents have demonstrated measurable competence in negotiation and diplomacy. Key precedents:

- **Richelieu** (NeurIPS 2024): Self-evolving LLM agents that play the board game Diplomacy, demonstrating complex alliance formation, betrayal detection, and long-term strategic planning.
- **Meta's Cicero** (2022): The first AI to play Diplomacy at human level, combining natural language negotiation with strategic planning. Researchers subsequently used Cicero's value function to detect deceptive proposals.
- **NegotiationArena** (ICML 2024): A benchmark showing LLMs can conduct multi-party negotiations with distinct strategies.

**Application to real diplomacy:** Snow Globe's persona system could model state actors with distinct national interests, domestic political constraints, and historical grievances. The Tavily-powered planning agent would inject current intelligence about ongoing negotiations, economic conditions, and military postures. Running dozens of simulations would map the space of possible treaty outcomes, identifying fragile agreements versus robust ones.

**Limitation:** Current LLMs process only text and are blind to nonverbal communication channels --- body language, tone, and cultural nuance --- that are critical in real diplomatic settings.

### 1.3 Crisis Response Planning

This is one of the most validated use cases. A landmark 2025 study, "What Makes LLM Agent Simulations Useful for Policy?" (arXiv:2509.21868), documents 16 months of iterative collaboration between simulation developers and emergency preparedness officials at a major university.

**Key findings from the study:**
- Over five iterations, simulations scaled from 100 agents to 13,000 agents modeling a commencement ceremony evacuation
- Validation against actual crowd movement footage from a real event built institutional trust
- Deliberately imperfect early simulations surfaced tacit domain knowledge --- when policymakers saw unrealistic outputs, they revealed unstated practices (like accessibility requirements) that proved essential
- The process ultimately produced three concrete policy proposals that were adopted for implementation

**Recommendations for crisis simulation:**
1. Start with routine, observable scenarios before attempting speculative ones
2. Use incomplete prototypes as "exploratory probes" --- ask "what's missing?" not "is this correct?"
3. Invest heavily in environmental context (physical spaces, social relationships, institutional roles)
4. Expect sustained partnership between developers and policymakers over months, not days

### 1.4 Regulatory Impact Assessment

The GWU "FOMC In Silico" system (2025) demonstrates how multi-agent simulation can model regulatory decision-making. It simulates Federal Reserve committee meetings by:
- Assigning each FOMC member an LLM agent with a distinct profile and hawkish/dovish prior beliefs
- Feeding agents real economic data (Beige Book, TealBook)
- Modeling deliberation rounds where agents revise positions after observing others' reasoning
- Producing interest rate predictions comparable to actual FOMC outcomes

**MiniFed** takes a similar approach, having an "economist agent" generate three policy alternatives for discussion, then simulating the full committee vote.

These approaches generalize beyond monetary policy to any regulatory body with known members, stated mandates, and public deliberation records.

### 1.5 Public Opinion Modeling

**ElectionSim** and **FlockVote** (both 2024-2025) demonstrate large-scale public opinion simulation:

- **FlockVote** (ICAIS 2025): Creates LLM agents with high-fidelity demographic profiles (age, income, education, location, media consumption). Deployed on the 2024 U.S. Presidential Election across seven swing states, it successfully replicated the real-world outcome. The key contribution is interpretability --- researchers can probe individual agent rationale to understand *why* simulated voters made their choices.
- **ElectionSim**: Scales to massive populations, simulating social media mobilization effects on voter behavior.

**Known biases:** LLM agents exhibit systematic political biases (GPT models consistently overestimate Democratic vote share), are sensitive to superficial prompt changes, and show non-deterministic behavior. These must be accounted for through ensemble methods and calibration.

---

## 2. Prediction Applications

### 2.1 Election Scenario Modeling

Beyond FlockVote, several systems now model elections:

- LLM agents can simulate voter-level dynamics at significant scale using combinations of real-world and synthetic demographic data
- Multi-step reasoning chains (candidate policies -> personal impact assessment -> vote choice) improve prediction quality
- The primary value is not point prediction but scenario exploration: what happens if a candidate shifts position on a key issue? What if turnout patterns change?

**Methodological note:** Running the same election simulation many times with randomized LLM outputs produces a distribution of outcomes rather than a single prediction, analogous to Monte Carlo methods in quantitative finance.

### 2.2 Geopolitical Conflict Trajectory Forecasting

**WarAgent** (2023-2024) is the most prominent example: an LLM-based multi-agent simulation of historical international conflicts including World War I, World War II, and the Warring States Period.

- Each country is represented by an agent with a country profile
- "Secretary agents" verify the logical consistency of each country's actions
- The system successfully replicated macro outcomes like alliance formation sequences and war declaration timing
- Researchers found the system could identify plausible counterfactual scenarios (what if a different diplomatic move had been made?)

**Fable Studio's SIM-1** (2024-2025) demonstrated a different approach: simulating the five-day OpenAI leadership crisis as a wargame with 20 AI players. Across 20 simulation runs, Sam Altman won in only 4, revealing the fragility of the actual outcome. Fable has announced plans to simulate Taiwan Strait crisis scenarios using the same framework.

### 2.3 Economic Policy Outcome Prediction

The Federal Reserve simulation systems (FOMC In Silico, MiniFed, Hawkish-Dovish Framework) represent direct applications:

- Agents begin with distinct initial beliefs and revise predictions through iterative deliberation rounds
- The Hawkish-Dovish Framework structurally models how FOMC members influence each other during meetings
- IMF working papers (2025) now use LLMs to analyze central bank communications and construct "narrative monetary policy surprises"

### 2.4 Technology Regulation Impact Prediction

No production system exists yet, but the architecture maps directly:
- Agents representing tech companies, regulators, civil society groups, and international counterparts
- Scenario injection of proposed regulations (e.g., AI safety laws, data sovereignty rules, antitrust actions)
- Simulation of industry adaptation strategies, compliance costs, market restructuring, and regulatory arbitrage

### 2.5 Climate Policy Negotiation Simulation

Climate negotiations (COP process) are a natural fit for multi-agent simulation because:
- The actors (nation-states) have well-documented positions, red lines, and domestic constraints
- Historical negotiation records provide calibration data
- The iterated game structure (annual COPs) enables validation against subsequent real outcomes
- Coalition dynamics (AOSIS, EU bloc, G77, BASIC) are well-studied

No published system specifically targets this, representing a significant opportunity.

---

## 3. Institutional Use Cases

### 3.1 Intelligence Community

Snow Globe has the strongest institutional validation here. The CIA's Center for the Study of Intelligence published a study on Snow Globe in *Studies in Intelligence* (Vol. 69, No. 4, December 2025), documenting "Lessons from Human-AI Teaming in War Games." IQT Labs (In-Q-Tel's applied research arm) built an integration between Snow Globe and the ICB Project, a dataset of 496 historical geopolitical crisis scenarios.

**Key institutional use:** Analysts use the system to rapidly explore "what if" branches of developing situations, testing how different actors might respond to events before they unfold.

### 3.2 Think Tanks and Policy Research Organizations

**CSIS (Center for Strategic and International Studies)** is the leading example:
- Partnered with Scale AI specifically to explore LLM applications in strategic-level wargaming
- The CSIS Futures Lab researches how AI-enabled wargaming affects force planning, information operations, and professional military education
- Published the influential report "It Is Time to Democratize Wargaming Using Generative AI" arguing that AI wargaming could replace exercises costing "hundreds of thousands to millions of dollars"

**New Lines Institute** partnered with Mantis Analytics (September 2025) to launch an AI-powered geopolitical risk assessment platform that uses intelligent agents to track signals and model emerging risk dynamics.

### 3.3 Military Education and Planning

**U.S. Army Command and General Staff College (CGSC):** AI-enabled wargaming will become the default method in every CGSC planning exercise starting academic year 2026-2027.

**Johns Hopkins APL GenWar Lab:** Dedicated facility (opening 2026) that leverages LLMs to support wargames and tabletop exercises. The GenWar TTX system enables senior military commanders and civilian leaders to engage in AI-agent-assisted tabletop exercises, reducing wargame planning cycles from months to as little as two weeks.

**Army War College:** Uses LLMs for ethical adjudication in Free Kriegsspiel exercises, preventing biases in unclassified scenarios.

### 3.4 International Organizations

No confirmed production deployment, but the UN, EU, and NATO are natural customers for:
- Treaty negotiation scenario planning (simulating member-state positions before summits)
- Sanctions impact modeling (simulating how target states and third parties adapt)
- Peacekeeping force deployment planning (modeling local faction responses)
- Humanitarian crisis response coordination

### 3.5 Academic Political Science

WarAgent and FlockVote both emerged from academic research groups. Key departments:
- Computational social science programs using LLM simulations as "computational laboratories"
- International relations departments using historical crisis replay for teaching
- Public policy schools using stakeholder simulation for curriculum exercises

### 3.6 Corporate Government Affairs and Regulatory Strategy

Enterprises need to anticipate regulatory changes and model their impact. Applications include:
- Simulating how proposed regulations affect business operations before lobbying
- Modeling competitor responses to regulatory changes
- Testing compliance strategies against different enforcement scenarios
- War-gaming M&A approval processes with antitrust regulators

---

## 4. Methodological Considerations

### 4.1 Validation Against Real Outcomes

The central challenge. A 2025 systematic review ("Validation is the central challenge for generative social simulation," PMC) found that LLMs may *exacerbate* rather than alleviate validation challenges due to their black-box structure, cultural biases, and stochastic outputs.

**Practical validation approaches:**
- **Hindcasting:** Run simulations of historical events and compare to known outcomes (as WarAgent does with WWI/WWII)
- **Observable scenario comparison:** Run simulations of upcoming routine events, then compare to actual outcomes (as the emergency preparedness study did with commencement crowd flows)
- **Expert review:** Have domain experts evaluate whether agent behaviors and reasoning are plausible
- **Ablation studies:** Systematically remove simulation components to identify which elements drive results

### 4.2 Ensemble Approaches

Running many simulations is essential, not optional:
- Snow Globe's original paper demonstrates running "repeated iterations of the same simulation with randomized LLM output" to show "a range of possible outcomes"
- FlockVote runs multiple instances to produce outcome distributions rather than point predictions
- The FOMC In Silico system combines LLM simulation with Monte Carlo Bayesian voting models
- Cross-model ensembles (running the same scenario across different LLM providers) can identify model-specific biases

### 4.3 Calibration Against Historical Events

**IQT's ICB integration** provides the strongest existing approach: 496 historical geopolitical crises with documented actors, actions, and outcomes. This enables systematic calibration across a large corpus rather than cherry-picked scenarios.

**Challenges:**
- Nearly all current studies rely on zero-shot prompting --- "calibration" reduces to prompt engineering
- LLMs trained on historical data may simply recall events rather than reasoning about them
- Rare, high-impact events (which matter most for policy) have the fewest calibration examples

### 4.4 Combining with Traditional Methods

LLM simulation works best as a complement to, not replacement for, traditional policy analysis:
- Use simulations to *generate* hypotheses, then test them with quantitative models
- Use domain experts to *seed* agent personas with accurate belief systems
- Use simulations to *stress-test* conclusions from conventional analysis
- Use ensemble results to *bound* uncertainty ranges from formal models

### 4.5 Peer Review and Transparency

CSIS's report identifies a critical gap: wargaming results are rarely shared across agencies, reducing their cumulative value. AI-enabled simulations could address this through:
- Documented prompts and agent configurations as reproducible methods sections
- Structured data labeling of simulation outputs for meta-analysis
- Open-source frameworks (like Snow Globe) that enable independent replication
- Version-controlled scenario definitions that allow exact reproduction

---

## 5. Existing Precedents

### 5.1 Production or Near-Production Systems

| System | Developer | Status | Application |
|--------|-----------|--------|-------------|
| **Snow Globe** | IQT Labs / CIA CSI | Published in *Studies in Intelligence* (Dec 2025); open-source | Political wargaming with human-AI teaming |
| **GenWar TTX** | Johns Hopkins APL | Dedicated lab opening 2026 | Senior leader tabletop exercises |
| **CSIS + Scale AI** | CSIS Futures Lab | Active partnership since 2023 | Strategic-level wargaming, decision support |
| **Mantis + New Lines** | Mantis Analytics / New Lines Institute | Launched September 2025 | Geopolitical risk assessment and forecasting |
| **SIM-1** | Fable Studio | Demonstrated 2024-2025 | Crisis scenario simulation with 3D visualization |

### 5.2 Research Systems

| System | Institution | Publication | Application |
|--------|-------------|-------------|-------------|
| **WarAgent** | AGI Research Group | NeurIPS 2024 (OpenReview) | Historical conflict simulation (WWI, WWII) |
| **FlockVote** | Academic | ICAIS 2025 | U.S. presidential election simulation |
| **Richelieu** | Academic | NeurIPS 2024 | AI diplomacy with self-evolving agents |
| **FOMC In Silico** | GWU | Working Paper 2025 | Federal Reserve monetary policy simulation |
| **MiniFed** | Academic | arXiv 2024 | FOMC meeting simulation |
| **ElectionSim** | Academic | arXiv 2024 | Massive-scale election simulation |
| **Political Actor Agent** | Academic | AAAI 2025 | Legislative roll-call vote simulation |

### 5.3 Institutional Adoption Timeline

- **2022:** Meta's Cicero demonstrates human-level Diplomacy play
- **2023:** CSIS partners with Scale AI for LLM wargaming; IQT Labs releases Snow Globe
- **2024:** WarAgent, Richelieu published at NeurIPS; Fable demonstrates SIM-1; Snow Globe paper on arXiv
- **2025:** CIA publishes Snow Globe findings; CGSC mandates AI wargaming for AY2026-27; New Lines/Mantis launch commercial platform; FlockVote validated against 2024 election; FOMC simulation papers published; APL announces GenWar Lab
- **2026:** GenWar Lab facility opens; AI wargaming becomes standard in U.S. military education

---

## 6. Revenue and Sustainability

### 6.1 Market Sizing

The geopolitical risk analytics platform market was valued at approximately $3.5 billion globally in 2025, with AI and predictive analytics engines growing at the fastest CAGR of 17.42% through 2035. The broader market is projected to reach $15.26 billion by 2035. The AI agents market overall is projected to grow from $7.84 billion (2025) to $52.62 billion (2030).

### 6.2 Revenue Models

**Tier 1 --- Government/Defense Contracts:**
- Direct contracts with defense agencies, intelligence community, and state departments
- Current wargames cost $100K-$1M+ each; AI-enabled versions at 10-20% of that cost represent clear value
- Long-term maintenance and scenario development contracts
- Precedent: Scale AI's CSIS partnership; IQT Labs' Snow Globe development

**Tier 2 --- Policy Consulting Platform (SaaS):**
- Subscription access for think tanks, academic institutions, and NGOs
- Pay-per-simulation for ad hoc scenario analysis
- Tiered pricing by agent count, simulation complexity, and model provider
- Precedent: Mantis Analytics' commercial platform with New Lines Institute

**Tier 3 --- Corporate Government Affairs:**
- Regulatory impact simulation for enterprises facing policy changes
- M&A scenario planning for antitrust review processes
- Geopolitical supply chain risk assessment
- Bundled with consulting services for interpretation and strategy development

### 6.3 Productization Path

Following the pattern identified in AI consulting market analysis:

1. **Services phase:** Run custom simulations for specific clients (government, think tanks). Build domain expertise and scenario libraries.
2. **Platform phase:** Standardize the most common simulation types (crisis response, regulatory impact, diplomatic negotiation) into configurable products.
3. **Marketplace phase:** Enable third parties to create and share scenario templates, agent personas, and validation datasets.

Snow Globe's open-source, model-agnostic architecture (OpenRouter integration, YAML-based configuration, pluggable model pools) is well-suited for this progression.

### 6.4 Competitive Landscape

- **Mantis Analytics:** Funded startup, commercial geopolitical risk platform, partnership with established think tank
- **Fable Studio (SIM-1):** 3D-visualized simulations, entertainment-adjacent positioning
- **Scale AI:** Enterprise AI, defense partnerships, CSIS collaboration
- **Johns Hopkins APL (GenWar):** Government-funded, defense-focused, not commercially available
- **Palantir / Anduril:** Adjacent capabilities in defense AI, potential entrants

### 6.5 Differentiation Opportunities for Snow Globe

- **Open-source foundation:** Transparency and reproducibility that classified systems cannot offer; essential for academic and NGO adoption
- **Model diversity:** OpenRouter integration means simulations are not locked to a single LLM provider, enabling cross-model ensemble analysis
- **Current events integration:** Tavily-powered planning agent automatically grounds simulations in real-world context
- **Lightweight deployment:** No GPU cluster required; runs on commodity hardware
- **Human-AI hybrid play:** Proven in CIA-published research as the most trusted configuration

---

## 7. Key Risks and Open Questions

1. **Validation gap:** The field lacks standardized methods for validating policy simulation outputs. Without this, institutional adoption will remain limited to exploratory use.
2. **Bias amplification:** LLMs carry training biases that may systematically skew simulation results (e.g., Western-centric worldviews, political biases). Cross-model ensembles mitigate but do not eliminate this.
3. **Overconfidence risk:** Policymakers may treat simulation outputs as predictions rather than scenario explorations. Clear communication of uncertainty is essential.
4. **Adversarial manipulation:** If simulation frameworks become influential in policy, there is incentive to manipulate agent personas or scenario definitions to produce preferred outcomes.
5. **Classification tension:** The most valuable applications (intelligence, defense) often require classified scenarios that cannot use open-source tools directly, limiting the feedback loop between public research and operational use.
6. **Reproducibility:** Non-deterministic LLM outputs mean exact reproduction is impossible; statistical reproducibility (similar distributions across runs) is the achievable standard.

---

## Sources

### Snow Globe and IQT Labs
- [Snow Globe GitHub (IQT Labs)](https://github.com/IQTLabs/snowglobe)
- [Snow Globe Multi-Player AI System --- CIA Studies in Intelligence, Vol. 69, No. 4 (December 2025)](https://www.cia.gov/resources/csi/studies-in-intelligence/studies-in-intelligence-vol-69-no-4-extracts-december-2025/snow-globe-multi-player-ai-system-lessons-from-human-ai-teaming-in-war-games)
- [Open-Ended Wargames with Large Language Models (arXiv:2404.11446)](https://arxiv.org/abs/2404.11446)

### Military and Defense
- [AI-Enabled Wargaming at U.S. Army CGSC --- Small Wars Journal (January 2026)](https://smallwarsjournal.com/2026/01/16/ai-enabled-wargaming-cgsc/)
- [GenWar Lab --- Johns Hopkins APL (October 2025)](https://www.jhuapl.edu/news/news-releases/251030-genwar-lab)
- [Generative AI Wargaming Promises to Accelerate Mission Analysis --- Johns Hopkins APL (March 2025)](https://www.jhuapl.edu/news/news-releases/250303-generative-wargaming)
- [AI for Wargaming and Modeling --- RAND (Davis & Bracken, 2025)](https://journals.sagepub.com/doi/abs/10.1177/15485129211073126)
- [Back to the Basics in Wargaming --- U.S. Army War College War Room](https://warroom.armywarcollege.edu/articles/back-to-the-basics/)

### Think Tanks and Policy
- [It Is Time to Democratize Wargaming Using Generative AI --- CSIS](https://www.csis.org/analysis/it-time-democratize-wargaming-using-generative-ai)
- [Scale AI + CSIS Partnership Announcement](https://scale.com/blog/scale-csis-partnership-announcement)
- [AI Start-up Partners with Policy Think Tank --- New Lines Institute (September 2025)](https://newlinesinstitute.org/political-systems/ai-start-up-partners-with-policy-think-tank-to-launch-customizable-geopolitical-risk-assessment-solution/)

### Diplomacy and Negotiation
- [Richelieu: Self-Evolving LLM-Based Agents for AI Diplomacy --- NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/df2d62b96a4003203450cf89cd338bb7-Paper-Conference.pdf)
- [Assessing Cicero's Diplomacy Play --- ACL 2024](https://aclanthology.org/2024.acl-long.672.pdf)
- [How Well Can LLMs Negotiate? NegotiationArena --- ICML 2024](https://raw.githubusercontent.com/mlresearch/v235/main/assets/bianchi24a/bianchi24a.pdf)
- [Democratizing Diplomacy: A Harness for Evaluating Any LLM (arXiv:2508.07485)](https://arxiv.org/pdf/2508.07485)

### Conflict Simulation
- [WarAgent: LLM-based Multi-Agent Simulation of World Wars](https://arxiv.org/abs/2311.17227)
- [SIM-1 Wargames --- Fable Studio](https://fablestudio.github.io/openai-wargames/)
- [LLM-based Wargame Scenario Generation --- Simulation journal (2026)](https://journals.sagepub.com/doi/10.1177/00375497251415245)

### Election and Public Opinion
- [FlockVote: LLM-Empowered Agent-Based Modeling for Simulating U.S. Presidential Elections (arXiv:2512.05982)](https://arxiv.org/abs/2512.05982)
- [ElectionSim: Massive Population Election Simulation (arXiv:2410.20746)](https://arxiv.org/html/2410.20746v2)
- [Political Actor Agent: Simulating Legislative System --- AAAI 2025](https://ojs.aaai.org/index.php/AAAI/article/view/32017/34172)

### Economic Policy
- [FOMC In Silico: Multi-Agent System for Monetary Policy --- GWU Working Paper 2025-005](https://www2.gwu.edu/~forcpgm/2025-005.pdf)
- [MiniFed: LLM-based Agentic-Workflow for Simulating FOMC (arXiv:2410.18012)](https://arxiv.org/html/2410.18012v1)
- [Modeling Hawkish-Dovish Latent Beliefs in Multi-Agent Systems (arXiv:2511.02469)](https://www.arxiv.org/pdf/2511.02469)

### Forecasting
- [AI-Augmented Predictions: LLM Assistants Improve Human Forecasting Accuracy --- LSE](https://eprints.lse.ac.uk/127059/3/3707649.pdf)
- [AIA Forecaster Technical Report (arXiv:2511.07678)](https://arxiv.org/html/2511.07678v1)
- [Training LLMs to Predict World Events --- Thinking Machines Lab](https://thinkingmachines.ai/news/training-llms-to-predict-world-events/)

### Validation Methodology
- [What Makes LLM Agent Simulations Useful for Policy? (arXiv:2509.21868)](https://arxiv.org/html/2509.21868v1)
- [Validation is the Central Challenge for Generative Social Simulation --- PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12627210/)
- [Towards Operational Validation of LLM-Agent Social Simulations (arXiv:2508.21740)](https://arxiv.org/pdf/2508.21740)

### Market Data
- [Geopolitical Risk Analytics Platform Market Forecast --- SNS Insider (April 2026)](https://www.globenewswire.com/news-release/2026/04/06/3268496/0/en/Geopolitical-Risk-Analytics-Platform-Market-to-Reach-USD-15-26-Billion-by-2035-Owing-to-Rising-Global-Uncertainties-and-Demand-for-Real-Time-Risk-Insights-SNS-Insider.html)
- [Generative Agent-Based Modeling (GABM) Overview --- Emergent Mind](https://www.emergentmind.com/topics/generative-agent-based-modeling-gabm)
