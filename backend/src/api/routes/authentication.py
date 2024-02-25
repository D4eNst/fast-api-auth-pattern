import datetime
import json
import secrets
import uuid
from typing import Optional

import fastapi
from fastapi import Form
from fastapi.security import HTTPBasicCredentials, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import (
    get_token_from_password_creds,
    get_token_from_client_creds,
    get_auth_user_or_none,
    get_token_from_auth_code, get_token_payload, get_token_from_account,
)
from src.api.dependencies.auth_utils import OAuth2RequestForm, security
from src.api.dependencies.repository import get_repository
from src.api.dependencies.scopes import Scopes
from src.api.dependencies.session import get_async_session
from src.config.manager import settings
from src.models.schemas.account import AccountInCreate, AccountDetail
from src.models.schemas.jwt import Tokens, SRefreshSession
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.application import ApplicationCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.repository.database import redis_client
from src.securities.authorizations.jwt import jwt_generator, AuthTypes
from src.utilities.exceptions.database import EntityAlreadyExists
from src.utilities.exceptions.http.exc_400 import http_400_exc_bad_email_request, http_400_exc_bad_username_request
from src.utilities.exceptions.http.exc_401 import http_401_exc_bad_token_request, http_401_exc_expired_token_request

router = fastapi.APIRouter(prefix="/auth", tags=["authentication"])


@router.get(
    "/authorize",
    name="auth:get-tokens",
    # response_model=Tokens,
    status_code=fastapi.status.HTTP_200_OK,
)
async def authorize(
        request: fastapi.Request,
        client_id: str = "",
        response_type: str = "",
        redirect_uri: str = "",
        state: str = "",
        scope: str = "",
        code_challenge_method: str = None,
        code_challenge: str = None,
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository))
):
    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None and client_id != settings.CLIENT_ID:
        return "INVALID_CLIENT: Invalid client"
    if code_challenge_method is not None and code_challenge_method != "S256":
        return "INVALID_CLIENT: Invalid code challenge method"
    if scope:
        for sc in scope.split(" "):
            if sc not in Scopes.all_scopes_strings():
                return "INVALID_CLIENT: Scope invalid"
    if redirect_uri not in app.redirect_uris:
        return "INVALID_CLIENT: Invalid redirect_uri"

    params = "?" + str(request.query_params)

    access_token = request.cookies.pop('access_token', '')
    user = await get_auth_user_or_none(
        security_scopes=SecurityScopes(),
        account_repo=account_repo,
        payload=await get_token_payload(
            access_token, access_token
        )
    )
    if user is None:
        return fastapi.responses.RedirectResponse(
            '/api/login' + params,
            status_code=fastapi.status.HTTP_302_FOUND)

    if response_type.lower().strip() == "token":
        tokens = await get_token_from_account(client_id=client_id, account=user, scope=scope, app_repo=app_repo)
        return fastapi.responses.RedirectResponse(
            f"{redirect_uri}?access_token={tokens.access_token}&"
            f"token_type=Bearer&"
            f"expires_in={tokens.expires_in}&"
            f"state={state}",
            status_code=fastapi.status.HTTP_302_FOUND)

    code = secrets.token_urlsafe(64)

    data_dict = {'user_id': user.id, 'scope': scope, 'redirect_uri': redirect_uri, "code_challenge": code_challenge}
    await redis_client.setex(name=f"code:{code}", value=json.dumps(data_dict), time=datetime.timedelta(minutes=5))

    return fastapi.responses.RedirectResponse(
        f"{redirect_uri}?code={code}&state={state}",
        status_code=fastapi.status.HTTP_302_FOUND)


