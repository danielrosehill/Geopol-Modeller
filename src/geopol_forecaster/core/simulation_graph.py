#!/usr/bin/env python3

#   Licensed under the Apache License, Version 2.0

"""LangGraph-based simulation loop for Geopol Forecaster simulations.

Replaces the imperative for-loop with an inspectable, pausable state graph.
"""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END


class SimState(TypedDict):
    # Scenario context
    scenario: str
    briefing: str
    title: str
    timestep: str
    nature: float
    mode: list

    # Player configs: [{name, persona, model_id}]
    player_configs: list

    # Turn tracking
    moves_total: int
    move_current: int
    current_player_idx: int

    # History: [{name, text}]
    history: list
    current_responses: list

    # Assessment
    questions: list
    mc_questions: list
    assessments: list

    # Escalation tracking (from graph config)
    escalation_history: list  # [{move, level, direction}]

    # Runtime references (callables injected at build time)
    # These are set during graph construction, not serialized
    _player_respond: object
    _adjudicate: object
    _assess: object
    _verbosity: int
    _progress: object      # SimulationProgress or NullProgress
    _checkpoint: object    # bool — save checkpoints after each move
    _resuming: object      # bool — skip setup when resuming from checkpoint


async def setup_node(state: SimState) -> dict:
    """Initialize history with scenario + briefing."""
    # When resuming from a checkpoint, skip initialization — state is already loaded
    if state.get("_resuming"):
        return {"_resuming": False}

    history = [{"name": "Narrator", "text": state["scenario"]}]
    if state.get("briefing"):
        history.append({"name": "Briefing", "text": state["briefing"]})

    progress = state.get("_progress")
    if progress:
        progress.start_phase("SIMULATION")
        title = state.get("title", "Simulation")
        progress.start_move(1)
    elif state.get("_verbosity", 0) >= 1:
        print()
        title = state.get("title", "Simulation")
        print("+-" + "-" * len(title) + "-+")
        print("| " + title + " |")
        print("+-" + "-" * len(title) + "-+")
        print()
        print(state["scenario"])

    return {
        "history": history,
        "move_current": 0,
        "current_player_idx": 0,
        "current_responses": [],
        "assessments": [],
        "escalation_history": [],
    }


async def player_respond_node(state: SimState) -> dict:
    """Get response from the current player."""
    idx = state["current_player_idx"]
    player_config = state["player_configs"][idx]
    respond_fn = state["_player_respond"]

    progress = state.get("_progress")
    if progress:
        progress.start_player(player_config["name"])
    elif state.get("_verbosity", 0) >= 1:
        print(f"\n### {player_config['name']}\n")

    response_text = await respond_fn(
        player_config=player_config,
        history=state["history"],
        timestep=state.get("timestep"),
        move_current=state.get("move_current"),
        moves_total=state.get("moves_total"),
    )

    new_responses = state["current_responses"] + [
        {"name": player_config["name"], "text": response_text}
    ]

    return {
        "current_responses": new_responses,
        "current_player_idx": idx + 1,
    }


async def adjudicate_node(state: SimState) -> dict:
    """Narrator weaves player responses into outcome."""
    adjudicate_fn = state["_adjudicate"]

    progress = state.get("_progress")
    if progress:
        progress.start_adjudication()
    elif state.get("_verbosity", 0) >= 1:
        print("\n### Result\n")

    outcome = await adjudicate_fn(
        history=state["history"],
        responses=state["current_responses"],
        nature=state["nature"],
        timestep=state["timestep"],
        mode=state["mode"],
    )

    # Build new history entry label
    move_num = state["move_current"] + 1
    ts = state["timestep"].title() if state["timestep"] else ""
    label = f"{ts} {move_num}" if ts else f"Round {move_num}"

    new_history = state["history"] + [{"name": label, "text": outcome}]

    result = {
        "history": new_history,
        "move_current": state["move_current"] + 1,
        "current_player_idx": 0,
        "current_responses": [],
    }

    # Checkpoint after each completed move
    if state.get("_checkpoint"):
        from ..output.checkpoint import save_checkpoint
        merged = {**state, **result}
        path = save_checkpoint(merged)
        if progress:
            progress.checkpoint_saved(path)
        elif state.get("_verbosity", 0) >= 1:
            print(f"  [checkpoint saved: {path}]")

    # Announce next move if there is one
    next_move = state["move_current"] + 2  # +1 for 0-index, +1 for next
    if progress and next_move <= state["moves_total"]:
        progress.start_move(next_move)

    return result


async def assess_node(state: SimState) -> dict:
    """Run assessment questions."""
    assess_fn = state["_assess"]
    assessments = []

    progress = state.get("_progress")
    if progress:
        progress.start_phase("ASSESSMENT")

    for question in state.get("questions", []):
        if progress:
            progress.start_assessment(question)
        elif state.get("_verbosity", 0) >= 1:
            print(f"\n--- {question}\n")
        result = await assess_fn(history=state["history"], query=question)
        assessments.append({"question": question, "answer": result})

    for question, mc in state.get("mc_questions", []):
        if progress:
            progress.start_assessment(question)
        elif state.get("_verbosity", 0) >= 1:
            print(f"\n--- {question}\n")
        result = await assess_fn(history=state["history"], query=question, mc=mc)
        assessments.append({"question": question, "answer": result, "options": mc})

    return {"assessments": assessments}


def should_continue_players(state: SimState) -> str:
    """Route: more players to respond, or adjudicate."""
    if state["current_player_idx"] < len(state["player_configs"]):
        return "player_respond"
    return "adjudicate"


def should_continue_moves(state: SimState) -> str:
    """Route: more moves, or assess."""
    if state["move_current"] < state["moves_total"]:
        return "next_turn"
    return "assess"


def build_simulation_graph():
    """Construct the simulation StateGraph."""
    graph = StateGraph(SimState)

    graph.add_node("setup", setup_node)
    graph.add_node("player_respond", player_respond_node)
    graph.add_node("adjudicate", adjudicate_node)
    graph.add_node("assess", assess_node)

    graph.set_entry_point("setup")

    # setup -> check if players to respond
    graph.add_conditional_edges("setup", should_continue_players, {
        "player_respond": "player_respond",
        "adjudicate": "adjudicate",
    })

    # after player responds -> check if more players
    graph.add_conditional_edges("player_respond", should_continue_players, {
        "player_respond": "player_respond",
        "adjudicate": "adjudicate",
    })

    # after adjudication -> check if more moves
    graph.add_conditional_edges("adjudicate", should_continue_moves, {
        "next_turn": "player_respond",
        "assess": "assess",
    })

    # assess -> end
    graph.add_edge("assess", END)

    return graph.compile()
