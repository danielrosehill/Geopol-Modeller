#!/usr/bin/env python3

#   Licensed under the Apache License, Version 2.0

"""Planning agent that runs before simulation to produce a shared briefing.

Uses Tavily for current-events research, trafilatura for reference URL
ingestion, and optional local document loading.
All simulation agents receive the same briefing output.
"""

import os
from ..core.llm import LLMClient
from ..tools.rag import fetch_urls


PLANNING_SYSTEM_PROMPT = """\
You are a research analyst preparing a briefing document for a wargame simulation.

Given the scenario description below, you must:
1. Search for current real-world events, geopolitical context, and relevant background that could inform the simulation.
2. If reference documents are provided, incorporate key facts from them.
3. Produce a structured BRIEFING document that all players will receive.

The briefing should include:
- **Current Context**: Real-world events and conditions relevant to the scenario
- **Key Players & Relationships**: Known actors and their interests
- **Risk Factors**: Potential escalation paths or destabilizing factors
- **Historical Precedents**: Relevant past events that inform the scenario

Keep the briefing factual, concise, and actionable. Avoid speculation — label uncertainty clearly.
"""


class PlanningAgent:
    """Runs once before simulation to produce a shared briefing."""

    def __init__(self, llm_client, model, tavily_api_key=None, verbosity=1, progress=None):
        self.llm_client = llm_client
        self.model = model
        self.verbosity = verbosity
        self.progress = progress
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")

    async def research(self, scenario, title=None, num_queries=3):
        """Use Tavily to search for context relevant to the scenario."""
        if not self.tavily_api_key:
            if self.progress:
                self.progress.update("No TAVILY_API_KEY set, skipping web research")
            elif self.verbosity >= 1:
                print("[Planning] No TAVILY_API_KEY set, skipping web research")
            return ""

        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            if self.progress:
                self.progress.update("tavily-python not installed, skipping web research")
            elif self.verbosity >= 1:
                print("[Planning] tavily-python not installed, skipping web research")
            return ""

        client = AsyncTavilyClient(api_key=self.tavily_api_key)

        # Generate search queries from the scenario
        query_prompt = (
            f"Given this wargame scenario, generate {num_queries} concise web search queries "
            f"to find current real-world context. Return only the queries, one per line.\n\n"
            f"Title: {title or 'Untitled'}\n\n"
            f"Scenario:\n{scenario[:2000]}"
        )
        query_response = await self.llm_client.complete(
            model=self.model,
            messages=[{"role": "user", "content": query_prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        queries = [q.strip().strip("-•*0123456789.") for q in query_response.strip().split("\n") if q.strip()]
        queries = queries[:num_queries]

        if self.verbosity >= 2:
            print(f"[Planning] Searching for: {queries}")

        # Run searches
        results = []
        for query in queries:
            try:
                response = await client.search(query, max_results=3)
                for result in response.get("results", []):
                    results.append(f"**{result.get('title', '')}**\n{result.get('content', '')}")
            except Exception as e:
                if self.verbosity >= 1:
                    print(f"[Planning] Search failed for '{query}': {e}")

        return "\n\n---\n\n".join(results) if results else ""

    def load_documents(self, doc_paths=None, infodocs=None):
        """Load reference documents as plain text."""
        texts = []
        if doc_paths:
            for path in doc_paths:
                try:
                    with open(path, "r") as f:
                        texts.append(f"**{os.path.basename(path)}**:\n{f.read()}")
                except Exception as e:
                    if self.verbosity >= 1:
                        print(f"[Planning] Failed to load {path}: {e}")

        if infodocs:
            for name, doc in infodocs.items():
                texts.append(f"**{doc.get('title', name)}**:\n{doc.get('content', '')}")

        return "\n\n".join(texts) if texts else ""

    def load_reference_urls(self, urls):
        """Fetch reference URLs and extract clean markdown content.

        Uses trafilatura for robust content extraction (similar to Mozilla
        Readability). Each URL is fetched and its main content extracted
        as markdown, then formatted for inclusion in the briefing context.
        """
        if not urls:
            return ""

        if self.progress:
            self.progress.update(f"Fetching {len(urls)} reference URL(s)...")
        elif self.verbosity >= 1:
            print(f"[Planning] Fetching {len(urls)} reference URL(s)...")

        docs = fetch_urls(urls, output_format="markdown", verbosity=self.verbosity)

        if not docs:
            return ""

        texts = []
        for doc in docs:
            texts.append(f"**Source: {doc['source']}**\n\n{doc['content']}")

        return "\n\n---\n\n".join(texts)

    async def create_briefing(self, scenario, title=None, doc_paths=None,
                              infodocs=None, reference_urls=None):
        """Produce the briefing document that all agents will receive.

        Args:
            scenario: The simulation scenario text.
            title: Scenario title.
            doc_paths: Local file paths to ingest.
            infodocs: Dict of inline documents.
            reference_urls: List of URLs to fetch and include as context.
        """
        if self.progress:
            self.progress.start_phase("PLANNING")
            self.progress.update("Researching current events...")
        elif self.verbosity >= 1:
            print("[Planning] Researching current events...")

        research = await self.research(scenario, title=title)

        if self.progress:
            self.progress.update("Loading reference documents...")
        elif self.verbosity >= 1:
            print("[Planning] Loading reference documents...")

        documents = self.load_documents(doc_paths=doc_paths, infodocs=infodocs)

        # Fetch reference URLs
        url_content = self.load_reference_urls(reference_urls)

        # Assemble context for the planner
        user_content = f"## Scenario: {title or 'Untitled'}\n\n{scenario}\n\n"
        if research:
            user_content += f"## Web Research Results\n\n{research}\n\n"
        if documents:
            user_content += f"## Reference Documents\n\n{documents}\n\n"
        if url_content:
            user_content += f"## Reference URLs\n\n{url_content}\n\n"
        user_content += "## Task\n\nProduce the briefing document now."

        if self.progress:
            self.progress.update("Generating briefing...")
        elif self.verbosity >= 1:
            print("[Planning] Generating briefing...")

        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        if self.verbosity >= 1:
            if self.progress:
                self.progress.pause()

            briefing = ""
            async for chunk in self.llm_client.complete_stream(
                model=self.model, messages=messages, max_tokens=4096, temperature=0.4
            ):
                print(chunk, end="", flush=True)
                briefing += chunk
            print()

            if self.progress:
                self.progress.resume()
        else:
            briefing = await self.llm_client.complete(
                model=self.model, messages=messages, max_tokens=4096, temperature=0.4
            )

        if self.progress:
            self.progress.end_phase()
            self.progress.update(f"Briefing complete ({len(briefing)} chars)")
        elif self.verbosity >= 1:
            print(f"[Planning] Briefing complete ({len(briefing)} chars)")

        return briefing.strip()
