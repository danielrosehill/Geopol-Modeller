#!/usr/bin/env python3

"""Scenario subgraph configuration loader.

Loads per-scenario graph configs from config/graphs/<name>.yaml that
inject domain-specific behavior into the core simulation loop:
information asymmetry, exogenous shocks, escalation tracking, and
adaptive tempo.
"""

import os
import random

from ruamel.yaml import YAML


class GraphConfig:
    """Parsed scenario subgraph configuration."""

    def __init__(self, data=None):
        self.data = data or {}
        self.name = self.data.get("name", "default")

        # Visibility / information asymmetry
        vis = self.data.get("visibility", {})
        self._blocs = vis.get("blocs", {})
        self._actor_to_bloc = {}
        for bloc_name, actor_ids in self._blocs.items():
            for actor_id in actor_ids:
                self._actor_to_bloc[actor_id] = bloc_name

        # Shocks
        self._shocks = self.data.get("shocks", [])

        # Escalation scale
        esc = self.data.get("escalation_scale", {})
        self._escalation_levels = esc.get("levels", {})
        self._track_escalation = esc.get("tracking", {}).get("output_per_round", False)

        # Adaptive tempo
        tempo = self.data.get("adaptive_tempo", {})
        self._adaptive_tempo_enabled = tempo.get("enabled", False)
        self._tempo_rules = tempo.get("rules", [])

    @property
    def has_visibility_rules(self):
        return bool(self._blocs)

    @property
    def has_shocks(self):
        return bool(self._shocks)

    @property
    def has_escalation_tracking(self):
        return self._track_escalation

    @property
    def has_adaptive_tempo(self):
        return self._adaptive_tempo_enabled

    def get_bloc_for_actor(self, actor_id):
        """Return the bloc name for an actor, or None if not assigned."""
        return self._actor_to_bloc.get(actor_id)

    def get_bloc_members(self, bloc_name):
        """Return actor IDs in a bloc."""
        return self._blocs.get(bloc_name, [])

    def filter_history_for_actor(self, history_entries, actor_id, actor_id_map=None):
        """Filter history entries based on visibility rules.

        Each actor sees:
        - All entries from 'Narrator', 'Briefing', or adjudicated rounds (public)
        - Their own prior responses
        - Responses from actors in the same bloc

        Args:
            history_entries: list of {name, text} dicts
            actor_id: the actor's ID (from actor definition)
            actor_id_map: dict mapping display names to actor IDs

        Returns:
            Filtered list of {name, text} dicts.
        """
        if not self.has_visibility_rules:
            return history_entries

        if actor_id_map is None:
            actor_id_map = {}

        actor_bloc = self.get_bloc_for_actor(actor_id)
        if actor_bloc is None:
            # Actor not in any bloc — sees everything (e.g., mediators)
            return history_entries

        bloc_members = set(self.get_bloc_members(actor_bloc))

        filtered = []
        for entry in history_entries:
            name = entry["name"]

            # Public entries: Narrator, Briefing, adjudicated round labels
            if name in ("Narrator", "Briefing") or name.startswith((
                "+", "Round ", "Short ", "Medium ", "Long ", "Daily ",
            )):
                filtered.append(entry)
                continue

            # Own responses
            entry_actor_id = actor_id_map.get(name)
            if entry_actor_id == actor_id:
                filtered.append(entry)
                continue

            # Same-bloc responses
            if entry_actor_id and entry_actor_id in bloc_members:
                filtered.append(entry)
                continue

            # Everything else is hidden from this actor

        return filtered

    def select_shock(self):
        """Select an exogenous shock based on weighted probabilities.

        Returns:
            A shock dict {id, type, trigger, consequences} or None.
        """
        if not self.has_shocks:
            return None

        weights = [s.get("weight", 0.1) for s in self._shocks]
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for shock, weight in zip(self._shocks, weights):
            cumulative += weight
            if r <= cumulative:
                return shock
        return self._shocks[-1]  # fallback

    def get_escalation_prompt_suffix(self):
        """Return the prompt suffix that requests structured escalation output."""
        if not self.has_escalation_tracking:
            return ""

        levels_str = "\n".join(
            f"  {k}: {v}" for k, v in sorted(self._escalation_levels.items())
        )
        return (
            "\n\nAfter your narrative, on a new line output EXACTLY this format:\n"
            "ESCALATION_LEVEL: <number 0-9>\n"
            "ESCALATION_DIRECTION: <escalating|stable|de-escalating>\n\n"
            f"Use this scale:\n{levels_str}"
        )

    def get_adaptive_timestep(self, escalation_level):
        """Return the timestep to use based on current escalation level.

        Args:
            escalation_level: int 0-9

        Returns:
            Timestep string or None if no adaptive rule matches.
        """
        if not self.has_adaptive_tempo or escalation_level is None:
            return None

        for rule in self._tempo_rules:
            if "escalation_above" in rule:
                if escalation_level > rule["escalation_above"]:
                    return rule["timestep"]
            elif "escalation_between" in rule:
                low, high = rule["escalation_between"]
                if low <= escalation_level <= high:
                    return rule["timestep"]
            elif "escalation_below" in rule:
                if escalation_level < rule["escalation_below"]:
                    return rule["timestep"]

        return None

    @property
    def escalation_levels(self):
        return self._escalation_levels


def load_graph_config(scenario_data, config_dir):
    """Load graph config for a scenario, if one exists.

    Looks for a graph config matching the scenario's actor_cluster name
    or an explicit `graph_config` field in the scenario YAML.

    Returns:
        GraphConfig instance (empty/default if no config file found).
    """
    # Explicit reference in scenario
    graph_name = scenario_data.get("graph_config")

    # Fall back to actor_cluster name
    if graph_name is None:
        graph_name = scenario_data.get("actor_cluster")

    if graph_name is None:
        return GraphConfig()

    graph_path = os.path.join(config_dir, "graphs", f"{graph_name}.yaml")
    if not os.path.exists(graph_path):
        # No graph config — use defaults
        return GraphConfig()

    yaml = YAML(typ="safe")
    with open(graph_path, "r") as f:
        data = yaml.load(f)

    return GraphConfig(data)


def parse_escalation_from_output(text):
    """Extract structured escalation data from adjudication output.

    Looks for lines matching:
        ESCALATION_LEVEL: <int>
        ESCALATION_DIRECTION: <string>

    Returns:
        (level: int or None, direction: str or None, clean_text: str)
        where clean_text has the escalation lines removed.
    """
    import re

    level = None
    direction = None
    clean_lines = []

    for line in text.split("\n"):
        level_match = re.match(r"ESCALATION_LEVEL:\s*(\d+)", line.strip())
        dir_match = re.match(r"ESCALATION_DIRECTION:\s*(\w+)", line.strip())

        if level_match:
            level = int(level_match.group(1))
        elif dir_match:
            direction = dir_match.group(1).lower()
        else:
            clean_lines.append(line)

    clean_text = "\n".join(clean_lines).strip()
    return level, direction, clean_text
