import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import APIResponse
from app.repositories.notification import NotificationRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    notifications = await repo.get_unread_for_user(current_user.id)
    return APIResponse(data=[
        {
            "id": str(n.id),
            "budget_id": str(n.budget_id),
            "threshold": n.threshold,
            "percentage": n.percentage,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ])


@router.patch("/{id}/read")
async def mark_read(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    await repo.update(id, {"is_read": True})
    return APIResponse(data=None, message="Notification marked as read")