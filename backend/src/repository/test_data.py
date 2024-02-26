import loguru
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.sql.functions import user

from src.models.db.application import ApplicationUser
from src.models.schemas.account import AccountInCreate
from src.models.schemas.application import SApplication, SApplicationUser
from src.models.schemas.jwt import SRefreshSession
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.application import ApplicationCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.repository.table import Base


async def delete_tables(connection: AsyncConnection):
    alembic_version_table = Table('alembic_version', MetaData())
    tables_to_drop = [table for table in Base.metadata.tables.values() if table is not alembic_version_table]
    await connection.run_sync(Base.metadata.drop_all, tables=tables_to_drop)


async def update_bd_in_change(connection: AsyncConnection):
    existing_tables = await connection.run_sync(
        lambda sync_conn: inspect(sync_conn).get_table_names()
    )
    if set(Base.metadata.tables.keys()).issubset(existing_tables):
        loguru.logger.info("Database Tables already exist. Skipping creation.")
    else:
        await delete_tables(connection)
        await connection.run_sync(Base.metadata.create_all)

        await create_initial_test_data(connection)
        loguru.logger.info("Database Table Creation --- Successfully Initialized!")


async def create_initial_test_data(connection: AsyncConnection) -> None:
    loguru.logger.info("Creating Initial Test Data...")

    async with AsyncSession(connection) as session:
        account_repo = AccountCRUDRepository(async_session=session)
        accounts = [
            AccountInCreate(username="string", email="user@example.com", password="string"),
            AccountInCreate(username="user1", email="user1@exa.com", password="qwerty"),
            AccountInCreate(username="user2", email="user2@exa.com", password="qwerty"),
            AccountInCreate(username="user3", email="user3@exa.com", password="qwerty"),
            AccountInCreate(username="user4", email="user4@exa.com", password="qwerty"),
            AccountInCreate(username="user5", email="user5@exa.com", password="qwerty"),
        ]
        for account in accounts:
            await account_repo.create(data=account.model_dump(), commit_changes=False)

        refresh_session_repo = RefreshCRUDRepository(async_session=session)
        refresh_sessions = [
            SRefreshSession(account=1, ua="ua", ip="111-22-3-44")
        ]
        for refresh_session in refresh_sessions:
            a = await refresh_session_repo.create(data=refresh_session.model_dump(), commit_changes=False)

        app_repo = ApplicationCRUDRepository(async_session=session)
        apps = [
            SApplication(user=1, name="test", website="http://localhost:8000",
                         redirect_uris=["https://oauth.pstmn.io/v1/callback"])
        ]
        for app in apps:
            application = await app_repo.create(data=app.model_dump(), commit_changes=False)
            application.allowed_users.append(ApplicationUser(application_id=application.id, fullname="fullname", email="user@example.com"))

        await account_repo.commit_changes()
        await session.commit()

    loguru.logger.info("Initial Test Data Created Successfully!")
