"""
Dashboard - справочник товаров/услуг
"""

from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def products_list(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/products/index.html",
        context=get_dashboard_context(
            request=request,
            title="Товары и услуги — Documatica",
            active_menu="products",
        )
    )


@router.get("/create/", response_class=HTMLResponse)
async def product_create(request: Request):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/products/create.html",
        context=get_dashboard_context(
            request=request,
            title="Добавить товар/услугу — Documatica",
            active_menu="products",
        )
    )


@router.get("/edit/{product_id}/", response_class=HTMLResponse)
async def product_edit(request: Request, product_id: str = Path(...)):
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/products/edit.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать товар/услугу — Documatica",
            active_menu="products",
            product_id=product_id,
        )
    )
