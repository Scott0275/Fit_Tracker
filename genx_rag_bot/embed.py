"""
Build FAISS vector store from data/replies.json using Google Gemini embeddings.
Run after updating replies.json to refresh the index.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from ingest import get_data_path, get_documents

load_dotenv()

INDEX_DIR = "faiss_index"
EMBEDDING_MODEL = "models/gemini-embedding-001"


def build_and_save_index(index_path: Path | None = None) -> FAISS:
    """
    Load documents from replies.json, embed with Google Gemini, build FAISS index, save to disk.
    Returns the in-memory FAISS vector store.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        raise SystemExit("GOOGLE_API_KEY is not set. Add it to .env or the environment.")

    base = index_path or get_data_path()
    save_path = base / INDEX_DIR

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    documents = get_documents()

    if not documents:
        raise SystemExit("No documents from data/replies.json. Add at least one reply.")

    try:
        vectorstore = FAISS.from_documents(documents, embeddings)
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e) or "resource_exhausted" in str(e).lower():
            raise SystemExit(
                "Google API quota exceeded. Check your usage at "
                "https://aistudio.google.com/"
            ) from e
        raise

    vectorstore.save_local(str(save_path))
    print(f"Saved FAISS index to {save_path} ({len(documents)} documents)")
    return vectorstore


if __name__ == "__main__":
    build_and_save_index()
