"""
Dashboard - справочник организаций
"""

from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def organizations_list(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/organizations/index.html",
        context=get_dashboard_context(
            request=request,
            title="Мои организации — Documatica",
            active_menu="organizations",
        )
    )


@router.get("/create/", response_class=HTMLResponse)
async def organization_create(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/organizations/create.html",
        context=get_dashboard_context(
            request=request,
            title="Добавить организацию — Documatica",
            active_menu="organizations",
        )
    )


@router.get("/edit/{org_id}/", response_class=HTMLResponse)
async def organization_edit(request: Request, org_id: str = Path(...)):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/organizations/edit.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать организацию — Documatica",
            active_menu="organizations",
            org_id=org_id,
        )
    )
