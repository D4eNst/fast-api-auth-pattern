from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.application import Application
from src.repository.crud.base import BaseCRUDRepository
from src.securities.hashing.password import pwd_generator


class ApplicationCRUDRepository(BaseCRUDRepository[Application]):
    model = Application

    async def find_by_client_id(self, client_id: str, **filter_by) -> Application:
        return await self.find_by_field(field_name='client_id', field_value=client_id)

    async def find_by_client_id_or_none(self, client_id: str, **filter_by) -> Application | None:
        return await self.find_by_field_or_none(field_name='client_id', field_value=client_id)
