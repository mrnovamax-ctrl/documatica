"""
Dashboard - генератор УПД
"""

from datetime import date
from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, get_user_from_request, require_auth

router = APIRouter()


@router.get("/create/", response_class=HTMLResponse)
async def upd_create(request: Request, preset: Optional[str] = None):
    """
    Страница создания УПД
    
    Args:
        preset: Пресет для автозаполнения (ooo, ip, samozanyatye, s-nds, bez-nds, usn)
    """
    # УБИРАЕМ проверку авторизации - разрешаем гостям заполнять форму
    # Проверка будет при попытке скачать PDF
    
    # Определяем настройки по пресету
    preset_config = {
        "ooo": {"org_type": "ooo", "has_nds": True},
        "ip": {"org_type": "ip", "has_nds": False},
        "samozanyatye": {"org_type": "samozanyatye", "has_nds": False},
        "s-nds": {"has_nds": True},
        "bez-nds": {"has_nds": False},
        "usn": {"org_type": "ip", "has_nds": False, "tax_system": "usn"},
    }
    
    config = preset_config.get(preset, {})
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/upd/create.html",
        context=get_dashboard_context(
            request=request,
            title="Создать УПД — Documatica",
            active_menu="upd-create",
            preset=preset,
            config=config,
            today=date.today().isoformat(),
        )
    )


@router.get("/edit/{document_id}/", response_class=HTMLResponse)
async def upd_edit(request: Request, document_id: str = Path(...)):
    """Страница редактирования УПД - использует create.html с предзаполнением"""
    # Проверка авторизации - редактирование только для авторизованных
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/upd/create.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать УПД — Documatica",
            active_menu="upd-create",
            edit_document_id=document_id,
            today=date.today().isoformat(),
        )
    )


@router.get("/{document_id}/", response_class=HTMLResponse)
async def upd_view(request: Request, document_id: str = Path(...)):
    """Страница просмотра УПД"""
    # Проверка авторизации - просмотр только для авторизованных
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/upd/view.html",
        context=get_dashboard_context(
            request=request,
            title="Просмотр УПД — Documatica",
            active_menu="documents",
            document_id=document_id,
        )
    )
