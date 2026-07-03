from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import io
import re

import pandas as pd
import pdfplumber


@dataclass
class RawTransaction:
    date: date
    description: str
    amount: Decimal
    currency: str = "USD"
    raw_text: str = ""


def parse_file(file_bytes: bytes, filename: str) -> list[RawTransaction]:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return _parse_pdf(file_bytes)
    elif ext == "csv":
        return _parse_csv(file_bytes)
    elif ext in ("xlsx", "xls"):
        return _parse_xlsx(file_bytes)
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(file_bytes: bytes) -> list[RawTransaction]:
    transactions: list[RawTransaction] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Try to extract table rows from each page
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    tx = _try_parse_row(row)
                    if tx:
                        transactions.append(tx)

    # Fallback: regex line-by-line parsing
    if not transactions:
        transactions = _parse_text_lines(all_text)

    return transactions


def _try_parse_row(row: list) -> RawTransaction | None:
    """Attempt to extract a transaction from a table row (handles most bank formats)."""
    if not row or len(row) < 3:
        return None
    cells = [str(c or "").strip() for c in row]
    raw = " | ".join(cells)

    date_val = _find_date(cells)
    amount_val = _find_amount(cells)
    description = _find_description(cells, date_val, amount_val)

    if date_val and amount_val is not None and description:
        return RawTransaction(date=date_val, description=description, amount=amount_val, raw_text=raw)
    return None


def _parse_text_lines(text: str) -> list[RawTransaction]:
    """Line-based fallback for unstructured PDF text."""
    transactions: list[RawTransaction] = []
    date_pattern = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
    amount_pattern = re.compile(r"-?\$?([\d,]+\.\d{2})")

    for line in text.splitlines():
        line = line.strip()
        date_m = date_pattern.search(line)
        amount_m = amount_pattern.search(line)
        if date_m and amount_m:
            try:
                d = _parse_date_str(date_m.group())
                amt = Decimal(amount_m.group(1).replace(",", ""))
                desc = line[: date_m.start()].strip() + line[date_m.end() : amount_m.start()].strip()
                desc = re.sub(r"\s+", " ", desc).strip() or "Unknown"
                # Treat positive amounts as debits (expenses) — negate
                if amt > 0 and "credit" not in line.lower() and "deposit" not in line.lower():
                    amt = -amt
                transactions.append(RawTransaction(date=d, description=desc, amount=amt, raw_text=line))
            except Exception:
                continue
    return transactions


def _parse_csv(file_bytes: bytes) -> list[RawTransaction]:
    df = pd.read_csv(io.BytesIO(file_bytes), on_bad_lines="skip")
    return _df_to_transactions(df)


def _parse_xlsx(file_bytes: bytes) -> list[RawTransaction]:
    df = pd.read_excel(io.BytesIO(file_bytes))
    return _df_to_transactions(df)


def _df_to_transactions(df: pd.DataFrame) -> list[RawTransaction]:
    df.columns = [c.lower().strip() for c in df.columns]

    date_col = _find_col(df, ["date", "transaction date", "trans date", "posted date", "value date"])
    desc_col = _find_col(df, ["description", "desc", "merchant", "payee", "transaction", "details", "narration"])
    amount_col = _find_col(df, ["amount", "debit", "credit", "transaction amount", "value"])

    if not date_col or not desc_col or not amount_col:
        raise ValueError(
            f"Could not detect required columns. Found: {list(df.columns)}. "
            "Expected columns for date, description, and amount."
        )

    transactions: list[RawTransaction] = []
    for _, row in df.iterrows():
        try:
            d = _parse_date_str(str(row[date_col]))
            desc = str(row[desc_col]).strip()
            raw_amt = str(row[amount_col]).replace(",", "").replace("$", "").strip()
            amt = Decimal(raw_amt)
            transactions.append(RawTransaction(date=d, description=desc, amount=amt, raw_text=str(row.to_dict())))
        except Exception:
            continue
    return transactions


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_date(cells: list[str]) -> date | None:
    for cell in cells:
        try:
            return _parse_date_str(cell)
        except Exception:
            continue
    return None


def _find_amount(cells: list[str]) -> Decimal | None:
    amount_pat = re.compile(r"^-?\$?([\d,]+\.\d{2})$")
    for cell in reversed(cells):
        m = amount_pat.match(cell.replace(" ", ""))
        if m:
            try:
                return Decimal(m.group(1).replace(",", "")) * (-1 if "-" in cell else 1)
            except Exception:
                continue
    return None


def _find_description(cells: list[str], found_date: date | None, found_amount: Decimal | None) -> str:
    candidates = []
    amount_pat = re.compile(r"^-?\$?[\d,]+\.\d{2}$")
    date_pat = re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}")
    for cell in cells:
        if not cell:
            continue
        if amount_pat.match(cell.replace(" ", "")):
            continue
        if date_pat.search(cell) and len(cell) < 15:
            continue
        candidates.append(cell)
    return " ".join(candidates[:3]).strip() or "Unknown"


def _parse_date_str(s: str) -> date:
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m-%d-%Y", "%b %d, %Y", "%d %b %Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}")
