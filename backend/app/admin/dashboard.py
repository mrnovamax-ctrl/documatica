"""
Admin Dashboard - главная страница со статистикой
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Пути к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


def load_json(filename: str) -> dict:
    """Загрузка JSON файла"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_statistics() -> dict:
    """Получение статистики для дашборда"""
    # Пользователи
    users_data = load_json("users.json")
    users = users_data.get("users", [])
    total_users = len(users)
    
    # Платные аккаунты (у кого tariff != 'free')
    paid_users = len([u for u in users if u.get("tariff") not in (None, "free", "starter")])
    
    # Документы
    docs_data = load_json("documents.json")
    documents = docs_data.get("documents", [])
    total_documents = len(documents)
    
    # Документы по типам
    doc_types = {}
    for doc in documents:
        doc_type = doc.get("type", "unknown")
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    # Документы за последние периоды
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    docs_today = 0
    docs_week = 0
    docs_month = 0
    
    for doc in documents:
        created_str = doc.get("created_at", "")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                created = created.replace(tzinfo=None)  # Убираем timezone для сравнения
                if created >= today_start:
                    docs_today += 1
                if created >= week_start:
                    docs_week += 1
                if created >= month_start:
                    docs_month += 1
            except Exception:
                pass
    
    # Организации
    orgs_data = load_json("organizations.json")
    # organizations.json может быть списком или объектом с ключом
    if isinstance(orgs_data, list):
        total_orgs = len(orgs_data)
    else:
        total_orgs = len(orgs_data.get("organizations", []))
    
    # Контрагенты
    contractors_data = load_json("contractors.json")
    if isinstance(contractors_data, list):
        total_contractors = len(contractors_data)
    else:
        total_contractors = len(contractors_data.get("contractors", []))
    
    # Товары/услуги
    products_data = load_json("products.json")
    if isinstance(products_data, list):
        total_products = len(products_data)
    else:
        total_products = len(products_data.get("products", []))
    
    # Файлы документов на диске
    total_files = 0
    if DOCUMENTS_DIR.exists():
        total_files = len(list(DOCUMENTS_DIR.glob("*")))
    
    return {
        "users": {
            "total": total_users,
            "paid": paid_users,
            "free": total_users - paid_users,
        },
        "documents": {
            "total": total_documents,
            "today": docs_today,
            "week": docs_week,
            "month": docs_month,
            "by_type": doc_types,
        },
        "organizations": total_orgs,
        "contractors": total_contractors,
        "products": total_products,
        "files_on_disk": total_files,
    }


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Главная страница админки со статистикой"""
    # Проверка авторизации
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    stats = get_statistics()
    
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
