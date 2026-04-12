#!/usr/bin/env python3

"""Typst PDF report generation for snowglobe simulations."""

import os
import subprocess
import datetime
import re


def generate_report(state, output_dir=None):
    """Generate a Typst PDF report from the completed simulation state.

    Writes a .typ source file, compiles it with `typst compile`, and
    returns the path to the generated PDF.
    """
    if output_dir is None:
        output_dir = ".snowglobe_data/reports"

    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = _slugify(state.get("title", "simulation"))
    typ_path = os.path.join(output_dir, f"{title_slug}_{ts}.typ")
    pdf_path = typ_path.replace(".typ", ".pdf")

    typ_content = _build_typst_document(state)

    with open(typ_path, "w") as f:
        f.write(typ_content)

    subprocess.run(
        ["typst", "compile", typ_path, pdf_path],
        check=True,
        capture_output=True,
    )

    return pdf_path


def _build_typst_document(state):
    """Build the Typst markup string from simulation state."""
    title = state.get("title", "Simulation")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    sections = []

    # Document setup
    sections.append(f'#set document(title: "{_esc(title)}")')
    sections.append('#set text(font: "IBM Plex Sans", size: 11pt)')
    sections.append("#set page(margin: 2cm)")
    sections.append('#set heading(numbering: "1.")')
    sections.append("")

    # Title block
    sections.append(f"= {_esc(title)}")
    sections.append(f"#text(gray)[Generated {now} by Snowglobe]")
    sections.append("")

    # Scenario
    sections.append("== Scenario")
    sections.append("")
    sections.append(_esc(state.get("scenario", "")))
    sections.append("")

    # Briefing
    briefing = state.get("briefing", "")
    if briefing:
        sections.append("== Intelligence Briefing")
        sections.append("")
        sections.append(_esc(briefing))
        sections.append("")

    # Simulation narrative
    sections.append("== Simulation Narrative")
    sections.append("")

    history = state.get("history", [])
    for entry in history:
        name = entry.get("name", "")
        text = entry.get("text", "")
        # Skip entries already covered in scenario/briefing sections
        if name in ("Narrator", "Briefing"):
            continue
        sections.append(f"=== {_esc(name)}")
        sections.append("")
        sections.append(_esc(text))
        sections.append("")

    # Assessments
    assessments = state.get("assessments", [])
    if assessments:
        sections.append("== Assessments")
        sections.append("")
        for a in assessments:
            question = a.get("question", "")
            answer = a.get("answer", "")
            options = a.get("options")
            sections.append(f"*Q: {_esc(question)}*")
            sections.append("")
            if options:
                sections.append(
                    f"Options: {', '.join(_esc(o) for o in options)}"
                )
                sections.append("")
            sections.append(f"*A: {_esc(answer)}*")
            sections.append("")

    # Configuration summary
    sections.append("== Configuration")
    sections.append("")
    config_items = [
        ("Moves", str(state.get("moves_total", "?"))),
        ("Timestep", state.get("timestep", "?")),
        ("Mode", ", ".join(state.get("mode", []))),
    ]
    players = state.get("player_configs", [])
    for p in players:
        config_items.append((p.get("name", "Player"), p.get("model_id", "?")))

    sections.append("#table(")
    sections.append('  columns: (auto, auto),')
    sections.append('  stroke: 0.5pt + gray,')
    sections.append('  inset: 8pt,')
    for key, val in config_items:
        sections.append(f'  [{_esc(key)}], [{_esc(val)}],')
    sections.append(")")
    sections.append("")

    return "\n".join(sections)


def _esc(text):
    """Escape Typst special characters in user/LLM-generated text."""
    if not isinstance(text, str):
        text = str(text)
    # Order matters: backslash first to avoid double-escaping
    for char in ["\\", "#", "*", "_", "@", "$", "<", ">", "~", "`"]:
        text = text.replace(char, "\\" + char)
    return text


def _slugify(text):
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:30].strip("_")
