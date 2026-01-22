"""
Dashboard - Страница тарифов и оплаты
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def tariffs_page(request: Request, db: Session = Depends(get_db)):
    """Страница тарифов и оплаты"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/tariffs/index_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Тарифы — Documatica",
            active_menu="tariffs",
        )
    )


@router.get("/success", response_class=HTMLResponse)
async def payment_success_page(request: Request, order_id: str = None, db: Session = Depends(get_db)):
    """Страница успешной оплаты"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/tariffs/success_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Оплата успешна — Documatica",
            active_menu="tariffs",
            order_id=order_id,
        )
    )


@router.get("/fail", response_class=HTMLResponse)
async def payment_fail_page(request: Request, order_id: str = None, db: Session = Depends(get_db)):
    """Страница ошибки оплаты"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/tariffs/fail_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Ошибка оплаты — Documatica",
            active_menu="tariffs",
            order_id=order_id,
        )
    )


@router.get("/mock", response_class=HTMLResponse)
async def payment_mock_page(request: Request, order_id: str = None, amount: int = None, db: Session = Depends(get_db)):
    """Mock-страница оплаты для тестирования"""
    return templates.TemplateResponse(
        request=request,
        name="dashboard/tariffs/mock_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Тестовая оплата — Documatica",
            active_menu="tariffs",
            order_id=order_id,
            amount=amount // 100 if amount else 0,  # Из копеек в рубли
        )
    )
