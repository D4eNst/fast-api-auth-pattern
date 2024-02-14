import datetime
from calendar import timegm

import pydantic
from jose import jwt as jose_jwt, JWTError, ExpiredSignatureError

from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.jwt import JWTAccount
from src.utilities.exceptions.database import EntityDoesNotExist


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
            expire = issued_at + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME).seconds

        to_encode.update(
            iat=issued_at,
            exp=expire,
        )

        return jose_jwt.encode(to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def generate_access_token(self, account: Account) -> str:
        if not account:
            raise EntityDoesNotExist(f"Cannot generate JWT token for without Account entity!")

        sub_obj = getattr(account, settings.JWT_SUBJECT)
        setattr(account, "sub", sub_obj)
        return self._generate_jwt_token(
            jwt_data=JWTAccount.model_validate(account).model_dump(),
            expires_delta=datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME),
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
