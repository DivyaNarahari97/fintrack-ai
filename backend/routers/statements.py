import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_or_create_user
from database import AsyncSessionLocal, get_db
from models import Statement, Transaction, User
from schemas import StatementOut, UploadResponse
from services.categorizer import categorize_transactions
from services.embedder import compute_embeddings, store_to_chromadb
from services.parser import parse_file

router = APIRouter()


async def _process_statement(
    statement_id: uuid.UUID,
    user_id: str,
    file_bytes: bytes,
    filename: str,
) -> None:
    async with AsyncSessionLocal() as db:
        stmt = await db.get(Statement, statement_id)
        if stmt is None:
            return
        try:
            # Step 1: parse (everything depends on this)
            raw_txs = await asyncio.to_thread(parse_file, file_bytes, filename)

            embed_texts = [
                f"Date: {r.date} | Description: {r.description} | Amount: {float(r.amount):.2f}"
                for r in raw_txs
            ]

            # Step 2: categorize + embed in parallel (both only need raw_txs)
            categories, embeddings = await asyncio.gather(
                asyncio.to_thread(categorize_transactions, raw_txs),
                asyncio.to_thread(compute_embeddings, embed_texts),
            )

            # Step 3: build Transaction rows (IDs generated here, not by DB)
            tx_rows: list[Transaction] = [
                Transaction(
                    id=uuid.uuid4(),
                    statement_id=statement_id,
                    user_id=user_id,
                    date=raw.date,
                    description=raw.description,
                    amount=raw.amount,
                    currency=raw.currency,
                    category=category,
                    raw_text=raw.raw_text,
                )
                for raw, category in zip(raw_txs, categories)
            ]
            for tx in tx_rows:
                db.add(tx)

            # Step 4: flush to Postgres + store to ChromaDB in parallel
            async def _pg_flush() -> None:
                await db.flush()

            await asyncio.gather(
                _pg_flush(),
                asyncio.to_thread(
                    store_to_chromadb,
                    user_id,
                    [str(tx.id) for tx in tx_rows],
                    [tx.date for tx in tx_rows],
                    [tx.description for tx in tx_rows],
                    [tx.amount for tx in tx_rows],
                    [tx.category or "Other" for tx in tx_rows],
                    embeddings,
                ),
            )

            stmt.status = "done"
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with AsyncSessionLocal() as db2:
                stmt2 = await db2.get(Statement, statement_id)
                if stmt2:
                    stmt2.status = "error"
                    stmt2.error_message = str(exc)[:500]
                    await db2.commit()


@router.post("/upload", response_model=UploadResponse)
async def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "csv", "xlsx", "xls"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, CSV, or XLSX.")

    file_bytes = await file.read()
    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 20 MB limit.")

    statement = Statement(
        id=uuid.uuid4(),
        user_id=user.clerk_id,
        filename=file.filename or "upload",
        file_type=ext,
        status="processing",
    )
    db.add(statement)
    await db.commit()

    background_tasks.add_task(
        _process_statement, statement.id, user.clerk_id, file_bytes, file.filename or "upload"
    )

    return UploadResponse(statement_id=statement.id, status="processing")


@router.get("", response_model=list[StatementOut])
async def list_statements(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> list[StatementOut]:
    result = await db.execute(
        select(Statement)
        .where(Statement.user_id == user.clerk_id)
        .order_by(Statement.uploaded_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{statement_id}", response_model=StatementOut)
async def get_statement(
    statement_id: uuid.UUID,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> StatementOut:
    result = await db.execute(
        select(Statement).where(
            Statement.id == statement_id, Statement.user_id == user.clerk_id
        )
    )
    stmt = result.scalar_one_or_none()
    if stmt is None:
        raise HTTPException(status_code=404, detail="Statement not found")
    return stmt


@router.delete("/{statement_id}", status_code=204)
async def delete_statement(
    statement_id: uuid.UUID,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Statement).where(
            Statement.id == statement_id, Statement.user_id == user.clerk_id
        )
    )
    stmt = result.scalar_one_or_none()
    if stmt is None:
        raise HTTPException(status_code=404, detail="Statement not found")
    await db.delete(stmt)
    await db.commit()
