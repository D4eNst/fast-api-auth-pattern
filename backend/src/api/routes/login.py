import fastapi
from starlette.templating import Jinja2Templates

from src.api.dependencies.repository import get_repository
from src.api.dependencies.scopes import Scopes
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
    # TODO SAME REFRESH SESSION COOKIES
    ans_list_scopes = {scope_type.descr: [sc.detail
                                          for sc in Scopes.all_scopes()
                                          if sc.scope_str in (scope.split() if scope else [])]
                       for scope_type in Scopes.all_types()}

    ans_list_scopes[Scopes.VIEW_ACCOUNT_DETAILS.descr].append('Публичные данные аккаунта')

    question_user = ""
    for key, value in ans_list_scopes.items():
        if value:
            question_user += key + "\n"
            for item in value:
                question_user += f"  - {item}"
                question_user += "\n"

    errors = ""
    query_params = str(request.query_params)
    params = "?" + query_params if query_params else ""
    if not redirect_uri:
        q = f"client_id={settings.CLIENT_ID + '&' if not client_id else ''}redirect_uri=http://127.0.0.1:8000/docs"
        params += f"&{q}" if params else f"?{q}"

    if not client_id:
        client_id = settings.CLIENT_ID
    is_main_app = "true" if settings.CLIENT_ID == client_id else "false"

    app = None
    if is_main_app == "false":
        app = await app_repo.find_by_client_id_or_none(client_id=client_id)
        if app is None:
            return "INVALID_CLIENT: Invalid client"

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "errors": errors,
            "next_url": params,
            "app": app.name if app else "",
            "is_main_app": is_main_app,
            "question_user": question_user,
        }
    )
