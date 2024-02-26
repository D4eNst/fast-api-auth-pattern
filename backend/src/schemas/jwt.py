import datetime
import uuid
from calendar import timegm
from uuid import UUID

import pydantic
from pydantic import Field

from src.config.manager import settings


class SJwtToken(pydantic.BaseModel):
    sub: str
    scopes: list

    class Config:
        from_attributes = True


def exp_in_func():
    now = timegm(datetime.datetime.utcnow().utctimetuple())
    expires_in = datetime.timedelta(minutes=settings.REFRESH_TOKEN_EXPIRATION_TIME).seconds
    return now + expires_in


class SRefreshSession(pydantic.BaseModel):
    account: int
    ua: str
    ip: str
    scope: str = ""
    expires_in: int = Field(default_factory=exp_in_func)
    refresh_token: uuid.UUID = Field(default_factory=uuid.uuid4)
    #
    # def __init__(self, **data):
    #     super().__init__(**data)
    #     if self.expires_in is None:
    #         ...
    #     if self.refresh_token is None:
    #         self.refresh_token = uuid.uuid4()


class Tokens(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: UUID | None
    scope: str | None
