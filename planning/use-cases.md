# Geopol Forecaster / Geopol Modeller — Use Case Roadmap

Potential applications of multi-actor LLM simulation beyond the current
Iran-Israel conflict scenario. The core engine is domain-agnostic; these
use cases require only new scenario YAML, actor clusters, and optional
graph configs.

## Geopolitical Forecasting & Conflict Simulation

The primary use case. Fast-moving crises where affected populations need
actionable predictions.

| Scenario | Actor Complexity | Notes |
|----------|-----------------|-------|
| Iran-Israel war (active) | 25+ actors | Current focus. Internal dynamics critical. |
| South China Sea escalation | 15-20 actors | US, China, Taiwan, Philippines, Japan, ASEAN |
| Ukraine front-line evolution | 15+ actors | Military + diplomatic + domestic politics |
| Korean Peninsula crisis | 10-15 actors | DPRK, ROK, US, China, Japan |
| India-Pakistan escalation | 10-15 actors | Nuclear dimension, Kashmir trigger |
| Horn of Africa (Ethiopia, Sudan) | 15+ actors | Multi-ethnic, multi-state, humanitarian |

## Foreign Policy Simulation

Testing policy options before implementation. A government analyst could
define their country's decision-maker as a controllable actor and test
different policy choices against the responses of other actors.

| Scenario | Use | Notes |
|----------|-----|-------|
| Sanctions impact modelling | Test sanctions regimes against target-state responses | Economic + political actors |
| Alliance stress-testing | Model how alliance commitments hold under pressure | NATO Article 5 scenarios |
| Treaty negotiation simulation | Pre-negotiate by modelling counterpart responses | Trade, arms control, climate |
| Diplomatic recognition scenarios | Model cascading effects of recognition decisions | Taiwan, Palestine, Kosovo |

## Worst-Case Scenario Planning

"Pre-mortems" for geopolitical risks. Run the simulation with `nature`
set high and the shock taxonomy configured for maximum disruption.

| Scenario | Purpose |
|----------|---------|
| Strait of Hormuz closure | Energy security planning for import-dependent states |
| Suez Canal blockage (military) | Global supply chain stress test |
| Simultaneous multi-front war | Force planning and readiness assessment |
| Nuclear escalation ladder | At what point do actors cross the nuclear threshold? |
| Cyber-physical attack on infrastructure | How do states respond to ambiguous attacks? |

## Domestic Policy Simulation

The actor-based approach applies to any multi-stakeholder decision
environment. Domestic policy involves actors with competing interests,
constraints, and red lines — exactly what the simulation models.

| Scenario | Actors | Notes |
|----------|--------|-------|
| Noise pollution regulation | Municipal council, residents, businesses, enforcement, developers, nightlife industry | Classic NIMBY multi-stakeholder |
| Housing policy reform | Government, developers, NIMBYs, renters, banks, construction unions | Red lines and coalition dynamics |
| Public transit planning | City planners, commuters, car lobby, environmental groups, budget office | Trade-offs and competing priorities |
| Healthcare system reform | Government, hospitals, insurers, doctors' unions, patients, pharma | Institutional constraints |
| Education curriculum reform | Ministry, teachers' unions, parents, religious groups, employers | Cultural red lines |
| Climate adaptation planning | City, residents, industry, environmental groups, insurers, federal gov | Long-term vs. short-term tension |

## Economic & Market Simulation

Model market participants as actors with strategies, constraints, and
information asymmetry.

| Scenario | Actors | Notes |
|----------|--------|-------|
| Trade war escalation | Governments, industries, supply chains, consumers, WTO | Tariff/retaliation cycles |
| Central bank policy coordination | Fed, ECB, BoJ, BoE, emerging market CBs, markets | Interest rate game theory |
| Sovereign debt crisis contagion | Debtor state, creditor nations, IMF, markets, neighbours | Cascading default modelling |
| Energy transition dynamics | Oil producers, renewables, governments, utilities, consumers | Stranded asset risk |
| Tech regulation | Governments, tech platforms, users, advertisers, civil society | Regulatory arbitrage |
| Sanctions impact wargaming | Target state, sanctioning coalition, neutral states, markets, smuggling networks | Each model as a national economic perspective |

## Predictive Forecasting & Verification

Structured prediction through adversarial multi-model analysis.

| Scenario | Actors/Lenses | Notes |
|----------|---------------|-------|
| Election outcome forecasting | Polling analyst, economic lens, sentiment analyst, historical pattern analyst | Multipolar analytical lenses, not role-play |
| Ceasefire durability scoring | Each stakeholder assesses agreement survivability from their position | Post-agreement stress-testing |
| Treaty compliance monitoring | Compliance advocate, violation hunter, adjudicator | Adversarial analysis structure |
| Disinformation campaign attribution | Linguistics analyst, network topology, timing analyst, narrative analyst | Multi-domain forensic analysis |
| Climate-security nexus forecasting | Climate modeller, livelihood analyst, political analyst, conflict researcher | Causal chain modelling |
| Generational leadership transition | Successor factions, old guard, military, external patrons | Succession dynamics in opaque regimes |

## International Institutional Simulation

Modelling formal international bodies with well-defined rules, voting
records, and quantifiable preferences. These are particularly amenable
to simulation because their procedures are documented and their actors'
historical positions are on record.

### Highly Modelable Bodies

