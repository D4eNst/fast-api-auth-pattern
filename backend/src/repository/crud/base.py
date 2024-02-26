import typing

import sqlalchemy
from sqlalchemy import Update, Delete, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import functions

from src.securities.password import PasswordGenerator
from src.repository.exceptions import EntityDoesNotExist

T = typing.TypeVar("T")


class BaseCRUDRepository(typing.Generic[T]):
    model: T = None

    def __init__(self, async_session: AsyncSession):
        super().__init__()
        self.async_session = async_session

    async def commit_changes(self):
        await self.async_session.commit()

    async def create(self, data: dict, commit_changes: bool = True) -> T:
        new_obj = self.model(**data)

        self.async_session.add(instance=new_obj)
        if commit_changes:
            await self.async_session.commit()
            await self.async_session.refresh(instance=new_obj)

        return new_obj

    async def find_all(self, **filter_by) -> typing.Sequence[T]:
        stmt = sqlalchemy.select(self.model).filter_by(**filter_by)
        query = await self.async_session.execute(statement=stmt)
        result = query.scalars()

        return result.all()

    async def find_by_id_or_none(self, id: int, **filter_by) -> typing.Optional[T]:
        stmt = sqlalchemy.select(self.model).where(self.model.id == id).filter_by(**filter_by)
        query = await self.async_session.execute(statement=stmt)
        result = query.scalar()
        return result

    async def find_by_id(self, id: int, **filter_by) -> T:
        result: T = await self.find_by_id_or_none(id, **filter_by)

        if not result:
            raise EntityDoesNotExist(f"Object {self.model.__name__} with id `{id}` does not exist!")

        return result

    async def find_by_field_or_none(self, field_name: str, field_value: typing.Any, **filter_by) -> typing.Optional[T]:
        column: ColumnElement = getattr(self.model, field_name, None)

        if column is None:
            raise ValueError(f"Field '{field_name}' not found in the model.")

        stmt = sqlalchemy.select(self.model).where(column == field_value).filter_by(**filter_by)
        query = await self.async_session.execute(statement=stmt)

        result = query.scalar()

        return result

    async def find_by_field(self, field_name: str, field_value: typing.Any, **filter_by) -> T:
        result = await self.find_by_field_or_none(field_name, field_value, **filter_by)
        if not result:
            raise EntityDoesNotExist(f"Object {self.model.__name__} with value `{field_value}` does not exist!")

        return result

    async def patch_by_id(self, id: int, data_to_update: dict, commit_changes: bool = True, **filter_by) -> T:
        update_account = await self.find_by_id(id=id, **filter_by)
        if not update_account:
            raise EntityDoesNotExist(f"Object with id `{id}` does not exist!")

        to_update = data_to_update.copy()
        update_stmt: Update = (
            sqlalchemy
            .update(table=self.model)
            .where(self.model.id == update_account.id)  # type: ignore
            .values()
        )

        if hasattr(self.model, "updated_at"):
            _ = to_update.pop("updated_at", None)
            update_stmt = update_stmt.values(updated_at=functions.now())

        if hasattr(self.model, "_hashed_password"):
            password: str | None = to_update.pop("password", None)
            if password is not None:
                update_account.set_hash_salt(hash_salt=PasswordGenerator.generate_salt())  # type: ignore

                update_account.set_hashed_password(
                    hashed_password=PasswordGenerator.generate_hashed_password(
                        hash_salt=update_account.hash_salt,
                        new_password=password))

        for update_column in to_update:
            if hasattr(self.model, update_column):
                update_value = to_update[update_column]
                update_attr = getattr(self.model, update_column)

                if update_value is not None or update_attr.nullable:
                    update_stmt = update_stmt.values({
                        f"{update_column}": update_value
                    })
            else:
                raise Exception(f"No such column: {update_column} in {self.model.__tablename__}")

        await self.async_session.execute(statement=update_stmt)
        if commit_changes:
            await self.async_session.commit()
            await self.async_session.refresh(instance=update_account)

        return update_account

    async def delete_by_id(self, id: int, commit_changes: bool = True, **filter_by) -> str:
        delete_obj = await self.find_by_id(id=id, **filter_by)

        if not delete_obj:
            raise EntityDoesNotExist(f"Object with id `{id}` does not exist!")

        stmt: Delete = sqlalchemy.delete(table=self.model).where(delete_obj.id == self.model.id)  # type: ignore

        await self.async_session.execute(statement=stmt)

        if commit_changes:
            await self.async_session.commit()

        return f"Object with id '{id}' is successfully deleted!"
