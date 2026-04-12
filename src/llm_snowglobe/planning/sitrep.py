#!/usr/bin/env python3

"""SITREP generation agent — produces a structured situational report before simulation.

Uses Tavily for current-events research and trafilatura for reference URL
ingestion. Outputs a military-style SITREP with precise UTC timestamp that
becomes the world-state context for all simulation actors.
"""

import os
import datetime

from ..core.llm import LLMClient
from ..tools.rag import fetch_urls


SITREP_SYSTEM_PROMPT = """\
You are an intelligence analyst producing a SITUATIONAL REPORT (SITREP) to
establish the world state for a geopolitical simulation exercise.

Your SITREP must follow this exact structure:

---

## SITREP — {title}

**DTG:** {dtg}
**Classification:** EXERCISE — SIMULATION USE ONLY
**Prepared by:** Automated Intelligence Fusion Cell

### 1. SITUATION
Current state of affairs as of the DTG. What is happening right now. Be precise
and factual. Cite sources where possible.

### 2. BACKGROUND
Historical context that led to the current situation. Key events, treaties,
prior escalations, and structural factors.

### 3. KEY DEVELOPMENTS
The most recent significant events, listed in reverse chronological order.
Each entry should include a date/time (if known) and source attribution.
Format as a numbered list.

### 4. FORCE DISPOSITION
Known military, political, and economic positions of each relevant actor.
Include deployments, mobilisations, sanctions, diplomatic postures.
Organise by actor.

### 5. ASSESSMENT
Your analytical assessment of the trajectory. What is most likely to happen
in the near term? What are the key decision points? Where are the escalation
and de-escalation pathways?

### 6. IMPLICATIONS FOR SIMULATION ACTORS
For each actor listed below, a brief paragraph on what this situation means
for their decision-making and what pressures or opportunities they face.

Actors: {actor_names}

### 7. SOURCES
List all URLs, search queries, and reference documents used to compile this
SITREP. Format as a bulleted list.

---

RULES:
- Be factual. Label uncertainty explicitly ("assessed", "likely", "unconfirmed").
- Do NOT speculate about what actors will do — that is for the simulation.
- Use the reference material and web research provided. Do not invent facts.
- Write in a concise, professional intelligence style.
- The DTG and actor list are provided — use them exactly as given.
"""


