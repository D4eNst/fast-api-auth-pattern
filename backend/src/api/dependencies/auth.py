from typing import Annotated

import fastapi
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError

from src.api.dependencies.repository import get_repository
from src.config.manager import settings
from src.models.db.account import Account
from src.repository.crud.account import AccountCRUDRepository
from src.securities.authorizations.jwt import jwt_generator
from src.securities.hashing.password import pwd_generator
from src.utilities.exceptions.http.exc_400 import http_exc_400_credentials_bad_signin_request
from src.utilities.exceptions.http.exc_401 import (
    http_401_exc_bad_token_request,
    http_401_exc_expired_token_request
)
from src.utilities.exceptions.http.exc_403 import http_403_forbidden_inactive_user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token/"
)


def check_client(account_login: OAuth2PasswordRequestForm):
    client_id = account_login.client_id
    client_secret = account_login.client_secret
    return settings.CLIENT_ID == client_id and settings.CLIENT_SECRET == client_secret


async def validate_auth_user(
        account_login: Annotated[OAuth2PasswordRequestForm, fastapi.Depends()],
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> Account:
    if not check_client(account_login):
        raise await http_exc_400_credentials_bad_signin_request()
    try:
        db_account = await account_repo.find_by_username(username=account_login.username)
    except Exception:
        raise await http_exc_400_credentials_bad_signin_request()

    if not db_account.is_active:
        raise http_403_forbidden_inactive_user()

    is_correct_pwd = pwd_generator.is_password_authenticated(
        hash_salt=db_account.hash_salt,
        password=account_login.password,
        hashed_password=db_account.hashed_password
    )

    if not is_correct_pwd:
        raise await http_exc_400_credentials_bad_signin_request()

    return db_account


async def get_token_payload(
        token: str = fastapi.Depends(oauth2_scheme),
        # token: str,
):
    try:
        payload = jwt_generator.retrieve_data_from_token(token)
    except ExpiredSignatureError:
        raise await http_401_exc_expired_token_request()
    except Exception:
        raise await http_401_exc_bad_token_request()

    return payload


async def get_auth_user(
        payload: dict = fastapi.Depends(get_token_payload),
        account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository))
) -> Account:
    username = payload.get("sub")
    db_account = await account_repo.find_by_username(username=username, is_active=True)
    return db_account
