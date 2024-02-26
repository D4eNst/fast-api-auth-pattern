import typing

import sqlalchemy
from sqlalchemy.orm import joinedload

from src.repository.models.application import Application
from src.repository.crud.base import BaseCRUDRepository
from src.repository.exceptions import EntityDoesNotExist


class ApplicationCRUDRepository(BaseCRUDRepository[Application]):
    model = Application

    async def find_by_id_or_none(self, id: int, **filter_by) -> typing.Optional[Application]:
        stmt = (sqlalchemy
                .select(self.model)
                .where(self.model.id == id)
                .filter_by(**filter_by)
                .options(joinedload(Application.allowed_users)))
        query = await self.async_session.execute(statement=stmt)
        result = query.scalar()
        return result

    async def find_by_id(self, id: int, **filter_by) -> Application:
        app = await self.find_by_id_or_none(id, **filter_by)
        if not app:
            raise EntityDoesNotExist(f"Object {self.model.__name__} with id `{id}` does not exist!")
        return app

    async def find_by_client_id(self, client_id: str, **filter_by) -> Application:
        # return await self.find_by_field(field_name='client_id', field_value=client_id, **filter_by)
        app = await self.find_by_client_id_or_none(client_id=client_id, **filter_by)
        if not app:
            raise EntityDoesNotExist(f"Object {self.model.__name__} with client id `{client_id}` does not exist!")
        return app

    async def find_by_client_id_or_none(self, client_id: str, **filter_by) -> Application | None:
        # return await self.find_by_field_or_none(field_name='client_id', field_value=client_id, **filter_by)
        stmt = (sqlalchemy
                .select(Application)
                .where(Application.client_id == client_id)
                .filter_by(**filter_by)
                .options(joinedload(Application.allowed_users)))
        query = await self.async_session.execute(statement=stmt)
        result = query.scalar()
        return result
