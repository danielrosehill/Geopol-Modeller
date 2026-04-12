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

import os
import yaml
from dataclasses import dataclass

import openai


@dataclass
class ModelPool:
    planner: str
    narrator: str
    player: str
    advisor: str


def read_yaml(path):
    if os.path.exists(path):
        with open(path, "r") as obj:
            content = yaml.safe_load(obj)
        if content is None:
            content = {}
    else:
        content = {}
    return content


def load_pools(path):
    data = read_yaml(path)
    pools = {}
    for name, models in data.get("pools", {}).items():
        pools[name] = ModelPool(
            planner=models["planner"],
            narrator=models["narrator"],
            player=models["player"],
            advisor=models["advisor"],
        )
    active = data.get("active_pool", "deepseek")
    base_url = data.get("api", {}).get("base_url", "https://openrouter.ai/api/v1")
    return pools, active, base_url


class LLMClient:
    """Thin async wrapper around OpenAI SDK pointed at OpenRouter."""

    def __init__(self, api_key=None, base_url="https://openrouter.ai/api/v1"):
        if api_key is None:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def complete(
        self,
        model,
        messages,
        temperature=0.7,
        max_tokens=2048,
        stop=None,
    ):
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
        )
        return response.choices[0].message.content or ""

    async def complete_stream(
        self,
        model,
        messages,
        temperature=0.7,
        max_tokens=2048,
        stop=None,
    ):
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
