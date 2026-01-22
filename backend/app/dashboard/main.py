"""
Dashboard - главная страница личного кабинета
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, get_user_from_request

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Главная страница личного кабинета"""
    # Проверка авторизации
    user = get_user_from_request(request)
    if not user.get("is_authenticated"):
        return RedirectResponse(url="/login/", status_code=302)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Личный кабинет — Documatica",
            active_menu="dashboard",
        )
    )
