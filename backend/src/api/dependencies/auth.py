import base64
import hashlib
import json

import fastapi
from fastapi.security import SecurityScopes
from jose import ExpiredSignatureError

from src.api.dependencies.auth_utils import oauth2_client_scheme, oauth2_code_scheme
from src.api.dependencies.repository import get_repository
from src.api.dependencies.scopes import Scopes
from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.jwt import SJwtToken, SRefreshSession, Tokens
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.application import ApplicationCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.repository.database import redis_client
from src.securities.authorizations.jwt import jwt_generator, AuthTypes
from src.securities.hashing.password import pwd_generator
from src.utilities.exceptions.http.exc_400 import http_exc_400_credentials_bad_signin_request, \
    http_exc_400_client_credentials_bad_request, http_exc_400_req_body_bad_signin_request
from src.utilities.exceptions.http.exc_401 import (
    http_401_exc_bad_token_request,
    http_401_exc_expired_token_request,
    http_401_exc_not_enough_permissions,
    http_exc_401_unauthorized_request,
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
    # if client_id is None or client_id != settings.CLIENT_ID:
    #     raise await http_exc_400_client_credentials_bad_request()

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

    access_token = jwt_generator.generate_access_token(
        db_account,
        AuthTypes.PASSWORD_CREDENTIALS_FLOW.value,
        Scopes.get_scopes_strings()
    )

    s_refresh_session = SRefreshSession(
        account=db_account.id,
        ua=user_agent,
        ip=ip,
        scope=Scopes.in_string(),
    )
    refresh_session = await refresh_session_repo.create(s_refresh_session.model_dump())
    refresh_token = refresh_session.refresh_token

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,  # TODO change in prod
    )
    response.headers.append("Access-Control-Allow-Origin", settings.ALLOWED_ORIGINS[0])

    tokens = Tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MIN * 60,
        scope=" ".join(Scopes.get_scopes_strings())
    )
    return tokens


async def get_token_from_client_creds(
        client_id: str | None,
        client_secret: str | None,
        app_repo: ApplicationCRUDRepository,
        account_repo: AccountCRUDRepository,
) -> Tokens:
    if client_id is None or client_secret is None:
        raise await http_exc_400_client_credentials_bad_request()

    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None or app.client_secret != client_secret:
        raise await http_exc_400_client_credentials_bad_request()
    user = await account_repo.find_by_id(app.user)

    access_token = jwt_generator.generate_access_token(user, AuthTypes.CLIENT_CREDENTIALS_FLOW.value, list())
    tokens = Tokens(
        access_token=access_token,
        refresh_token=None,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MAX * 60,
        scope=None
    )
    return tokens


async def get_token_from_auth_code(
        request: fastapi.Request,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str | None,
        code: str | None,
        app_repo: ApplicationCRUDRepository,
        account_repo: AccountCRUDRepository,
        refresh_session_repo: RefreshCRUDRepository,
        code_verifier: str = ""
) -> Tokens:
    if client_id is None is None or redirect_uri is None or code is None:
        raise await http_exc_400_req_body_bad_signin_request()

    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None:
        raise await http_exc_400_client_credentials_bad_request()

    user_agent = request.headers.get("User-Agent")
    ip = request.client.host

    async with redis_client.pipeline() as pipeline:
        await pipeline.get(name=f"code:{code}")
        await pipeline.delete(f"code:{code}")
        data_dict_json = (await pipeline.execute())[0]

    if data_dict_json:
        data_dict = json.loads(data_dict_json)
    else:
        raise await http_exc_400_req_body_bad_signin_request()

    scope = data_dict["scope"]

    if data_dict["code_challenge"] is not None:
        hashed_code_verifier = hashlib.sha256(code_verifier.encode()).digest()
        encoded_hashed_code_verifier = base64.urlsafe_b64encode(hashed_code_verifier).rstrip(b'=').decode()
        if not code_verifier or encoded_hashed_code_verifier != data_dict["code_challenge"]:
            raise await http_exc_400_req_body_bad_signin_request()
    elif client_secret is None or client_secret != app.client_secret:
        raise await http_exc_400_client_credentials_bad_request()

    if redirect_uri != data_dict["redirect_uri"]:
        raise await http_exc_400_req_body_bad_signin_request()

    db_account = await account_repo.find_by_id(id=data_dict["user_id"])
    current_sessions = await refresh_session_repo.find_all(account=db_account.id)
    for session in current_sessions:
        if len(current_sessions) > 5 or session.ua == user_agent:
            await refresh_session_repo.delete_by_id(session.id, commit_changes=False)

    access_token = jwt_generator.generate_access_token(
        sub=db_account,
        auth_type=AuthTypes.AUTHORIZATION_CODE_FLOW.value,
        scopes=scope.split()
    )

    s_refresh_session = SRefreshSession(
        account=db_account.id,
        ua=user_agent,
        ip=ip,
        scope=scope
    )
    refresh_session = await refresh_session_repo.create(s_refresh_session.model_dump())
    refresh_token = refresh_session.refresh_token

    tokens = Tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MIN * 60,
        scope=scope
    )
    return tokens


async def get_token_from_account(
        client_id: str | None,
        account: Account,
        scope: str,
        app_repo: ApplicationCRUDRepository,
) -> Tokens:
    if not client_id:
        raise await http_exc_400_client_credentials_bad_request()

    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None:
        raise await http_exc_400_client_credentials_bad_request()

    access_token = jwt_generator.generate_access_token(account, AuthTypes.CLIENT_CREDENTIALS_FLOW.value, scope.split())
    tokens = Tokens(
        access_token=access_token,
        refresh_token=None,
        expires_in=settings.JWT_TOKEN_EXPIRATION_TIME_MAX * 60,
        scope=None
    )
    return tokens


async def get_token_payload(
        # token1: str = fastapi.Depends(oauth2_password_scheme),
        token2: str = fastapi.Depends(oauth2_client_scheme),
        token3: str = fastapi.Depends(oauth2_code_scheme),
        # token: str,
):
    if token2 is None:
        raise await http_exc_401_unauthorized_request()
    try:
        payload = jwt_generator.retrieve_data_from_token(token3)
    except ExpiredSignatureError:
        raise await http_401_exc_expired_token_request()
    except Exception as e:
        print(e)
        return None

    return payload


async def get_auth_user_or_none(
        security_scopes: SecurityScopes,
        payload: dict = fastapi.Depends(get_token_payload),
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository))
) -> Account | None:
    if not payload:
        return None
    token_data = SJwtToken.model_validate(payload)
    username = token_data.sub
    db_account = await account_repo.find_by_username_or_none(username=username)

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise await http_401_exc_not_enough_permissions()

    return db_account


async def get_auth_user(
        account: Account | None = fastapi.Depends(get_auth_user_or_none)
) -> Account:
    if account is None:
        raise await http_401_exc_bad_token_request()
    return account
