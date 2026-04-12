# Actor Schema Specification v1.0

Reusable schema for defining actors in snowglobe wargaming simulations.
Designed for geopolitical, diplomatic, and conflict scenarios but
applicable to any multi-agent simulation.

## Design Principles

1. **No monoliths** -- decompose states and organizations into their
   internal factions. "Iran" is not one actor; it is Khamenei, the IRGC,
   the Basij, the reformists, the street, and the diaspora.
2. **Capture asymmetry** -- not every actor has the same fields. A state
   leader has red lines and institutional constraints; a diaspora
   community has influence channels and internal divisions.
3. **Reusable clusters** -- actor files live in `config/actors/` and are
   referenced by any scenario. A scenario can filter to a subset via
   `active_actors`.
4. **Layered identity** -- separate the actor's *structural role* from
   their *behavioral model* from their *relational position*.

## YAML Schema

```yaml
# ---- Cluster-level metadata ----
name: "<cluster name>"           # Human-readable cluster name
description: >                   # What this cluster covers
  One-paragraph description of the actor set and its intended use.
version: "1.0"                   # Schema version for forward compat
domain: "<domain>"               # geopol | diplomatic | economic | military

# ---- Actor list ----
actors:
  - id: "<snake_case_id>"        # REQUIRED — unique within cluster
    name: "<display name>"       # REQUIRED — used in simulation output
    role: "<title or position>"  # REQUIRED — institutional role
    type: "<actor_type>"         # REQUIRED — see Actor Types below

    # ---- Behavioral Model ----
    persona: >                   # REQUIRED — core behavioral description
      Multi-sentence description of how this actor thinks, decides, and
      communicates. Should include decision-making style, historical
      precedents they draw on, and institutional culture.

    red_lines:                   # List of thresholds that trigger escalation
      - "<condition that changes behavior>"

    response_pattern: >          # Typical behavioral sequence
      How this actor typically responds to provocation or opportunity.
      Describes sequencing (e.g., "absorbs first blow, then retaliates
      via proxies before direct action").

    constraints:                 # Structural limits on action
      - "<institutional, political, or resource constraint>"

    # ---- Relational Position ----
    bloc: "<bloc_id>"            # Optional — for visibility/information rules
    allies:                      # Optional — named relationships
      - "<actor_id>"
    rivals:                      # Optional — named adversaries
      - "<actor_id>"
    patrons:                     # Optional — who this actor depends on
      - "<actor_id>"
    clients:                     # Optional — who depends on this actor
      - "<actor_id>"

    # ---- Capabilities (optional, domain-specific) ----
    capabilities:
      military:                  # Military assets/tools
        - "<capability>"
      economic:                  # Economic levers
        - "<capability>"
      intelligence:              # Intel/covert capabilities
        - "<capability>"
      diplomatic:                # Diplomatic channels
        - "<capability>"
      information:               # Media/narrative tools
        - "<capability>"

    # ---- Internal Dynamics (for composite actors) ----
    internal_factions:           # Sub-groups within this actor
      - name: "<faction name>"
        position: >
          Brief description of this faction's stance.

    # ---- Influence Model (for non-executive actors) ----
    influence:
      channels:                  # How this actor exerts influence
        - "<channel: protests | lobbying | media | arms | funding>"
      reach: "<local | national | regional | global>"
      leverage: "<description of what gives this actor weight>"

    # ---- Metadata ----
    tier: "<primary | secondary | tertiary>"  # Simulation priority
    active_by_default: true      # Whether included without explicit selection
    tags:                        # Searchable labels
      - "<tag>"
```

## Actor Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `state_leader` | Head of state or government | persona, red_lines, constraints |
| `state_institution` | Military, intelligence, ministry | persona, constraints, capabilities |
| `sub_state_faction` | Internal political faction, militia | persona, influence, internal_factions |
| `non_state_armed` | Militia, insurgent, proxy force | persona, red_lines, capabilities, patrons |
| `opposition` | Domestic political opposition | persona, influence, constraints |
| `civil_society` | Activists, dissidents, NGOs | persona, influence |
| `diaspora` | Exile community, diaspora lobby | persona, influence, internal_factions |
| `multilateral` | UN, EU, Arab League, etc. | persona, constraints, capabilities.diplomatic |
| `mediator` | State or org acting as go-between | persona, capabilities.diplomatic |
| `economic` | Central bank, sovereign fund, market | persona, capabilities.economic |
| `religious` | Religious authority or institution | persona, influence, constraints |
| `media` | News organization, propaganda outlet | persona, influence |

## Tier System

- **primary** — direct decision-makers whose actions drive the simulation.
  Always active. Get full response turns.
- **secondary** — significant actors who shape the environment. Active by
  default but can be filtered out for faster runs.
- **tertiary** — background actors whose influence is felt indirectly.
  Included in comprehensive runs; omitted in quick runs.

## Cluster Organization

```
config/actors/
  iran-israel-core.yaml       # 10-actor lightweight set
  iran-israel-full.yaml       # 25+ actor comprehensive set
  south-china-sea.yaml        # Future scenario cluster
  ukraine-front.yaml          # Future scenario cluster
```

Scenarios reference clusters by name:

```yaml
# In config/scenarios/some-scenario.yaml
actor_cluster: iran-israel-full
active_actors:                  # Optional filter — omit to use all
  - khamenei
  - netanyahu
  - hezbollah
```

## Persona Writing Guidelines

1. **Ground in history** — reference specific past decisions, not
   abstract tendencies. "Restrained response after Soleimani 2020"
   beats "tends toward restraint."
2. **Name the decision process** — "consultative via small inner circle"
   or "impulsive, reverses within 24 hours" tells the LLM *how* the
   actor decides, not just *what* they decide.
3. **Include contradictions** — real actors have competing incentives.
   "Must not appear weak domestically" AND "sanctions-induced pressure
   limits tolerance for sustained conflict" creates realistic tension.
4. **Specify information access** — what does this actor know? A street
   protest movement has different intelligence than a state leader.
5. **For composite actors** — describe the internal disagreement. The
   IRGC is not one mind; the Quds Force and Aerospace Force have
   different priorities.

## Compatibility

This schema is designed for the snowglobe simulation engine but can be
consumed by any multi-agent system. The `persona` field is the minimum
viable actor definition; all other fields enrich simulation fidelity.

Fields like `bloc`, `allies`, `rivals` are currently informational
(included in the generated persona prompt). Future graph config support
will use these for visibility rules and information asymmetry.
