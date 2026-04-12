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

import re
import random
import asyncio

from .intelligent import Intelligent
from .llm import LLMClient
from .player import Player
from .stateful import Stateful


class Control(Intelligent, Stateful):
    def __init__(
        self,
        database,
        verbosity,
        name="Control",
        kind='ai',
        logger=None,
        llm_client=None,
        model_id=None,
        ioid=None,
        iodict=None,
        presets=None,
        **kwargs
    ):
        Intelligent.__init__(
            self,
            database=database,
            verbosity=verbosity,
            kind=kind,
            name=name,
            iodict=iodict,
            logger=logger,
            ioid=ioid,
            **kwargs
        )
        Stateful.__init__(self, **kwargs)

        self.llm_client = llm_client if llm_client is not None else LLMClient()
        self.model_id = model_id
        self.name = name
        self.persona = None
        self.ioid = ioid
        self.iodict = iodict
        self.presets = presets

    async def __call__(self):
        raise Exception(
            "! Override this method in the subclass for your specific scenario."
        )

    def run(self, *args, **kwargs):
        asyncio.run(self(*args, **kwargs))

    def header(self, title, h=0, width=80):
        print()
        if h == 0:
            print("+-" + "-" * min(len(title), width - 4) + "-+")
            print("| " + title + " |")
            print("+-" + "-" * min(len(title), width - 4) + "-+")
        elif h == 1:
            print("-" * min(len(title), width))
            print(title)
            print("-" * min(len(title), width))
        else:
            print(title)

    async def adjudicate(
        self,
        history=None,
        responses=None,
        query=None,
        nature=True,
        timestep="week",
        mode=[],
    ):
        responses_intro = "These are the plans for each person or group"
        if "geopol" in mode:
            responses_intro = (
                "These are the orders and decisions issued by each leader or actor"
            )
        if query is None:
            if "geopol" in mode:
                query = (
                    f"Narrate what happens over the next {timestep} as these "
                    f"orders are carried out. For each actor's actions, describe: "
                    f"(1) what they attempt, (2) how other actors and real-world "
                    f"constraints shape the outcome, (3) second-order consequences "
                    f"and reactions from affected parties. "
                    f"Be specific about mechanisms — name the diplomatic channel, "
                    f"military unit, economic lever, or intelligence operation. "
                    f"End with a brief STATUS section listing each actor's position "
                    f"at the close of this period."
                )
            else:
                query = (
                    f"Weave these plans into a cohesive narrative of what happens "
                    f"in the next {timestep}. Describe concrete outcomes, not just "
                    f"intentions. Include how plans interact, conflict, or reinforce "
                    f"each other."
                )
            if random.random() < nature:
                query += (
                    " Include at least one unexpected consequence — an unintended "
                    "side-effect, intelligence failure, accident, or miscalculation "
                    "that none of the actors planned for."
                )
        output = await self.return_output(
            history=history,
            responses=responses,
            responses_intro=responses_intro,
            query=query,
            query_format="oneline",
        )
        if "summarize" in mode:
            print("\n### Summary\n")
            template = "Give a short summary of the News.\n\n### History:\n\n{history}\n\n### News:\n\n{news}\n\n### Summary of the News:\n\n"
            variables = {"history": await history.textonly(), "news": output}
            output = await self.return_output(template=template, variables=variables)
        return output

    async def assess(
        self, history=None, responses=None, query=None, mc=None, short=False
    ):
        responses_intro = "Questions about what happened"
        if responses is None:
            query_format = "twoline"
        else:
            query_format = "twoline_simple"

        # Enhance assessment queries with structured prediction guidance
        enhanced_query = query
        if mc is None and query and not query.startswith("STRUCTURED:"):
            enhanced_query = (
                f"{query}\n\n"
                f"In your answer, be specific and falsifiable. Include:\n"
                f"- Your assessment of the most likely outcome\n"
                f"- A probability estimate (e.g. '65% likely')\n"
                f"- The time horizon over which this applies\n"
                f"- Key indicators that would confirm or refute this assessment\n"
                f"- The main alternative scenario and its probability"
            )

        bind = {"stop": ["\n\n"]} if short else None
        output = await self.return_output(
            bind=bind,
            history=history,
            history_over=True,
            responses=responses,
            responses_intro=responses_intro,
            query=enhanced_query,
            query_format=query_format,
        )
        if mc is not None:
            output = await self.multiple_choice(query, output, mc)
        return output

    def chat(self, history=None):
        name = self.name
        persona = "the Control (a.k.a. moderator) of a simulated scenario"
        return self.chat_terminal(name=name, persona=persona, history=history)

    async def create_scenario(self, query=None, clip=0):
        if query is None:
            raise Exception("Query required to create scenario.")
        output = await self.return_output(query=query, query_format="twoline_simple")
        if clip > 0:
            output = "\n\n".join(output.split("\n\n")[:-clip])
        return output

    async def create_players(
        self,
        scenario,
        max_players=None,
        query=None,
        others=False,
        pattern_sep=None,
        pattern_left=None,
    ):
        if query is None:
            query = "List the key players in this scenario, separated by semicolons."
        if pattern_sep is None:
            pattern_sep = r"[\.\,;\n0-9]+"
        if pattern_left is None:
            pattern_left = " ()-"
        template = "Scenario: {scenario}\n\nQuestion: {query}\n\nAnswer: "
        variables = {"scenario": scenario, "query": query}
        output = await self.return_output(template=template, variables=variables)
        names = re.split(pattern_sep, output)
        names = [name.lstrip(pattern_left).rstrip() for name in names]
        names = [name for name in names if len(name) > 0]
        if max_players is None:
            player_names = names
            other_names = []
        else:
            player_names = names[:max_players]
            other_names = names[max_players:]
        players = [
            Player(
                database=self.db,
                verbosity=self.verbosity,
                llm_client=self.llm_client,
                model_id=self.model_id,
                name=name,
                persona=name,
            )
            for name in player_names
        ]
        if not others:
            return players
        else:
            return players, other_names

    async def create_inject(self, history=None, query=None):
        if query is None:
            raise Exception("Query required to create inject.")
        output = await self.return_output(
            history=history,
            query=query,
            query_format="oneline",
            query_subtitle="Narrator",
        )
        return output
