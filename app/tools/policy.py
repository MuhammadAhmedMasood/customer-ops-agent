"""Tool: find the policy sections most relevant to a ticket (RAG retrieval)."""

import re
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

POLICY_PATH = Path(__file__).parents[2] / "data" / "policy.md"
EMBEDDING_MODEL = "text-embedding-3-small"


def load_policy_chunks() -> list[Document]:
    """One chunk per numbered section (e.g. 3.2), prefixed with its heading."""
    chunks = []
    heading = ""
    for line in POLICY_PATH.read_text().splitlines():
        if line.startswith("## "):
            heading = line.removeprefix("## ").split(". ", 1)[1]  # "## 3. Refunds" -> "Refunds"
        elif match := re.match(r"^(\d+\.\d+) (.+)", line):
            section, text = match.groups()
            chunks.append(Document(page_content=f"{heading}: {text}", metadata={"section": section}))
    return chunks


@lru_cache
def get_vector_store() -> InMemoryVectorStore:
    """Embed the policy the first time it's needed, then reuse it for every ticket."""
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return InMemoryVectorStore.from_documents(load_policy_chunks(), embeddings)


def search_policy(query: str, k: int = 3) -> list[Document]:
    return get_vector_store().similarity_search(query, k=k)
