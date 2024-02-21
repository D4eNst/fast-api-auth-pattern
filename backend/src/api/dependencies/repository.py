import typing

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.session import get_async_session
from src.repository.crud.base import BaseCRUDRepository


def get_repository(
    repo_type: typing.Type[BaseCRUDRepository],
) -> typing.Callable[[AsyncSession], BaseCRUDRepository]:
    def _get_repo(
        async_session: AsyncSession = fastapi.Depends(get_async_session),
    ) -> BaseCRUDRepository:
        return repo_type(async_session=async_session)

    return _get_repo
