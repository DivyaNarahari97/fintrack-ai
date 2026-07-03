import json
import anthropic
from .parser import RawTransaction

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Healthcare", "Education", "Utilities", "Housing", "Travel",
    "Income", "Transfers", "Other",
]

BATCH_SIZE = 50
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def categorize_transactions(transactions: list[RawTransaction]) -> list[str]:
    result: list[str] = []
    for i in range(0, len(transactions), BATCH_SIZE):
        batch = transactions[i : i + BATCH_SIZE]
        result.extend(_categorize_batch(batch))
    return result


def _categorize_batch(batch: list[RawTransaction]) -> list[str]:
    lines = [
        f"{i}. {tx.description} | ${abs(tx.amount):.2f} {'credit' if tx.amount >= 0 else 'debit'}"
        for i, tx in enumerate(batch)
    ]
    prompt = (
        f"Categorize each financial transaction. Use exactly one of: {', '.join(CATEGORIES)}.\n\n"
        "Transactions:\n"
        + "\n".join(lines)
        + "\n\nRespond with a JSON array only, no other text. Format: "
        '[{"index": 0, "category": "Food & Dining"}, ...]'
    )

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = next((b.text for b in message.content if b.type == "text"), "[]").strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else "[]"
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        items = json.loads(raw)
        cat_map = {item["index"]: item["category"] for item in items}
        return [cat_map.get(i, "Other") for i in range(len(batch))]
    except (json.JSONDecodeError, KeyError, TypeError):
        return ["Other"] * len(batch)
