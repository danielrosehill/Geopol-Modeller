#!/usr/bin/env python3

"""Checkpointing for snowglobe simulations — save/resume mid-run state."""

import json
import os
import datetime
import re

CHECKPOINT_DIR = ".snowglobe_data/checkpoints"

# SimState fields that are runtime callables/objects and can't be serialized
EXCLUDED_FIELDS = {
    "_player_respond", "_adjudicate", "_assess", "_progress",
    "_verbosity", "_checkpoint", "_resuming",
}


def save_checkpoint(state, checkpoint_dir=None):
    """Save the serializable subset of SimState to a JSON file.

    Returns the path of the written checkpoint file.
    """
    if checkpoint_dir is None:
        checkpoint_dir = CHECKPOINT_DIR

    serializable = {k: v for k, v in state.items() if k not in EXCLUDED_FIELDS}

    os.makedirs(checkpoint_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = _slugify(state.get("title", "sim"))
    move = state.get("move_current", 0)
    filename = f"{title_slug}_move{move}_{ts}.json"
    path = os.path.join(checkpoint_dir, filename)

    with open(path, "w") as f:
        json.dump(serializable, f, indent=2, default=str)

    return path


def load_checkpoint(path):
    """Load a checkpoint JSON file and return the partial SimState dict."""
    with open(path, "r") as f:
        return json.load(f)


def find_latest_checkpoint(checkpoint_dir=None, title=None):
    """Find the most recent checkpoint file, optionally filtered by title slug.

    Returns the file path, or None if no checkpoints exist.
    """
    if checkpoint_dir is None:
        checkpoint_dir = CHECKPOINT_DIR

    if not os.path.isdir(checkpoint_dir):
        return None

    candidates = sorted(
        [f for f in os.listdir(checkpoint_dir) if f.endswith(".json")],
        reverse=True,
    )

    if title:
        slug = _slugify(title)
        candidates = [f for f in candidates if f.startswith(slug)]

    if not candidates:
        return None

    return os.path.join(checkpoint_dir, candidates[0])


def _slugify(text):
    """Convert title to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:30].strip("_")
