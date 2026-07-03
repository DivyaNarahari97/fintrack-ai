import anthropic
from typing import Iterator
from .embedder import query_similar

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = (
    "You are a helpful personal finance assistant. You have access to the user's bank "
    "transaction data retrieved by semantic similarity.\n"
    "Answer questions about spending patterns, categories, and financial habits. "
    "Be specific with amounts and dates. Format currency as USD (e.g. $42.50).\n"
    "If the retrieved data doesn't contain enough information to answer precisely, say so honestly."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _build_context(user_id: str, question: str) -> str:
    items = query_similar(user_id, question, n_results=20)
    if not items:
        return "No transaction data found for this user yet."
    lines = [
        f"- {item.get('date', '?')} | {item.get('description', '?')} "
        f"| ${item.get('amount', 0):.2f} | {item.get('category', 'Other')}"
        for item in items
    ]
    return "Retrieved transactions:\n" + "\n".join(lines)


def stream_rag_response(user_id: str, question: str) -> Iterator[str]:
    context = _build_context(user_id, question)
    with _get_client().messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Transaction data:\n{context}\n\nQuestion: {question}",
            }
        ],
    ) as stream:
        yield from stream.text_stream
