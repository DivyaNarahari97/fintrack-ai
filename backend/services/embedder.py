import chromadb
from datetime import date
from decimal import Decimal
from sentence_transformers import SentenceTransformer
from config import settings

_model: SentenceTransformer | None = None
_chroma: chromadb.HttpClient | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _get_chroma() -> chromadb.HttpClient:
    global _chroma
    if _chroma is None:
        _chroma = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return _chroma


def _collection_name(user_id: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in user_id)
    return f"u_{safe}"[:63]


def upsert_transactions(
    user_id: str,
    tx_ids: list[str],
    dates: list[date],
    descriptions: list[str],
    amounts: list[Decimal],
    categories: list[str],
) -> None:
    if not tx_ids:
        return

    model = _get_model()
    client = _get_chroma()
    collection = client.get_or_create_collection(name=_collection_name(user_id))

    texts = [
        f"Date: {d} | Description: {desc} | Amount: {float(amt):.2f} | Category: {cat}"
        for d, desc, amt, cat in zip(dates, descriptions, amounts, categories)
    ]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()
    metadatas = [
        {"date": str(d), "description": desc, "amount": float(amt), "category": cat}
        for d, desc, amt, cat in zip(dates, descriptions, amounts, categories)
    ]

    collection.upsert(ids=tx_ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query_similar(user_id: str, query_text: str, n_results: int = 20) -> list[dict]:
    model = _get_model()
    client = _get_chroma()

    try:
        collection = client.get_collection(name=_collection_name(user_id))
    except Exception:
        return []

    count = collection.count()
    if count == 0:
        return []

    query_embedding = model.encode([query_text], show_progress_bar=False).tolist()[0]

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, count),
            include=["documents", "metadatas"],
        )
    except Exception:
        return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return [{"text": doc, **meta} for doc, meta in zip(docs, metas)]
