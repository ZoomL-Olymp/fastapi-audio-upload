from typing import Any, Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserUpdate

class CRUDUser(CRUDBase[User, User, UserUpdate]): # using User as CreateSchema placeholder
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(self.model).filter(self.model.email == email))
        return result.scalars().first()

    async def get_by_yandex_id(self, db: AsyncSession, *, yandex_id: str) -> Optional[User]:
        result = await db.execute(select(self.model).filter(self.model.yandex_id == yandex_id))
        return result.scalars().first()

    async def create_with_yandex(
        self, db: AsyncSession, *, yandex_id: str, email: Optional[str] = None,
        first_name: Optional[str] = None, last_name: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        """Creates a user directly from Yandex data."""
        db_obj = User(
            yandex_id=yandex_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_superuser=is_superuser
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
        # Use the base update method
        return await super().update(db=db, db_obj=db_obj, obj_in=obj_in)

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser(User)