from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.logging import get_logger
from app.models import User
from app.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
logger = get_logger("export")


@router.get("/transactions")
async def export_transactions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    buffer = await service.transactions_csv(
        current_user,
        start_date=start_date,
        end_date=end_date,
        type=type,
    )

    filename = _build_filename(current_user.base_currency, start_date, end_date, type)

    logger.info(
        "export.transactions",
        user_id=str(current_user.id),
        start_date=str(start_date),
        end_date=str(end_date),
        type=type,
    )

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Limit": "10000",
        },
    )


def _build_filename(
    currency: str,
    start_date: date | None,
    end_date: date | None,
    type: str | None,
) -> str:
    parts = ["pocketledger", "transactions"]
    if type:
        parts.append(type)
    if start_date:
        parts.append(start_date.isoformat())
    if end_date:
        parts.append(end_date.isoformat())
    parts.append(currency)
    return "_".join(parts) + ".csv"