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

import random
import time

from .history import History


class Intelligent:
    def __init__(self, database, verbosity, kind, ioid=None, name='', iodict=None, logger=None, **kwargs):
        self.db = database
        self.verbosity = verbosity
        self.logger = logger
        self.active = True
        self.kind = kind
        if ioid is not None:
            self.ioid = str(ioid)
        else:
            self.ioid = str(random.randint(100000, 999999))
        self.name = name
        self.iodict = iodict
        self.setup(self.kind)

    def setup(self, kind):
        if kind == "ai":
            pass
        elif kind == "human":
            self.interface_setup()
        elif kind == "preset":
            self.preset_setup()

    async def return_output(
        self, kind=None, bind=None, template=None, variables=None, **kwargs
    ):
        if kind is None:
            kind = self.kind

        if template is None and variables is None:
            template, variables = await self.return_template(**kwargs)

        if kind == "ai":
            output = await self.return_from_ai(template, variables, bind=bind)
        elif kind == "human":
            output = await self.return_from_human(template, variables)
        elif kind == "preset":
            output = await self.return_from_preset()
        return output

    async def return_template(
        self,
        name=None,
        persona=None,
        reminder=None,
        history=None,
        history_over=None,
        history_merged=None,
        responses=None,
        responses_intro=None,
        query=None,
        query_format=None,
        query_subtitle=None,
    ):
        if persona is not None:
            if persona[-1:] == ".":
                persona = persona[:-1]

        template = ""
        variables = {}
        if persona is not None:
            template += "### You are {persona}.\n\n"
            variables["persona"] = persona
        if history is not None:
            if not history_over:
                history_intro = "This is what has happened so far"
            else:
                history_intro = "This is what happened"
            template += "### " + history_intro + ":\n\n{history}\n\n"
            if isinstance(history, str):
                variables["history"] = history
            elif not history_merged:
                variables["history"] = await history.str(name=name)
            else:
                variables["history"] = await history.textonly()
        if responses is not None:
            template += "### " + responses_intro + ":\n\n{responses}\n\n"
            variables["responses"] = await responses.str(name=name)
        if query_format is None or query_format == "twoline":
            template += "### Question:\n\n{query}"
            if reminder == 2 and persona is not None:
                template += " (Remember, you are {persona}.)"
            elif reminder == 1 and name is not None:
                template += " (Remember, you are {name}.)"
                variables["name"] = name
            template += "\n\n### Answer:\n\n"
        elif query_format == "oneline":
            template += "### {query}:\n\n"
        elif query_format == "twoline_simple":
            template += "Question: {query}\n\nAnswer: "
        elif query_format == "oneline_simple":
            template += "{query}"
        variables["query"] = query
        if query_subtitle is not None:
            template += "{subtitle}:\n\n"
            variables["subtitle"] = query_subtitle
        return template, variables

    async def return_from_ai(self, template, variables, max_tries=64, bind=None):
        content = template.format(**variables)
        messages = [{"role": "user", "content": content}]
        stop = bind.get("stop") if bind else None

        if self.verbosity >= 4:
            print("v" * 80)
            print(content)
            print("^" * 80)

        for i in range(max_tries):
            if self.verbosity >= 1:
                output = ""
                async for chunk in self.llm_client.complete_stream(
                    model=self.model_id, messages=messages, stop=stop
                ):
                    print(chunk, end="", flush=True)
                    output += chunk
                output = output.strip()
            else:
                output = await self.llm_client.complete(
                    model=self.model_id, messages=messages, stop=stop
                )
                output = output.strip()

            if len(output) > 0:
                break

        if self.verbosity >= 1:
            print()
        return output

    async def return_from_human(self, template, variables):
        chatroom = self.db.default_chatroom(self.ioid)
        content = template.format(**variables)
        self.interface_send_message(chatroom, content)
        answer = await self.interface_get_message(chatroom)
        return answer

    async def return_from_preset(self):
        self.preset_idx += 1
        return self.presets[self.preset_idx - 1]

    def preset_setup(self):
        self.preset_idx = 0

    def interface_setup(self):
        if self.verbosity >= 2:
            print("ID %s : %s" % (self.ioid, self.name))
        self.db.add_player(self.ioid, self.name)
        if self.iodict is not None:
            for resource_type in [
                "chatrooms",
                "weblinks",
                "infodocs",
                "notepads",
                "editdocs",
            ]:
                if resource_type in self.iodict:
                    for resource in self.iodict[resource_type]:
                        self.db.add_resource(resource, resource_type[:-1])
                        self.db.assign(self.ioid, resource)
        self.db.commit()

    def interface_send_message(self, chatroom, content, fmt=None, cc=None):
        if fmt is None:
            fmt = "markdown"
        avatar = "ai.png" if self.kind == "ai" else "human.png"
        message = {
            "content": content,
            "format": fmt,
            "name": self.name,
            "stamp": time.ctime(),
            "avatar": avatar,
        }
        if cc is None:
            destinations = [chatroom]
        elif isinstance(cc, str):
            destinations = [chatroom, cc]
        else:
            destinations = [chatroom].append(cc)
        for destination in destinations:
            self.db.send_message(destination, **message)
        self.db.commit()

    async def interface_get_message(self, chatroom):
        while True:
            log = self.db.get_chatlog(chatroom)
            if len(log) > 0 and log[-1]["name"] == self.name:
                answer = log[-1]["content"]
                return answer
            await self.db.wait()

    async def multiple_choice(self, query, answer, mc):
        mc_parts = ["'" + x + "'," for x in mc]
        if len(mc_parts) == 2:
            mc_parts[0] = mc_parts[0][:-1]
        mc_parts[-1] = "or " + mc_parts[-1][:-1]
        mc_string = " ".join(mc_parts)
        template = "Question: {query}\n\nAnswer: {answer}\n\nQuestion: Which multiple choice response best summarizes the previous answer?: {mc_string}.\n\nAnswer: "
        variables = {"query": query, "answer": answer, "mc_string": mc_string}
        bind = {"stop": ["\n\n"]}
        output = await self.return_output(
            bind=bind, template=template, variables=variables
        )
        output = output.strip().strip('"' + "'" + ".,;").lower()
        mc_ref = [x.lower() for x in mc]
        if output in mc_ref:
            output = mc[mc_ref.index(output)]
        else:
            search_flags = [x in output for x in mc_ref]
            if sum(search_flags) == 1:
                output = mc[search_flags.index(True)]
            else:
                output = ""
        return output

    async def chat_response(
        self, chatlog, name="Assistant", persona=None, history=None, participants=None
    ):
        chat_intro = "This is a conversation about what happened"
        if participants is None:
            participants = set([entry["name"] for entry in chatlog.entries])
            participants.add(name)
            participants.add("Narrator")
        bind = {"stop": [p + ":" for p in participants]}
        output = await self.return_output(
            bind=bind,
            persona=persona,
            history=history,
            history_over=True,
            responses=chatlog,
            responses_intro=chat_intro,
            query=name + ":\n\n",
            query_format="oneline_simple",
        )
        return output

    async def chat_terminal(self, name="Assistant", persona=None, history=None):
        chatlog = History()
        nb = 2
        username = "User"
        if self.verbosity >= 2:
            instructions = "Chat | Press Enter twice after each message or to exit."
            print()
            print("-" * len(instructions))
            print(instructions)
            print("-" * len(instructions))
        while True:
            usertext = ""
            while True:
                userline = input()
                usertext += userline + "\n"
                if len(usertext) >= nb and usertext[-nb:] == "\n" * nb:
                    break
            if len(usertext) == nb and usertext[-nb:] == "\n" * nb:
                break
            usertext = usertext.strip()
            chatlog.add(username, usertext)
            output = await self.chat_response(
                chatlog,
                name=name,
                persona=persona,
                history=history,
                participants=[username, name, "Narrator"],
            )
            print()
            chatlog.add(name, output)

    async def chat_session(self, chatroom, history=None):
        while self.active:
            log = self.db.get_chatlog(chatroom)
            if len(log) > 0 and log[-1]["name"] != self.name:
                chatlog = History()
                for logitem in log:
                    chatlog.add(logitem["name"], logitem["content"])
                output = await self.chat_response(
                    chatlog, name=self.name, persona=self.persona, history=history
                )
                self.interface_send_message(chatroom, output)
            await self.db.wait()
