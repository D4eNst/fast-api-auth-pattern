import datetime
import enum

import pydantic

from src.models.db.account import RoleNames
from src.models.schemas.base import BaseSchemaModel


class AccountInCreate(BaseSchemaModel):
    username: str
    # firstname: str | None = None
    # lastname: str | None = None
    email: pydantic.EmailStr
    password: str


class AccountInUpdate(BaseSchemaModel):
    username: str | None = None
    # firstname: str | None = None
    # lastname: str | None = None
    email: pydantic.EmailStr | None = None
    password: str | None = None


class AccountDetail(BaseSchemaModel):
    id: int
    username: str
    # firstname: str | None = None
    # lastname: str | None = None
    email: pydantic.EmailStr
    role: enum.Enum
    is_active: bool
    is_logged_in: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


class AccountScopes(BaseSchemaModel):
    role: str

    _ROLE_RELATIONSHIPS = {
        RoleNames.STAFF.value: [RoleNames.STAFF.value],
        RoleNames.DEVELOPER.value: [RoleNames.STAFF.value, RoleNames.DEVELOPER.value],
        RoleNames.ADMIN.value: [RoleNames.STAFF.value, RoleNames.DEVELOPER.value, RoleNames.ADMIN.value],
    }

    def get_scopes(self) -> list[str]:
        scopes = self._ROLE_RELATIONSHIPS.get(self.role, [])
        scopes.append(self.role)
        return scopes
