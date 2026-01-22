"""
Dashboard - справочник контрагентов
"""

from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def contractors_list(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/contractors/index.html",
        context=get_dashboard_context(
            request=request,
            title="Контрагенты — Documatica",
            active_menu="contractors",
        )
    )


@router.get("/create/", response_class=HTMLResponse)
async def contractor_create(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/contractors/create.html",
        context=get_dashboard_context(
            request=request,
            title="Добавить контрагента — Documatica",
            active_menu="contractors",
        )
    )


@router.get("/edit/{contractor_id}/", response_class=HTMLResponse)
async def contractor_edit(request: Request, contractor_id: str = Path(...)):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/contractors/edit.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать контрагента — Documatica",
            active_menu="contractors",
            contractor_id=contractor_id,
        )
    )
