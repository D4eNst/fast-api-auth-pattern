from typing import Optional

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

    @property
    def in_strings(self) -> str:
        return " ".join(self.scopes)


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
    def str(self) -> str:
        return self.__scope

    @property
    def type(self) -> ScopeType:
        return self.__scope_type

    @property
    def detail(self) -> str:
        return self.__detail

    def __str__(self):
        return self.str


class Scopes:
    VIEW_ACCOUNT_DETAILS = ScopeType("Доступ к данным вашего аккаунта")
    USER_DEV = ScopeType("Доступ к инструментам разработчика")

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

    user_dev_read = ScopeInfo(
        "user-dev-read",
        USER_DEV,
        "Данные приложений"
    )
    user_dev_modify = ScopeInfo(
        "user-dev-modify",
        USER_DEV,
        "Изменение приложений"
    )

    @classmethod
    def get_scopes(cls, scope_type: Optional[ScopeType] = None) -> list[ScopeInfo]:
        """Return all scopes. If scope_type is passed, return scopes only for this type"""
        return [scope
                for scope in vars(cls).values()
                if isinstance(scope, ScopeInfo) and (scope_type is None or scope.type == scope_type)]

    @classmethod
    def get_scopes_strings(cls, scope_type: Optional[ScopeType] = None) -> list[str]:
        """Return all scopes in string. If scope_type is passed, return scopes only for this type"""
        return [scope.str
                for scope in vars(cls).values()
                if isinstance(scope, ScopeInfo) and (scope_type is None or scope.type == scope_type)]

    # @classmethod
    # def all_scopes_strings(cls, scope_type: ScopeType) -> list[str]:
    #     return [scope.str
    #             for scope in vars(cls).values()
    #             if isinstance(scope, ScopeInfo) and scope.type == scope_type]

    @classmethod
    def all_types(cls) -> list[ScopeType]:
        return [scope_type
                for scope_type in vars(cls).values()
                if isinstance(scope_type, ScopeType)]

    @classmethod
    def in_string(cls, scope_type: Optional[ScopeType] = None) -> str:
        if scope_type is not None:
            return " ".join(cls.get_scopes_strings(scope_type))
        return " ".join(cls.get_scopes_strings())
