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


import asyncio
import inspect


async def gather_plus(*args):
    items = list(args)
    awaitables = [(i, x) for i, x in enumerate(items) if inspect.isawaitable(x)]
    if not awaitables:
        return items
    results = await asyncio.gather(*[x for _, x in awaitables])
    for (i, _), result in zip(awaitables, results):
        items[i] = result
    return items


class History:
    def __init__(self):
        self.entries = []

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        history_part = History()
        if isinstance(index, slice):
            history_part.entries = self.entries[index]
        elif isinstance(index, int):
            history_part.entries = [self.entries[index]]
        return history_part

    def add(self, name, text):
        self.entries.append({"name": name, "text": text})

    async def concrete(self):
        texts = [entry["text"] for entry in self.entries]
        texts = await gather_plus(*texts)
        for i in range(len(texts)):
            self.entries[i]["text"] = texts[i]

    async def str(self, name=None):
        await self.concrete()
        return "\n\n".join(
            [
                ("You" if entry["name"] == name else entry["name"])
                + ":\n\n"
                + entry["text"]
                for entry in self.entries
            ]
        )

    async def textonly(self):
        await self.concrete()
        return "\n\n".join([entry["text"] for entry in self.entries])

    def clear(self):
        self.entries = []

    def copy(self):
        history_copy = History()
        history_copy.entries = self.entries.copy()
        return history_copy
