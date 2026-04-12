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

"""Document and URL loader for the planning agent.

Loads text files and fetches URLs as clean markdown for ingestion into
the briefing context. Uses trafilatura for robust web content extraction.
"""

import os


def load_text(path):
    with open(path, "r") as f:
        return f.read()


def chunk_text(text, chunk_size=2000, overlap=200):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def load_documents(paths, chunk_size=None):
    """Load documents from file paths, optionally chunking them.

    Returns list of {"source": path, "content": text} dicts.
    """
    docs = []
    for path in paths:
        if not os.path.exists(path):
            continue
        text = load_text(path)
        if chunk_size and len(text) > chunk_size:
            for chunk in chunk_text(text, chunk_size=chunk_size):
                docs.append({"source": path, "content": chunk})
        else:
            docs.append({"source": path, "content": text})
    return docs


def fetch_url(url, output_format="markdown", verbosity=1):
    """Fetch a URL and extract its main content as clean text.

    Uses trafilatura for robust content extraction (similar to Mozilla
    Readability). Falls back to raw download if trafilatura can't extract.

    Args:
        url: The URL to fetch.
        output_format: "markdown", "text", or "xml". Default "markdown".
        verbosity: Print status messages at verbosity >= 1.

    Returns:
        dict with "source" (url) and "content" (extracted text), or None on failure.
    """
    try:
        import trafilatura
    except ImportError:
        if verbosity >= 1:
            print(f"[refs] trafilatura not installed, skipping {url}")
        return None

    if verbosity >= 1:
        print(f"[refs] Fetching {url}")

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            if verbosity >= 1:
                print(f"[refs] Failed to download {url}")
            return None

        content = trafilatura.extract(
            downloaded,
            output_format=output_format,
            include_links=True,
            include_tables=True,
            favor_recall=True,
        )

        if not content:
            if verbosity >= 1:
                print(f"[refs] No content extracted from {url}")
            return None

        if verbosity >= 1:
            print(f"[refs] Extracted {len(content)} chars from {url}")

        return {"source": url, "content": content}

    except Exception as e:
        if verbosity >= 1:
            print(f"[refs] Error fetching {url}: {e}")
        return None


def fetch_urls(urls, output_format="markdown", verbosity=1):
    """Fetch multiple URLs and return extracted content.

    Args:
        urls: List of URLs to fetch.
        output_format: "markdown", "text", or "xml".
        verbosity: Print status messages at verbosity >= 1.

    Returns:
        List of {"source": url, "content": text} dicts (failures omitted).
    """
    results = []
    for url in urls:
        result = fetch_url(url, output_format=output_format, verbosity=verbosity)
        if result:
            results.append(result)
    return results
