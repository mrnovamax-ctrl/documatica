"""
Dashboard - список документов
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def documents_list(request: Request):
    """Список документов пользователя"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/documents/index.html",
        context=get_dashboard_context(
            request=request,
            title="Мои документы — Documatica",
            active_menu="documents",
        )
    )