@router.post(
    "/token",
    name="auth:get-tokens",
    response_model=Tokens,
    status_code=fastapi.status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def get_tokens(
        response: fastapi.Response,
        request: fastapi.Request,
        authorization: Optional[HTTPBasicCredentials] = fastapi.Depends(security),
        auth_descr: str = fastapi.Header(default=None, alias="Authorization", description="to add it in OpenAPI, use HTTPBasic"),
        form_data: OAuth2RequestForm = fastapi.Depends(),
        async_session: AsyncSession = fastapi.Depends(get_async_session)
) -> Tokens:
    account_repo = AccountCRUDRepository(async_session=async_session)
    refresh_session_repo = RefreshCRUDRepository(async_session=async_session)
    app_repo = ApplicationCRUDRepository(async_session=async_session)

    client_id_headers, client_secret_headers = None, None
    client_id_body, client_secret_body = None, None

    if authorization is None or not authorization.username or not authorization.password:
        client_id_body, client_secret_body = form_data.client_id, form_data.client_secret
    else:
        client_id_headers, client_secret_headers = authorization.username, authorization.password

    if not form_data.grant_type or form_data.grant_type == AuthTypes.PASSWORD_CREDENTIALS_FLOW.value:
        tokens = await get_token_from_password_creds(
            request=request,
            response=response,
            username=form_data.username,
            password=form_data.password,
            client_id=client_id_body,
            account_repo=account_repo,
            refresh_session_repo=refresh_session_repo
        )
    elif form_data.grant_type == AuthTypes.CLIENT_CREDENTIALS_FLOW.value:
        tokens = await get_token_from_client_creds(
            client_id=client_id_headers,
            client_secret=client_secret_headers,
            app_repo=app_repo,
            account_repo=account_repo
        )
    elif form_data.grant_type == AuthTypes.AUTHORIZATION_CODE_FLOW.value:
        client_id_for_code = client_id_headers if not form_data.code_verifier else client_id_body

        tokens = await get_token_from_auth_code(
            request=request,
            client_id=client_id_for_code,
            client_secret=client_secret_headers,
            redirect_uri=form_data.redirect_uri,
            code=form_data.code,
            code_verifier=form_data.code_verifier,
            app_repo=app_repo,
            account_repo=account_repo,
            refresh_session_repo=refresh_session_repo
        )
    else:
        raise

    return tokens


@router.post(
    "/refresh",
    name="auth:refresh-tokens",
    response_model=Tokens,
    status_code=fastapi.status.HTTP_200_OK,
)
async def refresh_tokens(
        response: fastapi.Response,
        request: fastapi.Request,
        refresh_token: uuid.UUID = Form(),
        grant_type: str = Form(default="refresh_token"),
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
        refresh_session_repo: RefreshCRUDRepository = fastapi.Depends(get_repository(repo_type=RefreshCRUDRepository)),
):
    if grant_type != "refresh_token":
        raise await http_401_exc_bad_token_request()
    try:
        refresh_session = await refresh_session_repo.get_by_token(refresh_token=refresh_token)
    except Exception:
        raise await http_401_exc_bad_token_request()

    if refresh_session.expires_in < datetime.datetime.utcnow().timestamp():
        await refresh_session_repo.delete_by_id(refresh_session.id)
        raise await http_401_exc_expired_token_request()

    user_agent = request.headers.get("User-Agent")
    if user_agent != refresh_session.ua:
        await refresh_session_repo.delete_by_id(refresh_session.id)
        raise await http_401_exc_bad_token_request()

    try:
        db_account = await account_repo.find_by_id(id=refresh_session.account)
    except Exception:
        await refresh_session_repo.delete_by_id(refresh_session.id)
        raise await http_401_exc_bad_token_request()

    # scope = refresh_session.scope  # TODO ADD SCOPES TO REFRESH SESSION
    scope = list()

    new_access_token = jwt_generator.generate_access_token(
        db_account,
        AuthTypes.AUTHORIZATION_CODE_FLOW.value,
        scope
    )

    new_s_refresh_session = SRefreshSession(
        account=db_account.id,
        ua=user_agent,
        # fingerprint=fingerprint,
        ip=refresh_session.ip,
    )
    await refresh_session_repo.delete_by_id(id=refresh_session.id, commit_changes=False)

    new_refresh_session = await refresh_session_repo.create(new_s_refresh_session.model_dump())
    new_refresh_token = new_refresh_session.refresh_token

    response.set_cookie(
        "refresh_token",
        new_refresh_token,
        httponly=True,
        secure=False,  # TODO change in prod
    )

    tokens = Tokens(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MIN * 60,
        scope=scope
    )
    return tokens


@router.post(
    "/signup",
    name="auth:signup",
    response_model=AccountDetail,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def signup(
        account_create: AccountInCreate,
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountDetail:
    try:
        await account_repo.is_email_taken(email=account_create.email)
    except EntityAlreadyExists:
        raise await http_400_exc_bad_email_request(email=account_create.email)

    try:
        await account_repo.is_username_taken(username=account_create.username)
    except EntityAlreadyExists:
        raise await http_400_exc_bad_username_request(username=account_create.email)

    new_account = await account_repo.create(data=account_create.model_dump())

    return AccountDetail.model_validate(new_account)


# # Пример пути с использованием шаблона
# @router.get(
#     path="/login",
#     name="auth/login",
#     response_class=HTMLResponse,
# )
# async def login_page(request: fastapi.Request):
#     return templates.TemplateResponse("login.html", {"request": request})
