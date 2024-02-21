import fastapi
from fastapi import HTTPException
from fastapi.security import SecurityScopes
from jose import ExpiredSignatureError

from src.api.dependencies.auth_utils import oauth2_password_scheme, oauth2_client_scheme, oauth2_code_scheme
from src.api.dependencies.repository import get_repository
from src.api.dependencies.session import get_async_session
from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.jwt import SJwtToken, SRefreshSession, Tokens
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.application import ApplicationCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.securities.authorizations.jwt import jwt_generator, AuthTypes
from src.securities.hashing.password import pwd_generator
from src.utilities.exceptions.http.exc_400 import http_exc_400_credentials_bad_signin_request, \
    http_exc_400_client_credentials_bad_request
from src.utilities.exceptions.http.exc_401 import (
    http_401_exc_bad_token_request,
    http_401_exc_expired_token_request,
    http_401_exc_not_enough_permissions,
)
from src.utilities.exceptions.http.exc_403 import http_403_forbidden_inactive_user


async def get_token_from_password_creds(
        request: fastapi.Request,
        response: fastapi.Response,
        username: str,
        password: str,
        client_id: str | None,
        account_repo: AccountCRUDRepository,
        refresh_session_repo: RefreshCRUDRepository,
):
    if client_id is None or client_id != settings.CLIENT_ID:
        raise await http_exc_400_client_credentials_bad_request()

    ip = request.client.host
    user_agent = request.headers.get("User-Agent")

    db_account = await account_repo.find_by_username_or_none(username=username)
    if db_account is None:
        raise await http_exc_400_credentials_bad_signin_request()
    if not db_account.is_active:
        raise http_403_forbidden_inactive_user()

    is_correct_pwd = pwd_generator.is_password_authenticated(
        hash_salt=db_account.hash_salt,
        password=password,
        hashed_password=db_account.hashed_password
    )
    if not is_correct_pwd:
        raise await http_exc_400_credentials_bad_signin_request()

    current_sessions = await refresh_session_repo.find_all(account=db_account.id)
    for session in current_sessions:
        if len(current_sessions) > 5 or session.ua == user_agent:
            await refresh_session_repo.delete_by_id(session.id, commit_changes=False)

    access_token = jwt_generator.generate_access_token(entity_obj=db_account, auth_type=AuthTypes.PASSWORD_CREDENTIALS_FLOW.value)

    s_refresh_session = SRefreshSession(
        account=db_account.id,
        ua=user_agent,
        # fingerprint=fingerprint,
        ip=ip,
    )
    refresh_session = await refresh_session_repo.create(s_refresh_session.model_dump())
    refresh_token = refresh_session.refresh_token

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,  # TODO change in prod
    )

    tokens = Tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MIN * 60
    )
    return tokens


async def get_token_from_client_creds(
        client_id: str | None,
        client_secret: str | None,
        app_repo: ApplicationCRUDRepository,
):
    if client_id is None or client_secret is None:
        raise await http_exc_400_client_credentials_bad_request()

    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None or app.client_secret != client_secret:
        raise await http_exc_400_client_credentials_bad_request()

    access_token = jwt_generator.generate_access_token(app, AuthTypes.CLIENT_CREDENTIALS_FLOW.value)
    tokens = Tokens(
        access_token=access_token,
        refresh_token=None,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MAX * 60
    )
    return tokens


async def get_token_payload(
        # token1: str = fastapi.Depends(oauth2_password_scheme),
        token2: str = fastapi.Depends(oauth2_client_scheme),
        token3: str = fastapi.Depends(oauth2_code_scheme),
        # token: str,
):
    try:
        payload = jwt_generator.retrieve_data_from_token(token3)
    except ExpiredSignatureError:
        raise await http_401_exc_expired_token_request()
    except Exception:
        raise await http_401_exc_bad_token_request()

    return payload


async def get_auth_user(
        security_scopes: SecurityScopes,
        payload: dict = fastapi.Depends(get_token_payload),
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository))
) -> Account:
    token_data = SJwtToken.model_validate(payload)

    db_account = None
    if token_data.refer == "user":
        username = token_data.sub
        db_account = await account_repo.find_by_username_or_none(username=username)
    elif token_data.refer == "app":
        app = await app_repo.find_by_client_id_or_none(client_id=token_data.sub)
        if app is None:
            raise await http_401_exc_bad_token_request()
        user_id = app.user
        db_account = await account_repo.find_by_id(user_id)

    if db_account is None:
        raise await http_401_exc_bad_token_request()

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise await http_401_exc_not_enough_permissions()

    return db_account

# async def get_auth_app(
#         security_scopes: SecurityScopes,
#         payload: dict = fastapi.Depends(get_token_payload),
#         account_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository))
# ) -> Application:
#     token_data = SJwtToken.model_validate(payload)
