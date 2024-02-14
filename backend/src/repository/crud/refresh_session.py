from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.refresh_session import RefreshSession
from src.repository.crud.base import BaseCRUDRepository


class RefreshCRUDRepository(BaseCRUDRepository[RefreshSession]):
    model = RefreshSession

    def __init__(self, async_session: AsyncSession):
        super().__init__(async_session)

    async def get_by_token(self, refresh_token: UUID) -> RefreshSession:
        return await self.find_by_field("refresh_token", refresh_token)

    async def get_by_token_or_none(self, refresh_token: UUID) -> RefreshSession:
        return await self.find_by_field_or_none("refresh_token", refresh_token)
