"""
Load replies.json and produce LangChain Document objects for embedding.
One document per reply; page_content combines intent, context, and text for semantic search.
"""

import json
from pathlib import Path

from langchain_core.documents import Document


def get_data_path() -> Path:
    """Project root (parent of this file)."""
    return Path(__file__).resolve().parent


def load_replies_json(path: Path | None = None) -> list[dict]:
    """Load and parse data/replies.json."""
    if path is None:
        path = get_data_path() / "data" / "replies.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def replies_to_documents(replies: list[dict]) -> list[Document]:
    """
    Convert reply records to LangChain Documents.
    page_content = intent + context + reply text so retrieval is semantic.
    """
    docs = []
    for item in replies:
        intent = item.get("intent", "")
        context = item.get("context", "") or item.get("scenario", "")
        text = item.get("text", "")
        parts = [f"Intent: {intent}"]
        if context:
            parts.append(f"Context: {context}")
        parts.append(f"Reply: {text}")
        page_content = " ".join(parts)
        metadata = {"intent": intent, "text": text}
        if context:
            metadata["context"] = context
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs


def get_documents(path: Path | None = None) -> list[Document]:
    """
    Load replies.json and return list of Document objects.
    path: optional path to replies.json; default is data/replies.json under project root.
    """
    replies = load_replies_json(path)
    return replies_to_documents(replies)


if __name__ == "__main__":
    docs = get_documents()
    print(f"Loaded {len(docs)} documents")
    if docs:
        print("Sample:", docs[0].page_content[:200], "...")
