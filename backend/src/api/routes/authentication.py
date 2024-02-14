import datetime
import uuid

import fastapi
from fastapi import Form

from src.api.dependencies.auth import validate_auth_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.account import AccountInCreate, AccountDetail
from src.models.schemas.jwt import Tokens, SRefreshSession
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.refresh_session import RefreshCRUDRepository
from src.securities.authorizations.jwt import jwt_generator
from src.utilities.exceptions.database import EntityAlreadyExists
from src.utilities.exceptions.http.exc_400 import http_400_exc_bad_email_request, http_400_exc_bad_username_request
from src.utilities.exceptions.http.exc_401 import http_401_exc_bad_token_request, \
    http_401_exc_expired_token_request

router = fastapi.APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/token",
    name="auth:get-tokens",
    response_model=Tokens,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_tokens(
        response: fastapi.Response,
        request: fastapi.Request,
        db_account: Account = fastapi.Depends(validate_auth_user),
        # fingerprint: str = fastapi.Header(alias="X-Fingerprint"),
        refresh_session_repo: RefreshCRUDRepository = fastapi.Depends(get_repository(repo_type=RefreshCRUDRepository))
) -> Tokens:
    ip = request.client.host
    user_agent = request.headers.get("User-Agent")

    current_sessions = await refresh_session_repo.find_all(account=db_account.id)
    for session in current_sessions:
        if len(current_sessions) > 5 or session.ua == user_agent:
            await refresh_session_repo.delete_by_id(session.id, commit_changes=False)

    access_token = jwt_generator.generate_access_token(account=db_account)

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

    tokens = Tokens(access_token=access_token, refresh_token=refresh_token)
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

    new_access_token = jwt_generator.generate_access_token(account=db_account)

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

    tokens = Tokens(access_token=new_access_token, refresh_token=new_refresh_token)
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
