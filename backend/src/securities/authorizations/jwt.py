import datetime
import enum
from calendar import timegm
from typing import Optional

import pydantic
from jose import jwt as jose_jwt, JWTError, ExpiredSignatureError

from src.config.manager import settings
from src.models.db.account import Account
from src.models.db.application import Application
from src.models.schemas.account import AccountScopes
from src.models.schemas.jwt import SJwtToken


class AuthTypes(enum.Enum):
    PASSWORD_CREDENTIALS_FLOW = "password"
    AUTHORIZATION_CODE_FLOW = "authorization_code"
    CLIENT_CREDENTIALS_FLOW = "client_credentials"
    IMPLICIT_GRANT_FLOW = "implicit_grant"


class JWTGenerator:
    def __init__(self):
        pass

    @classmethod
    def _generate_jwt_token(
            cls,
            *,
            jwt_data: dict[str, str | int],
            expires_delta: datetime.timedelta | None = None,
    ) -> str:
        to_encode = jwt_data.copy()
        issued_at = timegm(datetime.datetime.utcnow().utctimetuple())
        if expires_delta:
            expire = issued_at + expires_delta.seconds
        else:
            expire = issued_at + datetime.timedelta(minutes=settings.JWT_TOKEN_EXPIRATION_TIME_MIN).seconds

        to_encode.update(
            iat=issued_at,
            exp=expire,
        )

        return jose_jwt.encode(to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def generate_access_token(self, entity_obj: object, auth_type: str) -> str:
        scopes = ["read"]
        refer: str
        if auth_type in (AuthTypes.PASSWORD_CREDENTIALS_FLOW.value, AuthTypes.AUTHORIZATION_CODE_FLOW.value):
            expires_delta = datetime.timedelta(minutes=settings.JWT_TOKEN_EXPIRATION_TIME_MIN)
        else:
            expires_delta = datetime.timedelta(minutes=settings.JWT_TOKEN_EXPIRATION_TIME_MAX)

        if isinstance(entity_obj, Account):
            sub_obj = getattr(entity_obj, "username")
            scopes.extend(AccountScopes(role=entity_obj.role.value).get_scopes())
            refer = "user"
        elif isinstance(entity_obj, Application):
            sub_obj = getattr(entity_obj, "client_id")
            refer = "app"
        else:
            raise ValueError(f"Cannot generate JWT token with entity type {type(entity_obj)}! "
                             f"Supported entities are Account or Application!")

        return self._generate_jwt_token(
            jwt_data=SJwtToken(sub=sub_obj, scopes=" ".join(scopes), refer=refer).model_dump(),
            expires_delta=expires_delta
        )

    @classmethod
    def retrieve_data_from_token(cls, token: str, secret_key: str = settings.JWT_SECRET_KEY) -> dict:
        try:
            payload = jose_jwt.decode(
                token=token,
                key=secret_key,
                algorithms=[settings.JWT_ALGORITHM],
                options=dict(
                    verify_sub=False
                )
            )

        except ExpiredSignatureError as token_expired_error:
            raise ExpiredSignatureError() from token_expired_error
        except JWTError as token_decode_error:
            raise ValueError("Unable to decode JWT Token") from token_decode_error
        except pydantic.ValidationError as validation_error:
            raise ValueError("Invalid payload in token") from validation_error

        return payload


def get_jwt_generator() -> JWTGenerator:
    return JWTGenerator()


jwt_generator: JWTGenerator = get_jwt_generator()
