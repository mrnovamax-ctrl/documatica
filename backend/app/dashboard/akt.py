"""
Dashboard - генератор Акта выполненных работ
"""

from datetime import date
from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, get_user_from_request, require_auth

router = APIRouter()


@router.get("/create/", response_class=HTMLResponse)
async def akt_create(request: Request):
    """
    Страница создания Акта выполненных работ
    """
    # Разрешаем гостям заполнять форму
    # Проверка будет при попытке скачать PDF
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/akt/create.html",
        context=get_dashboard_context(
            request=request,
            title="Создать Акт выполненных работ — Documatica",
            active_menu="akt-create",
            today=date.today().isoformat(),
        )
    )


@router.get("/edit/{document_id}/", response_class=HTMLResponse)
async def akt_edit(request: Request, document_id: str = Path(...)):
    """Страница редактирования Акта - использует create.html с предзаполнением"""
    # Проверка авторизации - редактирование только для авторизованных
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/akt/create.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать Акт выполненных работ — Documatica",
            active_menu="akt-create",
            edit_document_id=document_id,
            today=date.today().isoformat(),
        )
    )


@router.get("/{document_id}/", response_class=HTMLResponse)
async def akt_view(request: Request, document_id: str = Path(...)):
    """Страница просмотра Акта выполненных работ"""
    # Проверка авторизации - просмотр только для авторизованных
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/akt/view.html",
        context=get_dashboard_context(
            request=request,
            title="Просмотр Акта выполненных работ — Documatica",
            active_menu="documents",
            document_id=document_id,
        )
    )
