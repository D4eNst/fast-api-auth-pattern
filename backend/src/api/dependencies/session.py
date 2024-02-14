import typing

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.repository.database import async_db


async def get_async_session() -> typing.AsyncGenerator[AsyncSession, None]:
    try:
        yield async_db.async_session
    except Exception as e:
        print(e)
        await async_db.async_session.rollback()
    finally:
        await async_db.async_session.close()
