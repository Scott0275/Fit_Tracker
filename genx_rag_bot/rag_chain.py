"""
RAG chain: load FAISS index and prompts, retrieve top k=4, generate reply with Google Gemini.
Exposes get_reply(incoming_message) for the app.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ingest import get_data_path

load_dotenv()

INDEX_DIR = "faiss_index"
TOP_K = 4
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "gemini-2.0-flash"


def _load_prompt(name: str) -> str:
    path = get_data_path() / "prompts" / name
    return path.read_text(encoding="utf-8").strip()


def _get_vectorstore():
    base = get_data_path()
    index_path = base / INDEX_DIR
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {index_path}. Run: python embed.py"
        )
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)


def _format_similar_replies(docs: list) -> str:
    """Turn retrieved documents into a single string of 'similar past replies'."""
    lines = []
    for i, doc in enumerate(docs, 1):
        reply = doc.metadata.get("text", doc.page_content)
        lines.append(f"{i}. {reply}")
    return "\n".join(lines) if lines else ""


def get_reply(incoming_message: str) -> str:
    """
    Generate an on-brand reply for the given DM or comment.
    Uses RAG (top 4 similar past replies) and strict system prompt; falls back to safe default if no index or no results.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY is not set. Add it to .env or the environment.")

    system_text = _load_prompt("system_dm.txt")
    fallback_text = _load_prompt("fallback.txt")

    try:
        vectorstore = _get_vectorstore()
        docs = vectorstore.similarity_search(incoming_message, k=TOP_K)
    except FileNotFoundError:
        docs = []

    if not docs:
        similar_replies_block = f"Similar past replies (use this tone):\n{fallback_text}"
    else:
        similar_replies_block = "Similar past replies (match tone and intent when relevant):\n" + _format_similar_replies(docs)

    user_content = f"{similar_replies_block}\n\nIncoming DM or comment to reply to:\n{incoming_message}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_text),
        ("human", "{user_content}"),
    ])

    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.35)
    chain = prompt | llm
    response = chain.invoke({"user_content": user_content})

    reply = response.content if hasattr(response, "content") else str(response)
    return reply.strip()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rag_chain.py \"Your DM or comment here\"")
        sys.exit(1)
    msg = " ".join(sys.argv[1:])
    print(get_reply(msg))
