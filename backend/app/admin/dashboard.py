"""
Admin Dashboard - главная страница со статистикой
"""

from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Payment
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Пути к данным (для документов на диске)
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


def get_statistics(db: Session) -> dict:
    """Получение статистики для дашборда из БД"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    # === Пользователи из БД ===
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Платные аккаунты (с активной подпиской)
    paid_users = db.query(func.count(User.id)).filter(
        User.subscription_plan == "subscription",
        User.subscription_expires > now
    ).scalar() or 0
    
    # Новые пользователи за периоды
    users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar() or 0
    
    users_week = db.query(func.count(User.id)).filter(
        User.created_at >= week_start
    ).scalar() or 0
    
    users_month = db.query(func.count(User.id)).filter(
        User.created_at >= month_start
    ).scalar() or 0
    
    # Верифицированные пользователи
    verified_users = db.query(func.count(User.id)).filter(
        User.is_verified == True
    ).scalar() or 0
    
    # === Документы ===
    # Считаем папки в директории documents
    total_documents = 0
    docs_today = 0
    docs_week = 0
    docs_month = 0
    
    if DOCUMENTS_DIR.exists():
        for doc_folder in DOCUMENTS_DIR.iterdir():
            if doc_folder.is_dir():
                total_documents += 1
                # Проверяем дату создания папки
                try:
                    folder_time = datetime.fromtimestamp(doc_folder.stat().st_ctime)
                    if folder_time >= today_start:
                        docs_today += 1
                    if folder_time >= week_start:
                        docs_week += 1
                    if folder_time >= month_start:
                        docs_month += 1
                except Exception:
                    pass
    
    # === Платежи из БД ===
    total_payments = db.query(func.count(Payment.id)).filter(
        Payment.status == "confirmed"
    ).scalar() or 0
    
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "confirmed"
    ).scalar() or 0
    
    payments_month = db.query(func.count(Payment.id)).filter(
        Payment.status == "confirmed",
        Payment.confirmed_at >= month_start
    ).scalar() or 0
    
    revenue_month = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "confirmed",
        Payment.confirmed_at >= month_start
    ).scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "paid": paid_users,
            "free": total_users - paid_users,
            "verified": verified_users,
            "today": users_today,
            "week": users_week,
            "month": users_month,
        },
        "documents": {
            "total": total_documents,
            "today": docs_today,
            "week": docs_week,
            "month": docs_month,
        },
        "payments": {
            "total_count": total_payments,
            "total_revenue": float(total_revenue) if total_revenue else 0,
            "month_count": payments_month,
            "month_revenue": float(revenue_month) if revenue_month else 0,
        },
        "files_on_disk": total_documents,
    }


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница админки со статистикой"""
    # Проверка авторизации
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    stats = get_statistics(db)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context=get_admin_context(
            request=request,
            title="Статистика — Админ-панель",
            active_menu="dashboard",
            stats=stats,
        )
    )
