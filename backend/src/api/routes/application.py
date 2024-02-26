from typing import Annotated

import fastapi
from fastapi import Security

from src.api.dependencies.auth import get_auth_user
from src.api.dependencies.repository import get_repository
from src.api.dependencies.scopes import Scopes
from src.models.db.account import Account
from src.models.db.application import Application, ApplicationUser
from src.models.schemas.application import SApplicationAns, SApplicationCreate, SApplication, SApplicationUpdate, \
    SApplicationUserCreate, SApplicationUserUpdate, SApplicationUser
from src.repository.crud.application import ApplicationCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_400 import http_400_exc_bad_email_request
from src.utilities.exceptions.http.exc_404 import http_404_exc_id_not_found_request

router = fastapi.APIRouter(prefix="/app", tags=["application"])


@router.get(
    path="",
    name="app:read-applications",
    response_model=list[SApplicationAns],
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_app_list(
        account: Annotated[Account, Security(get_auth_user, scopes=[Scopes.user_dev_read.str])],
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> list[SApplicationAns]:
    apps = await app_repo.find_all(user=account.id)
    ans_list = list()
    for app in apps:
        ans_list.append(SApplicationAns.model_validate(app))
    return ans_list


@router.post(
    path="",
    name="app:create-applications",
    response_model=None,
    status_code=fastapi.status.HTTP_200_OK,
)
async def create_app(
        account: Annotated[
            Account, Security(get_auth_user, scopes=[Scopes.user_dev_read.str, Scopes.user_dev_modify.str])],
        app_in_create: SApplicationCreate,
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> Application:

    s_app = SApplication(
        user=account.id,
        name=app_in_create.name,
        description=app_in_create.description,
        website=app_in_create.website,
        redirect_uris=app_in_create.redirect_uris
    )
    app = await app_repo.create(data=s_app.model_dump())
    return app


@router.get(
    path="/{id}",
    name="app:read-application-by-id",
    response_model=None,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_app(
        id: int,
        account: Annotated[Account, Security(get_auth_user, scopes=Scopes.get_scopes_strings(Scopes.USER_DEV))],
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> Application:
    app = await app_repo.find_by_id_or_none(id, user=account.id)
    if app is None:
        raise await http_404_exc_id_not_found_request(id)

    return app


@router.delete(
    path="/{id}",
    name="app:delete-application-by-id",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_app(
        id: int,
        account: Annotated[Account, Security(get_auth_user, scopes=Scopes.get_scopes_strings(Scopes.USER_DEV))],
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> dict[str, str]:
    try:
        res_del = await app_repo.delete_by_id(id, user=account.id)
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id)

    return {"notification": res_del}


@router.patch(
    path="/{id}",
    name="app:patch-application-by-id",
    response_model=None,
    status_code=fastapi.status.HTTP_200_OK,
)
async def patch_app(
        id: int,
        app_update: SApplicationUpdate,
        account: Annotated[Account, Security(get_auth_user, scopes=Scopes.get_scopes_strings(Scopes.USER_DEV))],
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> Application:
    try:
        updated_app = await app_repo.patch_by_id(id=id, data_to_update=app_update.model_dump(), user=account.id)
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id)
    return updated_app


@router.post(
    path="/{app_id}/allowed_user",
    name="app:create-applications-user",
    status_code=fastapi.status.HTTP_200_OK,
)
async def create_app_user(
        app_id: int,
        account: Annotated[
            Account, Security(get_auth_user, scopes=[Scopes.user_dev_read.str, Scopes.user_dev_modify.str])
        ],
        app_user_in_create: SApplicationUserCreate,
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> dict[str, str]:
    app = await app_repo.find_by_id_or_none(app_id, user=account.id)
    if app is None:
        raise await http_404_exc_id_not_found_request(app_id)

    for allowed_user in app.allowed_users.copy():
        if allowed_user.email == app_user_in_create.email:
            raise await http_400_exc_bad_email_request(app_user_in_create.email)

    app.allowed_users.append(ApplicationUser(**app_user_in_create.model_dump()))
    await app_repo.commit_changes()
    return {"notification": "allowed user has been created"}


@router.patch(
    path="/{app_id}/allowed_user/{app_user_id}",
    name="app:create-applications-user",
    status_code=fastapi.status.HTTP_200_OK,
)
async def create_app_user(
        app_id: int,
        app_user_id: int,
        account: Annotated[
            Account, Security(get_auth_user, scopes=[Scopes.user_dev_read.str, Scopes.user_dev_modify.str])
        ],
        upp_user_update: SApplicationUserUpdate,
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> dict[str, str]:
    app = await app_repo.find_by_id_or_none(app_id, user=account.id)
    if app is None:
        raise await http_404_exc_id_not_found_request(app_id)
    if len(app.allowed_users) >= 30:
        raise fastapi.HTTPException(status_code=400, detail="You have added the maximum number of users. To increase the allowed amount, your application must exit development mode")

    for allowed_user in app.allowed_users.copy():
        s_app_user = SApplicationUser.model_validate(allowed_user)
        if s_app_user.id == app_user_id:
            app_user: ApplicationUser = allowed_user
            app.allowed_users.remove(allowed_user)
            break
    else:
        raise await http_404_exc_id_not_found_request(app_user_id)
    app_user.fullname = upp_user_update.fullname if upp_user_update.fullname is not None else app_user.fullname
    app_user.email = upp_user_update.email if upp_user_update.email is not None else app_user.email

    app.allowed_users.append(app_user)
    await app_repo.commit_changes()
    return {"notification": "allowed user has been updated"}


@router.delete(
    path="/{app_id}/allowed_user/{app_user_id}",
    name="app:delete-application-by-id",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_app(
        app_id: int,
        app_user_id,
        account: Annotated[Account, Security(get_auth_user, scopes=Scopes.get_scopes_strings(Scopes.USER_DEV))],
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository)),
) -> dict[str, str]:
    app = await app_repo.find_by_id_or_none(app_id, user=account.id)
    if app is None:
        raise await http_404_exc_id_not_found_request(app_id)

    for allowed_user in app.allowed_users.copy():
        if allowed_user.id == app_user_id:
            app.allowed_users.remove(allowed_user)
            break
    else:
        raise await http_404_exc_id_not_found_request(app_user_id)
    await app_repo.commit_changes()
    return {"notification": "allowed user has been deleted"}
