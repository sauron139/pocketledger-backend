import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import APIResponse, CategoryResponse, CreateCategoryRequest, UpdateCategoryRequest
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/")
async def list_categories(
    type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    categories = await service.list(current_user, type=type)
    return APIResponse(data=[CategoryResponse.model_validate(c) for c in categories])


@router.post("/")
async def create_category(
    body: CreateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.create(current_user, body.name, body.type, body.icon)
    return APIResponse(data=CategoryResponse.model_validate(category))


@router.patch("/{id}")
async def update_category(
    id: uuid.UUID,
    body: UpdateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.update(current_user, id, body.model_dump())
    return APIResponse(data=CategoryResponse.model_validate(category))


@router.delete("/{id}")
async def delete_category(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    await service.delete(current_user, id)
    return APIResponse(data=None, message="Category deleted")
