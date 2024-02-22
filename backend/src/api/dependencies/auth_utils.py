from typing import Optional, Union, Annotated
from typing import Optional, Union, Annotated

from fastapi import HTTPException, Form
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, OAuth2, HTTPBearer
from fastapi.security.http import HTTPBasic
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED


class OAuth2RequestForm:
    def __init__(
            self,
            *,
            grant_type: Annotated[Union[str, None], Form()] = None,
            username: Annotated[Union[str, None], Form()] = None,
            password: Annotated[Union[str, None], Form()] = None,
            client_id: Annotated[Union[str, None], Form()] = None,
            client_secret: Annotated[Union[str, None], Form()] = None,
            code: Annotated[Union[str, None], Form()] = None,
            redirect_uri: Annotated[Union[str, None], Form()] = None,
            code_verifier: Annotated[Union[str, None], Form()] = None,
            scope: Annotated[str, Form()] = "",

    ):
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
        self.code = code
        self.redirect_uri = redirect_uri
        self.code_verifier = code_verifier


class Oauth2ClientCredentials(OAuth2):
    def __init__(
            self,
            tokenUrl: str,
            scheme_name: str = None,
            scopes: dict = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(clientCredentials={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


security = HTTPBasic(scheme_name="client_credentials", description="You can specify client_id and client_secret "
                                                                   "instead of username/password for testing/token "
                                                                   "using Swagger/OpenAPI", auto_error=False)

oauth2_password_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token/",
    scopes={"read": "Read publicly available information", "user": "Permissions available to the user"}
)

oauth2_code_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/api/auth/authorize",
    tokenUrl="/api/auth/token",
    refreshUrl="/refresh",
    scopes={"read": "Read publicly available information", "user": "Permissions available to the user"},
    auto_error=False,
)

oauth2_client_scheme = Oauth2ClientCredentials(
    tokenUrl="/api/auth/token/",
    auto_error=False,
)