| Body | Members | Why Simulable |
|------|---------|---------------|
| UN Security Council | 15 (5 veto) | Complete voting records, veto mechanics, narrow mandate |
| OPEC+ | ~23 | Quantified production quotas, transparent economic incentives |
| European Council | 27 | QMV mathematics, population-weighted votes, VoteWatch data |
| FOMC | 12 voting | Published transcripts, dot plots, estimable reaction functions |
| IAEA Board | 35 | Nuclear mandate, non-proliferation voting patterns |
| IMF Executive Board | 24 | Weighted voting, lending decision frameworks |
| FATF Plenary | 39 | Defined scoring criteria, grey/black list decisions |

### Moderately Modelable Bodies

| Body | Members | Notes |
|------|---------|-------|
| Arctic Council | 8 | Consensus, geographic focus, climate + sovereignty |
| Nuclear Suppliers Group | 48 | Consensus, India membership blocking dynamics |
| OPCW Executive Council | 41 | Compliance disputes, Syria precedent |
| ICJ | 15 judges | Published voting records and opinions |
| IPCC Approval Plenaries | 195 | SPM line-by-line negotiation |

## Humanitarian & Crisis Response

Simulate coordination failures and resource allocation in crisis
response.

| Scenario | Actors | Notes |
|----------|--------|-------|
| Refugee flow prediction | Origin, transit, destination countries, UNHCR, smugglers | Coordination failure modelling |
| Pandemic response coordination | WHO, national governments, pharma, public, media | Information asymmetry critical |
| Natural disaster response | National/local government, military, NGOs, affected population, donors | Resource allocation |
| Maritime chokepoint disruption | Shipping, insurers, navies, port states, commodity traders | Cascading supply chain effects |

## Democratic Resilience & Constitutional Stress-Testing

Simulate constitutional crises and institutional resilience. Each
branch of government, the military, civil society, and the judiciary
operate as actors with their own red lines and institutional incentives.

| Scenario | Actors | Notes |
|----------|--------|-------|
| Constitutional crisis red-teaming | Executive, legislature, judiciary, military, civil society | Democratic backsliding scenarios |
| Post-conflict power-sharing design | Ethnic/religious factions, military, external guarantors | Iteratively negotiate and stress-test provisions |
| Electoral dispute escalation | Incumbent, challenger, courts, military, street, international observers | Contested election dynamics |

## Ideological Lens Analysis (Panel Mode)

Not role-play but analytical framework simulation. Each "actor" is an
analytical perspective applied to the same problem. Draws from the
Panel-Of-Claude two-round deliberation pattern.

| Framework Set | Lenses | Use |
|---------------|--------|-----|
| IR theory | Realist, liberal institutionalist, constructivist, Marxist, postcolonial | Foreign policy analysis |
| Economic schools | Keynesian, monetarist, Austrian, MMT, development economics | Fiscal/monetary policy |
| Ethical frameworks | Utilitarian, deontological, virtue ethics, care ethics | Bioethics, AI ethics, policy ethics |
| Security studies | Traditional, human security, critical security, feminist security | Threat assessment |

## Integration Patterns from Related Projects

### From AI-Agent-UN
- **Voting simulation**: Define a resolution and have actors vote with
  structured justification. Applicable to any scenario ending in a
  formal decision (treaty, sanctions vote, policy adoption).
- **Bilateral impact analysis**: Post-simulation assessment of how the
  outcome affected pairwise relationships.

### From Peace In The Middle East
- **Chamber structure**: Plenary sessions + working groups + back-channels.
  Applicable to any negotiation scenario.
- **Facilitator agent**: Neutral moderator that manages speaking order
  and enforces procedural rules. Useful for diplomatic simulations.
- **Sub-faction decomposition**: The granular actor modelling approach
  (150+ actors for the Middle East) sets the standard for fidelity.

### From Panel-Of-Claude
- **Two-round deliberation**: Independent analysis → cross-pollination.
  Applicable to policy analysis scenarios where you want multiple
  analytical frameworks rather than role-playing.
- **Tension mapping**: Instead of declaring winners, map where genuine
  value conflicts exist. Better output for policy analysis than
  narrative adjudication.
- **Motion decomposition**: Break complex problems into problem statements,
  causal claims, and implicit questions before simulation.

### From Claude-AI-Conference
- **Agent clustering**: Organise large actor sets into thematic clusters.
  Already implemented via actor cluster YAML.
- **Identity generation**: Generate credible fictional identities for
  actors when simulating generic roles (e.g., "a municipal council
  member" rather than a named individual).
- **Broadcast mode**: Not all simulations need interactive debate. Some
  scenarios benefit from each actor independently assessing the
  situation, with synthesis happening post-hoc.

## Priority Roadmap

### Near-term (current sprint)
1. Iran-Israel full actor cluster (done)
2. Scenario subgraph config system (done — config format)
3. Information asymmetry implementation in core engine
4. Escalation ladder structured output

### Medium-term
5. Ensemble forecasting (multi-run aggregation)
6. Adaptive timestep implementation
7. Exogenous shock injection system
8. Second conflict scenario (South China Sea or Ukraine)
9. Domestic policy scenario template

### Long-term
10. Panel-Of-Claude tension mapping mode
11. AI-Agent-UN voting mode
12. PITME facilitator/chamber mode
13. Public API for simulation results
14. Calibration feedback loop from accuracy grading
