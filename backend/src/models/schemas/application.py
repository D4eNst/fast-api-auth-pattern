from functools import partial

from passlib.pwd import genword
from pydantic import Field, EmailStr

from src.models.schemas.base import BaseSchemaModel


class SApplicationUser(BaseSchemaModel):
    application_id: int
    fullname: str
    email: EmailStr


class SApplication(BaseSchemaModel):
    user: int
    name: str
    description: str = ""
    website: str
    redirect_uris: list[str]
    # allowed_users: list[SApplicationUser] = Field(default_factory=list)
    mode: str = 'dev'
    client_id: str = Field(default_factory=partial(genword, entropy=64, length=32))
    client_secret: str = Field(default_factory=partial(genword, entropy=64, length=32))

    # def __init__(self, **data):
    #     super().__init__(**data)
    #     if self.client_id is None:
    #         self.client_id = genword(entropy=64, length=32)
    #     if self.client_secret is None:
    #         client_secret = genword(entropy=64, length=32)
    #         self.client_secret = genword(entropy=64, length=32)
