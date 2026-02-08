"""
Admin Users - управление пользователями
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import (
    User,
    Payment,
    INNUsage,
    PromocodeUsage,
    Page,
    Redirect,
    Document,
    AnalyticsEvent,
    GuestDraft,
)
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Путь к документам
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


def get_user_documents_count_from_disk(user_id: int) -> int:
    """Подсчёт документов пользователя по папкам на диске"""
    # Документы хранятся в папках с UUID, связь через метаданные
    # Пока возвращаем 0, т.к. нет прямой связи user_id -> document folder
    return 0


@router.get("/", response_class=HTMLResponse)
async def users_list(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    deleted: int = 0,
    db: Session = Depends(get_db),
):
    """Список пользователей из БД"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    # Общее количество пользователей (все, без фильтра)
    total = db.query(func.count(User.id)).scalar() or 0

    # Пагинация
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page

    # Все пользователи: сортировка по id (новые первые), без исключений
    users_db = db.query(User).order_by(desc(User.id)).offset(offset).limit(per_page).all()
    
    # Преобразуем в формат для шаблона
    users_page = []
    now = datetime.utcnow()
    for user in users_db:
        has_active_subscription = (
            user.subscription_plan == "subscription"
            and user.subscription_expires
            and user.subscription_expires > now
        )
        has_package = (user.purchased_docs_remaining or 0) > 0
        if has_active_subscription:
            tariff_status = "subscription"
        elif has_package:
            tariff_status = "pay_per_doc"
        else:
            tariff_status = "free"

        users_page.append({
            "id": user.id,
            "email": user.email or "",
            "name": user.name,
            "phone": user.phone,
            "tariff": tariff_status,
            "subscription_expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
            "is_verified": user.is_verified,
            "auth_provider": getattr(user, 'auth_provider', 'email') or 'email',
            "yandex_id": getattr(user, 'yandex_id', None),
            "created_at": user.created_at.isoformat() if user.created_at else "",
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "free_generations_used": user.free_generations_used or 0,
            "subscription_docs_used": user.subscription_docs_used or 0,
            "purchased_docs_remaining": user.purchased_docs_remaining or 0,
            "documents_count": (user.free_generations_used or 0) + (user.subscription_docs_used or 0),
        })
    
    return templates.TemplateResponse(
        request=request,
        name="admin/users/list.html",
        context=get_admin_context(
            request=request,
            title="Пользователи — Админ-панель",
            active_menu="users",
            users=users_page,
            total_users=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            deleted=deleted,
        )
    )


@router.get("/delete/{user_id}/", response_class=RedirectResponse)
async def user_delete(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
):
    """Удаление пользователя (для очистки от спама)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        db.query(Payment).filter(Payment.user_id == user_id).delete()
        db.query(INNUsage).filter(INNUsage.user_id == user_id).delete()
        db.query(PromocodeUsage).filter(PromocodeUsage.user_id == user_id).delete()
        db.query(Page).filter(Page.created_by_user_id == user_id).update({Page.created_by_user_id: None})
        db.query(Redirect).filter(Redirect.created_by_user_id == user_id).update({Redirect.created_by_user_id: None})
        db.query(Document).filter(Document.user_id == user_id).update({Document.user_id: None})
        db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user_id).update({AnalyticsEvent.user_id: None})
        db.query(GuestDraft).filter(GuestDraft.user_id == user_id).update({GuestDraft.user_id: None})

        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")

    return RedirectResponse(url="/admin/users/?deleted=1", status_code=303)


@router.get("/{user_id}/", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Детальная карточка пользователя"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    has_active_subscription = (
        user.subscription_plan == "subscription"
        and user.subscription_expires
        and user.subscription_expires > now
    )
    has_package = (user.purchased_docs_remaining or 0) > 0
    if has_active_subscription:
        tariff_status = "subscription"
    elif has_package:
        tariff_status = "pay_per_doc"
    else:
        tariff_status = "free"
    user.tariff = tariff_status

    payments = (
        db.query(Payment)
        .filter(Payment.user_id == user.id)
        .order_by(desc(Payment.created_at))
        .all()
    )
    confirmed_payments = [p for p in payments if p.status == "confirmed"]
    total_payments = sum(float(p.amount) for p in confirmed_payments if p.amount)

    return templates.TemplateResponse(
        request=request,
        name="admin/users/detail.html",
        context=get_admin_context(
            request=request,
            title=f"{user.email} — Админ-панель",
            active_menu="users",
            user=user,
            payments=payments,
            confirmed_payments_count=len(confirmed_payments),
            total_payments=total_payments,
        ),
    )
