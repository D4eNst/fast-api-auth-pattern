import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.models.account import Account
from src.repository.crud.base import BaseCRUDRepository
from src.securities.password import PasswordGenerator
from src.repository.exceptions import EntityAlreadyExists


class AccountCRUDRepository(BaseCRUDRepository[Account]):
    model: Account = Account

    def __init__(self, async_session: AsyncSession):
        super().__init__(async_session)

    async def create(self, data: dict, commit_changes: bool = True) -> Account:
        password = data.pop("password")
        new_account = Account(**data)

        new_account.set_hash_salt(hash_salt=PasswordGenerator.generate_salt())
        new_account.set_hashed_password(
            hashed_password=PasswordGenerator.generate_hashed_password(
                hash_salt=new_account.hash_salt, new_password=password
            )
        )

        self.async_session.add(instance=new_account)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_account)

        return new_account

    async def find_by_email(self, email: str, **filter_by) -> Account:
        return await self.find_by_field(field_name="email", field_value=email, **filter_by)

    async def find_by_username(self, username: str, **filter_by) -> Account:
        return await self.find_by_field(field_name="username", field_value=username, **filter_by)

    async def find_by_username_or_none(self, username: str, **filter_by) -> Account:
        return await self.find_by_field_or_none(field_name="username", field_value=username, **filter_by)

    async def is_email_taken(self, email: str) -> bool:
        email_stmt = sqlalchemy.select(Account.email).select_from(Account).where(Account.email == email)
        email_query = await self.async_session.execute(email_stmt)
        db_email = email_query.scalar()

        if db_email is not None:
            raise EntityAlreadyExists(f"The email `{email}` is already registered!")  # type: ignore

        return True

    async def is_username_taken(self, username: str) -> bool:
        username_stmt = sqlalchemy.select(Account.username).select_from(Account).where(Account.username == username)
        username_query = await self.async_session.execute(username_stmt)
        db_username = username_query.scalar()

        if db_username is not None:
            raise EntityAlreadyExists(f"The username `{username}` is already registered!")  # type: ignore
        return True
