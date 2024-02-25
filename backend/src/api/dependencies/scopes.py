from typing import List

from src.models.db.account import RoleNames


class AccountScopes:
    """
    Scopes class for roles
    """
    def __init__(self, role: str):
        self.role = role

    _ROLE_RELATIONSHIPS = {
        RoleNames.STAFF.value: [RoleNames.STAFF.value],
        RoleNames.DEVELOPER.value: [RoleNames.STAFF.value, RoleNames.DEVELOPER.value],
        RoleNames.ADMIN.value: [RoleNames.STAFF.value, RoleNames.DEVELOPER.value, RoleNames.ADMIN.value],
    }

    @property
    def scopes(self) -> list[str]:
        scopes = self._ROLE_RELATIONSHIPS.get(self.role, [])
        scopes.append(self.role)
        return scopes



class ScopeType:
    def __init__(self, scope_type_descr: str) -> None:
        self.__scope_type_descr = scope_type_descr

    @property
    def descr(self):
        return self.__scope_type_descr

    def __str__(self):
        return self.descr


class ScopeInfo:
    def __init__(self, scope_str: str, scope_type: ScopeType, detail: str) -> None:
        self.__scope = scope_str
        self.__scope_type = scope_type
        self.__detail = detail

    @property
    def scope_str(self) -> str:
        return self.__scope

    @property
    def type(self) -> ScopeType:
        return self.__scope_type

    @property
    def detail(self) -> str:
        return self.__detail

    def __str__(self):
        return self.scope_str


class Scopes:
    VIEW_ACCOUNT_DETAILS = ScopeType("Просматривать данные вашего аккаунта")

    user_read_private = ScopeInfo(
        "user-read-private",
        VIEW_ACCOUNT_DETAILS,
        "Детали аккаунта"
    )
    user_read_email = ScopeInfo(
        "user-read-email",
        VIEW_ACCOUNT_DETAILS,
        "Адрес электронной почты"
    )

    @classmethod
    def all_scopes(cls) -> list[ScopeInfo]:
        return [scope
                for scope in vars(cls).values()
                if isinstance(scope, ScopeInfo)]

    @classmethod
    def all_scopes_strings(cls) -> list[str]:
        return [scope.scope_str
                for scope in vars(cls).values()
                if isinstance(scope, ScopeInfo)]

    @classmethod
    def scopes(cls, scope_type: ScopeType) -> list[str]:
        return [scope.scope_str
                for scope in vars(cls).values()
                if isinstance(scope, ScopeInfo) and scope.type == scope_type]

    @classmethod
    def all_types(cls) -> list[ScopeType]:
        return [scope_type
                for scope_type in vars(cls).values()
                if isinstance(scope_type, ScopeType)]
