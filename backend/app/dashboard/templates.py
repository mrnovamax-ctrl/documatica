"""
Dashboard - шаблоны документов
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def templates_list(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/templates/index.html",
        context=get_dashboard_context(
            request=request,
            title="Мои шаблоны — Documatica",
            active_menu="templates",
        )
    )
