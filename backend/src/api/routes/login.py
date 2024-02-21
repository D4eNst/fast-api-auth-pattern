import datetime
import uuid

import fastapi
from fastapi import Form
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from src.api.dependencies.repository import get_repository
from src.models.schemas.jwt import SRefreshSession
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.securities.hashing.password import pwd_generator
from src.utilities.exceptions.http.exc_400 import http_exc_400_credentials_bad_signin_request
from src.utilities.exceptions.http.exc_403 import http_403_forbidden_inactive_user

router = fastapi.APIRouter(tags=["login"], )
templates = Jinja2Templates(directory="templates")


@router.get(
    path="/login",
    name="login:page-to-login",
    status_code=fastapi.status.HTTP_200_OK,
)
async def login_page(
        request: fastapi.Request,
        errors: str = "",
        client_id: str = "",
        response_type: str = "",
        redirect_uri: str = "",
        state: str = "",
        scope: str = "",
        code_challenge_method: str = "",
        code_challenge: str = ""
):
    query_params = str(request.query_params)
    params = "?" + query_params if query_params else ""
    print("------------------------", params)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"errors": errors, "next_url": params, "app": "test_app", "is_main_app": "false"}
    )


@router.post(
    path="/login",
    name="login:login-check-creds",
    status_code=fastapi.status.HTTP_200_OK,
)
async def login_page(
        request: fastapi.Request,
        response: fastapi.Response,
        username: str = Form(),
        password: str = Form(),
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
        refresh_session_repo: RefreshCRUDRepository = fastapi.Depends(get_repository(repo_type=RefreshCRUDRepository)),
):
    query_params = str(request.query_params)
    next_url = "?" + query_params if query_params else ""
    print("------------------------", next_url)
    ip = request.client.host
    # if ip != "127.0.0.1":
    #     raise fastapi.HTTPException(status_code=400)

    db_account = await account_repo.find_by_username_or_none(username=username)
    if db_account is None:
        errors = "?errors=Username or Password is incorrect"
        return fastapi.responses.RedirectResponse(
            url='/api/login' + errors,
            status_code=fastapi.status.HTTP_302_FOUND
        )
    if not db_account.is_active:
        errors = "?errors=Inactive user!"
        return fastapi.responses.RedirectResponse(
            url='/api/login' + errors,
            status_code=fastapi.status.HTTP_302_FOUND)

    is_correct_pwd = pwd_generator.is_password_authenticated(
        hash_salt=db_account.hash_salt,
        password=password,
        hashed_password=db_account.hashed_password
    )
    if not is_correct_pwd:
        errors = "?errors=Username or Password is incorrect"
        return fastapi.responses.RedirectResponse(
            url='/api/login' + errors,
            status_code=fastapi.status.HTTP_302_FOUND
        )
    if not next_url:
        return fastapi.responses.RedirectResponse(
            '/docs',
            status_code=fastapi.status.HTTP_302_FOUND)

    return fastapi.responses.RedirectResponse(
        '/api/authorize' + next_url,
        status_code=fastapi.status.HTTP_302_FOUND)
