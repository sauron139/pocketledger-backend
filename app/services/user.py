from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def update(self, user: User, data: dict) -> User:
        updates = {k: v for k, v in data.items() if v is not None}

        if "email" in updates and updates["email"] != user.email:
            existing = await self.repo.get_by_email(updates["email"])
            if existing:
                raise ConflictError("Email already in use")

        return await self.repo.update(user.id, updates)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        await self.repo.update(user.id, {"hashed_password": hash_password(new_password)})

    async def delete(self, user: User) -> None:
        await self.repo.soft_delete(user.id)