class SitrepAgent:
    """Generates a structured SITREP before simulation begins."""

    def __init__(self, llm_client, model, tavily_api_key=None,
                 verbosity=1, progress=None):
        self.llm_client = llm_client
        self.model = model
        self.verbosity = verbosity
        self.progress = progress
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")

    async def research(self, scenario, title=None, num_queries=5):
        """Use Tavily to search for current-events context."""
        if not self.tavily_api_key:
            if self.progress:
                self.progress.update("No TAVILY_API_KEY — skipping web research")
            elif self.verbosity >= 1:
                print("[SITREP] No TAVILY_API_KEY — skipping web research")
            return "", []

        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            if self.progress:
                self.progress.update("tavily-python not installed — skipping web research")
            elif self.verbosity >= 1:
                print("[SITREP] tavily-python not installed — skipping web research")
            return "", []

        client = AsyncTavilyClient(api_key=self.tavily_api_key)

        # Generate search queries from the scenario
        query_prompt = (
            f"You are preparing a SITREP for a geopolitical simulation.\n"
            f"Given this scenario, generate {num_queries} concise web search queries "
            f"to find the latest real-world developments, military postures, "
            f"diplomatic statements, and background context.\n"
            f"Return only the queries, one per line.\n\n"
            f"Title: {title or 'Untitled'}\n\n"
            f"Scenario:\n{scenario[:3000]}"
        )
        query_response = await self.llm_client.complete(
            model=self.model,
            messages=[{"role": "user", "content": query_prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        queries = [
            q.strip().strip("-•*0123456789.)")
            for q in query_response.strip().split("\n")
            if q.strip()
        ]
        queries = queries[:num_queries]

        if self.verbosity >= 2:
            print(f"[SITREP] Search queries: {queries}")

        # Run searches
        results = []
        sources = []
        for query in queries:
            try:
                response = await client.search(query, max_results=3)
                for result in response.get("results", []):
                    title_r = result.get("title", "")
                    content = result.get("content", "")
                    url = result.get("url", "")
                    results.append(f"**{title_r}**\n{content}")
                    if url:
                        sources.append(f"Tavily search '{query}': {url}")
            except Exception as e:
                if self.verbosity >= 1:
                    print(f"[SITREP] Search failed for '{query}': {e}")

        return "\n\n---\n\n".join(results) if results else "", sources

    def fetch_reference_urls(self, urls):
        """Fetch reference URLs and extract content."""
        if not urls:
            return "", []

        if self.progress:
            self.progress.update(f"Fetching {len(urls)} reference URL(s)...")
        elif self.verbosity >= 1:
            print(f"[SITREP] Fetching {len(urls)} reference URL(s)...")

        docs = fetch_urls(urls, output_format="markdown", verbosity=self.verbosity)

        if not docs:
            return "", []

        texts = []
        sources = []
        for doc in docs:
            texts.append(f"**Source: {doc['source']}**\n\n{doc['content']}")
            sources.append(f"Reference URL: {doc['source']}")

        return "\n\n---\n\n".join(texts), sources

    async def generate_sitrep(self, scenario, title=None, reference_urls=None,
                               actor_names=None):
        """Produce the SITREP document.

        Args:
            scenario: The simulation scenario text.
            title: Scenario title.
            reference_urls: List of URLs to fetch and include as source material.
            actor_names: List of actor name strings for the implications section.

        Returns:
            Tuple of (sitrep_text, sitrep_path) where sitrep_path is the saved file.
        """
        if self.progress:
            self.progress.start_phase("SITREP")
            self.progress.update("Gathering intelligence...")
        elif self.verbosity >= 1:
            print("[SITREP] Gathering intelligence...")

        # Generate DTG
        dtg = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%d%H%MZ %b %Y"
        ).upper()

        # Gather source material
        research_text, research_sources = await self.research(scenario, title=title)

        url_text, url_sources = self.fetch_reference_urls(reference_urls)

        all_sources = research_sources + url_sources

        # Actor names string
        if actor_names:
            actor_names_str = ", ".join(actor_names)
        else:
            actor_names_str = "(not specified — infer from scenario)"

        # Build the system prompt with DTG and actor names filled in
        system_prompt = SITREP_SYSTEM_PROMPT.format(
            title=title or "Untitled Scenario",
            dtg=dtg,
            actor_names=actor_names_str,
        )

        # Assemble user content
        user_content = f"## Scenario\n\n{scenario}\n\n"
        if research_text:
            user_content += f"## Web Research Results\n\n{research_text}\n\n"
        if url_text:
            user_content += f"## Reference Documents\n\n{url_text}\n\n"
        if all_sources:
            user_content += "## Sources Used\n\n"
            for s in all_sources:
                user_content += f"- {s}\n"
            user_content += "\n"
        user_content += "## Task\n\nProduce the SITREP now."

        if self.progress:
            self.progress.update("Generating SITREP...")
        elif self.verbosity >= 1:
            print("[SITREP] Generating SITREP...")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Stream to console if verbose
        if self.verbosity >= 1:
            if self.progress:
                self.progress.pause()

            sitrep = ""
            async for chunk in self.llm_client.complete_stream(
                model=self.model, messages=messages,
                max_tokens=6000, temperature=0.3,
            ):
                print(chunk, end="", flush=True)
                sitrep += chunk
            print()

            if self.progress:
                self.progress.resume()
        else:
            sitrep = await self.llm_client.complete(
                model=self.model, messages=messages,
                max_tokens=6000, temperature=0.3,
            )

        sitrep = sitrep.strip()

        # Save to disk
        sitrep_path = self._save_sitrep(sitrep, title)

        if self.progress:
            self.progress.end_phase()
            self.progress.update(f"SITREP complete ({len(sitrep)} chars) → {sitrep_path}")
        elif self.verbosity >= 1:
            print(f"[SITREP] Complete ({len(sitrep)} chars) → {sitrep_path}")

        return sitrep, sitrep_path

    def _save_sitrep(self, sitrep_text, title=None):
        """Save the SITREP as a markdown file."""
        sitrep_dir = os.path.join(os.getcwd(), ".snowglobe_data", "sitreps")
        os.makedirs(sitrep_dir, exist_ok=True)

        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        slug = _slugify(title or "sitrep")
        filename = f"{slug}_{ts}.md"
        path = os.path.join(sitrep_dir, filename)

        with open(path, "w") as f:
            f.write(sitrep_text)

        return path


def _slugify(text):
    """Convert text to a filesystem-safe slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:40].strip("_")
