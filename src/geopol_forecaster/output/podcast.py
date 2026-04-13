#!/usr/bin/env python3

"""Edge-TTS podcast episode generation for Geopol Forecaster simulations."""

import os
import datetime
import re

import edge_tts


PODCAST_SYSTEM_PROMPT = """\
You are a podcast host narrating a geopolitical wargame simulation.

Convert the following simulation transcript into an engaging podcast episode script.
Write in first person as a narrator. Include:
- A brief introduction setting the scene
- Narration of each move's events in dramatic but factual style
- Commentary on key decisions and turning points
- A conclusion summarizing outcomes and lessons learned

Keep it natural and conversational. Do not use stage directions, sound effect cues,
or formatting markup. Output only the narration text — no headers or metadata.

Keep the narration under 3000 words to stay within a comfortable listening length.
"""


async def generate_podcast(state, llm_client, model, voice="en-US-GuyNeural",
                           output_dir=None, verbosity=1):
    """Generate a podcast MP3 from the completed simulation state.

    Phase 1: Use the LLM to rewrite the simulation transcript into a
    natural podcast narration script.
    Phase 2: Use edge-tts to synthesize the script to MP3.

    Returns the path to the generated MP3 file.
    """
    if output_dir is None:
        output_dir = ".geopol_data/podcasts"

    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = _slugify(state.get("title", "simulation"))

    # Phase 1: LLM rewrites history into podcast script
    if verbosity >= 1:
        print("\n[Podcast] Generating narration script...")

    transcript = _build_transcript(state)
    messages = [
        {"role": "system", "content": PODCAST_SYSTEM_PROMPT},
        {"role": "user", "content": transcript},
    ]
    script = await llm_client.complete(
        model=model, messages=messages, max_tokens=4096, temperature=0.6
    )
    script = script.strip()

    # Save script for reference
    script_path = os.path.join(output_dir, f"{title_slug}_{ts}_script.txt")
    with open(script_path, "w") as f:
        f.write(script)

    if verbosity >= 1:
        print(f"[Podcast] Script saved ({len(script)} chars): {script_path}")

    # Phase 2: edge-tts synthesis
    if verbosity >= 1:
        print(f"[Podcast] Synthesizing audio with voice '{voice}'...")

    mp3_path = os.path.join(output_dir, f"{title_slug}_{ts}.mp3")
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(mp3_path)

    if verbosity >= 1:
        print(f"[Podcast] Audio saved: {mp3_path}")

    return mp3_path


def _build_transcript(state):
    """Build a plain-text transcript from SimState for the LLM to rewrite."""
    parts = []

    title = state.get("title", "Untitled Simulation")
    parts.append(f"SIMULATION TITLE: {title}")
    parts.append(f"\nSCENARIO:\n{state.get('scenario', '')}")

    briefing = state.get("briefing", "")
    if briefing:
        parts.append(f"\nINTELLIGENCE BRIEFING:\n{briefing}")

    parts.append("\n--- SIMULATION MOVES ---")

    history = state.get("history", [])
    for entry in history:
        name = entry.get("name", "")
        text = entry.get("text", "")
        if name in ("Narrator", "Briefing"):
            continue
        parts.append(f"\n[{name}]\n{text}")

    assessments = state.get("assessments", [])
    if assessments:
        parts.append("\n--- FINAL ASSESSMENTS ---")
        for a in assessments:
            parts.append(f"\nQ: {a.get('question', '')}")
            parts.append(f"A: {a.get('answer', '')}")
            if a.get("options"):
                parts.append(f"Options were: {', '.join(a['options'])}")

    return "\n".join(parts)


def _slugify(text):
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:30].strip("_")
