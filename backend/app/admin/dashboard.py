"""
Admin Dashboard - главная страница со статистикой
"""

from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

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
    
    # === Пользователи из БД (один запрос вместо семи) ===
    user_row = db.query(
        func.count(User.id).label("total"),
        func.count(case((and_(
            User.subscription_plan == "subscription",
            User.subscription_expires > now
        ), 1))).label("paid"),
        func.count(case((User.created_at >= today_start, 1))).label("today"),
        func.count(case((User.created_at >= week_start, 1))).label("week"),
        func.count(case((User.created_at >= month_start, 1))).label("month"),
        func.count(case((User.is_verified == True, 1))).label("verified"),
        func.count(case((User.yandex_id.isnot(None), 1))).label("oauth"),
    ).one()
    total_users = user_row.total or 0
    paid_users = user_row.paid or 0
    users_today = user_row.today or 0
    users_week = user_row.week or 0
    users_month = user_row.month or 0
    verified_users = user_row.verified or 0
    oauth_users = user_row.oauth or 0
    
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
    
    # === Платежи из БД (один запрос вместо четырёх) ===
    confirmed = Payment.status == "confirmed"
    payment_row = db.query(
        func.count(Payment.id).label("total_count"),
        func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
        func.count(case((Payment.confirmed_at >= month_start, 1))).label("month_count"),
        func.coalesce(func.sum(case((Payment.confirmed_at >= month_start, Payment.amount))), 0).label("month_revenue"),
    ).filter(confirmed).one()
    total_payments = payment_row.total_count or 0
    total_revenue = float(payment_row.total_revenue or 0)
    payments_month = payment_row.month_count or 0
    revenue_month = float(payment_row.month_revenue or 0)
    
    return {
        "users": {
            "total": total_users,
            "paid": paid_users,
            "free": total_users - paid_users,
            "verified": verified_users,
            "oauth": oauth_users,
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
