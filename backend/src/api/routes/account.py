from typing import Annotated

import fastapi
import pydantic
from fastapi import Security

from src.api.dependencies.auth import get_auth_user
from src.api.dependencies.repository import get_repository
from src.api.dependencies.scopes import Scopes
from src.models.db.account import Account
from src.models.schemas.account import AccountInUpdate, AccountDetail
from src.repository.crud.account import AccountCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_404 import (
    http_404_exc_id_not_found_request,
)

router = fastapi.APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    path="",
    name="accounts:read-accounts",
    response_model=list[AccountDetail],
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_accounts(
        account: Annotated[Account, Security(get_auth_user, scopes=[])],
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> list[AccountDetail]:
    db_accounts = await account_repo.find_all()
    db_account_list = list()

    for db_account in db_accounts:
        account = AccountDetail.model_validate(db_account)

        db_account_list.append(account)

    return db_account_list


@router.get(
    path="/me",
    name="auth:get-my-account",
    response_model=AccountDetail,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_me(
        account: Annotated[Account, Security(get_auth_user, scopes=Scopes.scopes(Scopes.VIEW_ACCOUNT_DETAILS))],
) -> AccountDetail:
    return AccountDetail.model_validate(account)


@router.get(
    path="/{id}",
    name="accounts:read-account-by-id",
    response_model=AccountDetail,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_account(
        id: int,
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountDetail:
    try:
        db_account = await account_repo.find_by_id(id=id)

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    return AccountDetail.model_validate(db_account)


@router.patch(
    path="/{id}",
    name="accounts:update-account-by-id",
    response_model=AccountDetail,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_account(
        id: int,
        account_update: AccountInUpdate,
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountDetail:

    try:
        updated_db_account = await account_repo.patch_by_id(id=id, data_to_update=account_update.model_dump())

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    return AccountDetail.model_validate(updated_db_account)


@router.delete(
    path="/{id}",
    name="accounts:delete-account-by-id",
    status_code=fastapi.status.HTTP_200_OK)
async def delete_account(
        id: int,
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository))
) -> dict[str, str]:
    try:
        # deletion_result = await account_repo.delete_account_by_id(id=id)
        deletion_result = await account_repo.delete_by_id(id=id)

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    return {"notification": deletion_result}
