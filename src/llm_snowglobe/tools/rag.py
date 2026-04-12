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

"""Simple document loader for the planning agent.

Loads text files and returns their content. No vectorstore, no LangChain.
Used by the planning agent to ingest reference documents into the briefing.
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
