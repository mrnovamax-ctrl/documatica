"""
Admin Dashboard - главная страница со статистикой
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_

from app.database import get_db
from app.models import User, Payment
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Пути к данным (документы хранятся на диске, не в БД)
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


def _get_docs_stats_from_disk() -> dict:
    """
    Подсчёт документов с диска (папки с metadata.json).
    Document в БД не заполняется при сохранении, поэтому считаем по диску.
    """
    total = 0
    today_count = 0
    week_count = 0
    month_count = 0
    by_day = {}  # дата -> кол-во

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    if not DOCUMENTS_DIR.exists():
        return {"total": 0, "today": 0, "week": 0, "month": 0, "by_day": {}}

    for doc_folder in DOCUMENTS_DIR.iterdir():
        if not doc_folder.is_dir():
            continue
        metadata_path = doc_folder / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        created = data.get("created_at")
        if not created:
            total += 1
            continue
        try:
            if isinstance(created, str) and "T" in created:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            else:
                total += 1
                continue
        except (ValueError, TypeError):
            total += 1
            continue
        total += 1
        if dt >= today_start:
            today_count += 1
        if dt >= week_start:
            week_count += 1
        if dt >= month_start:
            month_count += 1
        day_key = dt.strftime("%Y-%m-%d")
        by_day[day_key] = by_day.get(day_key, 0) + 1

    return {"total": total, "today": today_count, "week": week_count, "month": month_count, "by_day": by_day}


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
    
    # === Документы с диска (папки documents/, Document в БД не заполняется при сохранении) ===
    disk_docs = _get_docs_stats_from_disk()
    total_documents = disk_docs["total"]
    docs_today = disk_docs["today"]
    docs_week = disk_docs["week"]
    docs_month = disk_docs["month"]
    
    # === Платежи: только фактически оплаченные (status=confirmed), без refunded ===
    confirmed = Payment.status == "confirmed"
    pay_date = func.coalesce(Payment.confirmed_at, Payment.created_at)
    payment_row = db.query(
        func.count(Payment.id).label("total_count"),
        func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
        func.count(case((pay_date >= month_start, 1))).label("month_count"),
        func.coalesce(func.sum(case((pay_date >= month_start, Payment.amount))), 0).label("month_revenue"),
    ).filter(confirmed).one()
    total_payments = payment_row.total_count or 0
    total_revenue = float(payment_row.total_revenue or 0)
    payments_month = payment_row.month_count or 0
    revenue_month = float(payment_row.month_revenue or 0)

    # === Динамика за 30 дней (для графиков) ===
    chart_labels = []
    chart_users = []
    chart_docs = []
    chart_revenue = []
    docs_by_day = disk_docs.get("by_day", {})
    for i in range(29, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_key = day_start.strftime("%Y-%m-%d")
        chart_labels.append(day_start.strftime("%d.%m"))
        u = db.query(func.count(User.id)).filter(User.created_at >= day_start, User.created_at < day_end).scalar() or 0
        chart_users.append(int(u))
        d = docs_by_day.get(day_key, 0)
        chart_docs.append(int(d))
        rev = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            confirmed,
            func.coalesce(Payment.confirmed_at, Payment.created_at) >= day_start,
            func.coalesce(Payment.confirmed_at, Payment.created_at) < day_end,
        ).scalar() or 0
        chart_revenue.append(float(rev))

    # === Последние подтверждённые платежи (для таблицы на дашборде) ===
    recent_payments = (
        db.query(Payment)
        .options(joinedload(Payment.user))
        .filter(confirmed)
        .order_by(func.coalesce(Payment.confirmed_at, Payment.created_at).desc())
        .limit(10)
        .all()
    )
    
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
        "chart_labels": chart_labels,
        "chart_users": chart_users,
        "chart_docs": chart_docs,
        "chart_revenue": chart_revenue,
        "recent_payments": recent_payments,
    }


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница админки со статистикой"""
    # Проверка авторизации
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    stats = get_statistics(db)
    stats["chart_labels_json"] = json.dumps(stats["chart_labels"])
    stats["chart_users_json"] = json.dumps(stats["chart_users"])
    stats["chart_docs_json"] = json.dumps(stats["chart_docs"])
    stats["chart_revenue_json"] = json.dumps(stats["chart_revenue"])
    
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
