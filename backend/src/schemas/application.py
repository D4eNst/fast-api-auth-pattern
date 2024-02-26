from functools import partial
from typing import Optional

from passlib.pwd import genword
from pydantic import Field, EmailStr

from src.schemas.base import BaseSchemaModel


class SApplicationUser(BaseSchemaModel):
    id: int
    application_id: int
    fullname: str
    email: EmailStr


class SApplicationUserCreate(BaseSchemaModel):
    fullname: str
    email: EmailStr


class SApplicationUserUpdate(BaseSchemaModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None


class SApplication(BaseSchemaModel):
    user: int
    name: str
    description: str = ""
    website: str
    redirect_uris: list[str]
    mode: str = 'dev'
    client_id: str = Field(default_factory=partial(genword, entropy=64, length=32))
    client_secret: str = Field(default_factory=partial(genword, entropy=64, length=32))


class SApplicationAns(BaseSchemaModel):
    user: int
    name: str
    description: str = ""
    website: str
    mode: str = 'dev'
    client_id: str = Field(default_factory=partial(genword, entropy=64, length=32))


class SApplicationCreate(BaseSchemaModel):
    name: str
    description: str = ""
    website: str
    redirect_uris: list[str]


class SApplicationUpdate(BaseSchemaModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    redirect_uris: Optional[list[str]] = None
