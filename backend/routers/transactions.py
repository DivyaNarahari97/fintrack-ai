from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_or_create_user
from database import get_db
from models import Transaction, User
from schemas import CategoryTotal, MonthlyTotal, SummaryOut, TransactionPage

router = APIRouter()


@router.get("", response_model=TransactionPage)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: str | None = None,
    search: str | None = None,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionPage:
    conditions = [Transaction.user_id == user.clerk_id]
    if category:
        conditions.append(Transaction.category == category)
    if search:
        conditions.append(Transaction.description.ilike(f"%{search}%"))

    total = (
        await db.execute(
            select(func.count()).select_from(Transaction).where(and_(*conditions))
        )
    ).scalar_one()

    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            select(Transaction)
            .where(and_(*conditions))
            .order_by(Transaction.date.desc())
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()

    return TransactionPage(items=list(rows), total=total, page=page, page_size=page_size)


@router.get("/summary", response_model=SummaryOut)
async def get_summary(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
) -> SummaryOut:
    cat_rows = (
        await db.execute(
            select(Transaction.category, func.sum(Transaction.amount), func.count())
            .where(Transaction.user_id == user.clerk_id, Transaction.amount < 0)
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount))
        )
    ).all()
    by_category = [
        CategoryTotal(category=r[0] or "Other", total=abs(r[1]), count=r[2])
        for r in cat_rows
    ]

    month_rows = (
        await db.execute(
            select(
                func.to_char(Transaction.date, "YYYY-MM").label("month"),
                func.sum(Transaction.amount),
            )
            .where(Transaction.user_id == user.clerk_id, Transaction.amount < 0)
            .group_by("month")
            .order_by("month")
        )
    ).all()
    by_month = [MonthlyTotal(month=r[0], total=abs(r[1])) for r in month_rows]

    total_spent = abs(
        (
            await db.execute(
                select(func.sum(Transaction.amount)).where(
                    Transaction.user_id == user.clerk_id, Transaction.amount < 0
                )
            )
        ).scalar_one_or_none()
        or 0
    )

    merch_rows = (
        await db.execute(
            select(Transaction.description, func.sum(Transaction.amount), func.count())
            .where(Transaction.user_id == user.clerk_id, Transaction.amount < 0)
            .group_by(Transaction.description)
            .order_by(func.sum(Transaction.amount))
            .limit(5)
        )
    ).all()
    top_merchants = [
        {"name": r[0], "total": float(abs(r[1])), "count": r[2]} for r in merch_rows
    ]

    return SummaryOut(
        by_category=by_category,
        by_month=by_month,
        total_spent=total_spent,
        top_merchants=top_merchants,
    )
