import datetime
import uuid
from calendar import timegm
from uuid import UUID

import pydantic

from src.config.manager import settings


class JWTAccount(pydantic.BaseModel):
    sub: str
    email: pydantic.EmailStr

    class Config:
        from_attributes = True


class SRefreshToken(pydantic.BaseModel):
    refresh_token: uuid.UUID
    grant_type: str = "refresh_token"


class SRefreshSession(pydantic.BaseModel):
    account: int
    ua: str
    ip: str
    expires_in: int = None
    refresh_token: uuid.UUID = None
    # fingerprint: str

    def __init__(self, **data):
        super().__init__(**data)
        if self.expires_in is None:
            now = timegm(datetime.datetime.utcnow().utctimetuple())
            expires_in = datetime.timedelta(minutes=settings.REFRESH_TOKEN_EXPIRATION_TIME).seconds
            self.expires_in = now + expires_in
        if self.refresh_token is None:
            self.refresh_token = uuid.uuid4()


class Tokens(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME * 60
    refresh_token: UUID
