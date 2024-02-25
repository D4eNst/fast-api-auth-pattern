from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.application import Application, ApplicationUser
from src.repository.crud.base import BaseCRUDRepository
from src.securities.hashing.password import pwd_generator


class ApplicationCRUDRepository(BaseCRUDRepository[Application]):
    model = Application

    async def find_by_client_id(self, client_id: str, **filter_by) -> Application:
        return await self.find_by_field(field_name='client_id', field_value=client_id, **filter_by)

    async def find_by_client_id_or_none(self, client_id: str, **filter_by) -> Application | None:
        return await self.find_by_field_or_none(field_name='client_id', field_value=client_id, **filter_by)

    async def add_user(self, application_id: int, fullname: str, email: str, commit_changes: bool = True) -> ApplicationUser:
        data = dict(
            application_id=application_id,
            fullname=fullname,
            email=email,
        )
        new_obj = ApplicationUser(**data)

        self.async_session.add(instance=new_obj)
        if commit_changes:
            await self.async_session.commit()
            await self.async_session.refresh(instance=new_obj)

        return new_obj
