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
from ruamel.yaml import YAML
from .llm import load_pools, ModelPool


class Configuration:
    def __init__(self, config_path="/config/game.yaml", pools_path=None):
        self.config_path = config_path
        self.data_dir = '/data/snowglobe/'
        self.game_id_file = '/data/snowglobe/game.id'

        with open(config_path, "r") as cfg_file:
            yaml = YAML(typ="safe")
            file_config = yaml.load(cfg_file)

        if file_config:
            self.data_dir = file_config.get('data_directory', self.data_dir)
            self.game_id_file = file_config.get('game_id_file', self.game_id_file)
            self.goals = file_config['goals']
            self.title = file_config['title']
            self.scenario = file_config['scenario']
            self.infodocs = dict()
            if 'infodocs' in file_config:
                for doc in file_config['infodocs']:
                    infodoc = file_config['infodocs'][doc]
                    self.infodocs[doc] = {
                        'title': doc,
                        'format': infodoc['format'],
                        'content': infodoc['content'],
                    }
            self.moves = file_config['moves']
            self.timestep = file_config['timestep']
            self.nature = file_config['nature']
            self.mode = file_config['mode']
            self.players = dict()
            self.advisors = dict()

            for player in file_config.get('players', {}):
                self.players[player] = file_config['players'][player]

            for advisor in file_config.get('advisors', {}):
                self.advisors[advisor] = file_config['advisors'][advisor]

        # Load model pools
        if pools_path is None:
            pools_path = os.path.join(os.path.dirname(config_path), "pools.yaml")
        if os.path.exists(pools_path):
            self.pools, self.active_pool_name, self.base_url = load_pools(pools_path)
        else:
            self.pools = {}
            self.active_pool_name = None
            self.base_url = "https://openrouter.ai/api/v1"

        # Allow game YAML to override active pool
        if file_config and 'pool' in file_config:
            self.active_pool_name = file_config['pool']

    @property
    def pool(self):
        if self.active_pool_name and self.active_pool_name in self.pools:
            return self.pools[self.active_pool_name]
        return ModelPool(
            planner="deepseek/deepseek-v3.2",
            narrator="deepseek/deepseek-v3.2",
            player="deepseek/deepseek-v3.2",
            advisor="deepseek/deepseek-v3.2",
        )
