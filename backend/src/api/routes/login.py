import fastapi
from starlette.templating import Jinja2Templates

from src.api.dependencies.repository import get_repository
from src.config.manager import settings
from src.repository.crud.application import ApplicationCRUDRepository

router = fastapi.APIRouter(tags=["login"], )
templates = Jinja2Templates(directory="templates")


@router.get(
    path="/login",
    name="login:page-to-login",
    status_code=fastapi.status.HTTP_200_OK,
)
async def login_page(
        request: fastapi.Request,
        client_id: str = "",
        response_type: str = "",
        redirect_uri: str = "",
        state: str = "",
        scope: str = "",
        code_challenge_method: str = "",
        code_challenge: str = "",
        app_repo: ApplicationCRUDRepository = fastapi.Depends(get_repository(repo_type=ApplicationCRUDRepository))
):
    errors = ""
    query_params = str(request.query_params)
    params = "?" + query_params if query_params else ""

    app = await app_repo.find_by_client_id_or_none(client_id=client_id)
    if app is None:
        return "INVALID_CLIENT: Invalid client"

    is_main_app = "true" if settings.CLIENT_ID == client_id else "false"

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"errors": errors, "next_url": params, "app": app.name, "is_main_app": is_main_app}
    )


# @router.post(
#     path="/login",
#     name="login:login-check-creds",
#     status_code=fastapi.status.HTTP_200_OK,
# )
# async def login_page(
#         request: fastapi.Request,
#         response: fastapi.Response,
#         username: str = Form(),
#         password: str = Form(),
#         account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
#         refresh_session_repo: RefreshCRUDRepository = fastapi.Depends(get_repository(repo_type=RefreshCRUDRepository)),
# ):
#     query_params = str(request.query_params)
#     next_url = "?" + query_params if query_params else ""
#     print("------------------------", next_url)
#     ip = request.client.host
#     # if ip != "127.0.0.1":
#     #     raise fastapi.HTTPException(status_code=400)
#
#     db_account = await account_repo.find_by_username_or_none(username=username)
#     if db_account is None:
#         errors = "?errors=Username or Password is incorrect"
#         return fastapi.responses.RedirectResponse(
#             url='/api/login' + errors,
#             status_code=fastapi.status.HTTP_302_FOUND
#         )
#     if not db_account.is_active:
#         errors = "?errors=Inactive user!"
#         return fastapi.responses.RedirectResponse(
#             url='/api/login' + errors,
#             status_code=fastapi.status.HTTP_302_FOUND)
#
#     is_correct_pwd = pwd_generator.is_password_authenticated(
#         hash_salt=db_account.hash_salt,
#         password=password,
#         hashed_password=db_account.hashed_password
#     )
#     if not is_correct_pwd:
#         errors = "?errors=Username or Password is incorrect"
#         return fastapi.responses.RedirectResponse(
#             url='/api/login' + errors,
#             status_code=fastapi.status.HTTP_302_FOUND
#         )
#     if not next_url:
#         return fastapi.responses.RedirectResponse(
#             '/docs',
#             status_code=fastapi.status.HTTP_302_FOUND)
#
    # return fastapi.responses.RedirectResponse(
    #     '/api/authorize' + next_url,
        # status_code=fastapi.status.HTTP_302_FOUND)
