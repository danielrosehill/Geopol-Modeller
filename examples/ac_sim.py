#!/usr/bin/env python3

#   Copyright 2023-2025 IQT Labs LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Azuristan vs Crimsonia — AI-vs-AI geopolitical simulation.

Uses OpenRouter model pools and optional Tavily briefing.
"""

import asyncio
import os

import geopol_forecaster as geopol


async def run_simulation(pool_name=None, verbosity=1):
    # Load pools config
    pools_path = os.path.join(os.path.dirname(__file__), "..", "config", "pools.yaml")
    pools, active, base_url = geopol.core.load_pools(pools_path)
    pool = pools.get(pool_name or active)

    # Create LLM client
    client = geopol.LLMClient(base_url=base_url)

    # Scenario
    title = "Azuristan and Crimsonia"
    scenario = """\
Azuristan and Crimsonia are neighboring countries in Central Asia.  Azuristan is a \
Western-backed democracy that suffers from endemic corruption.  Crimsonia is controlled \
by an autocratic government that stifles dissent and commits human rights violations.

Both countries have modern professional militaries, although Crimsonia's is slightly \
larger than Azuristan's.  In addition, Azuristan possesses ten nuclear weapons and \
Crimsonia has eight.

Most citizens of Azuristan are from the Azuristani ethnic group, and most citizens of \
Crimsonia are from the Crimsonian ethnic group.  The only exception is Azuristan's \
province of Tyriana, on the border with Crimsonia.  Most residents of Tyriana belong \
to the Crimsonian ethnic group.

The animosity between Azuristan and Crimsonia extends back over centuries of ethnic \
tension and intermittent warfare.  Recent years have been fairly calm.  However, that \
suddenly changes when Tyriana declares independence.  Amidst the crisis, local leaders \
in Tyriana ask Crimsonia to come to the province's defense, and the same leaders \
indicate that they want Tyriana to become part of Crimsonia."""

    goals = {
        'azuristan_dove': "Your goal is to avoid war at all costs, and to preserve the sovereignty of Azuristan if possible.",
        'crimsonia_dove': "Your goal is to avoid war at all costs, and to unify the Crimsonian people if possible.",
    }

    # Planning agent — research current events
    planner = geopol.PlanningAgent(
        llm_client=client, model=pool.planner, verbosity=verbosity
    )
    briefing = await planner.create_briefing(scenario=scenario, title=title)

    # Set up dummy database (no human players in this sim)
    db_path = os.path.join(os.path.dirname(__file__), "..")
    db = geopol.Database(ioid="sim_ac", path=db_path, initialize=True)

    # Create players
    players = [
        geopol.Player(
            database=db,
            verbosity=verbosity,
            llm_client=client,
            model_id=pool.player,
            name="President of Azuristan",
            persona=f"the leader of Azuristan. {goals['azuristan_dove']}",
        ),
        geopol.Player(
            database=db,
            verbosity=verbosity,
            llm_client=client,
            model_id=pool.player,
            name="Premier of Crimsonia",
            persona=f"the leader of Crimsonia. {goals['crimsonia_dove']}",
        ),
    ]

    # Create narrator (Control)
    narrator = geopol.Control(
        database=db,
        verbosity=verbosity,
        llm_client=client,
        model_id=pool.narrator,
    )

    # Build the simulation graph callbacks
    async def player_respond_fn(player_config, history):
        player_obj = next(p for p in players if p.name == player_config["name"])
        # Build a History object from the state's history list
        h = geopol.History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        # Inject briefing into the history if not already there
        return await player_obj.respond(history=h)

    async def adjudicate_fn(history, responses, nature, timestep, mode):
        h = geopol.History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        r = geopol.History()
        for entry in responses:
            r.add(entry["name"], entry["text"])
        return await narrator.adjudicate(
            history=h, responses=r, nature=nature, timestep=timestep, mode=mode
        )

    async def assess_fn(history, query, mc=None):
        h = geopol.History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        return await narrator.assess(history=h, query=query, mc=mc)

    # Run via LangGraph
    graph = geopol.build_simulation_graph()
    initial_state = {
        "scenario": scenario,
        "briefing": briefing,
        "title": title,
        "timestep": "month",
        "nature": 1.0,
        "mode": ["geopol"],
        "player_configs": [
            {"name": p.name, "persona": p.persona, "model_id": p.model_id}
            for p in players
        ],
        "moves_total": 3,
        "move_current": 0,
        "current_player_idx": 0,
        "history": [],
        "current_responses": [],
        "questions": ["In one sentence, what was the outcome?"],
        "mc_questions": [
            ["What was the final status of Tyriana?", ["part of Azuristan", "part of Crimsonia", "independent", "not yet determined"]],
            ["Did armed conflict occur?", ["yes", "no"]],
        ],
        "assessments": [],
        "_player_respond": player_respond_fn,
        "_adjudicate": adjudicate_fn,
        "_assess": assess_fn,
        "_verbosity": verbosity,
    }

    result = await graph.ainvoke(initial_state)

    print("\n\n=== ASSESSMENTS ===\n")
    for a in result.get("assessments", []):
        print(f"Q: {a['question']}")
        print(f"A: {a['answer']}")
        print()

    return result


if __name__ == "__main__":
    import sys
    pool = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_simulation(pool_name=pool))
