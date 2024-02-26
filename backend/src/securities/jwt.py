import datetime
import enum
from calendar import timegm

import pydantic
from jose import jwt as jose_jwt, JWTError, ExpiredSignatureError

from src.config.manager import settings
from src.repository.models.account import Account

from src.schemas.jwt import SJwtToken


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

    @classmethod
    def generate_access_token(cls, sub: Account, auth_type: str, scopes: list) -> str:
        if auth_type in (AuthTypes.PASSWORD_CREDENTIALS_FLOW.value, AuthTypes.AUTHORIZATION_CODE_FLOW.value):
            expires_delta = datetime.timedelta(minutes=settings.JWT_TOKEN_EXPIRATION_TIME_MIN)
        else:
            expires_delta = datetime.timedelta(minutes=settings.JWT_TOKEN_EXPIRATION_TIME_MAX)

        if hasattr(sub, settings.JWT_SUBJECT):
            sub_obj = getattr(sub, settings.JWT_SUBJECT)
        else:
            raise KeyError(f"{settings.JWT_SUBJECT} not found in {sub}")

        return cls._generate_jwt_token(
            jwt_data=SJwtToken(sub=sub_obj, scopes=scopes).model_dump(),
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
