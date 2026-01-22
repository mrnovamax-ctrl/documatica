"""
Admin Users - управление пользователями
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_users() -> List[Dict[str, Any]]:
    """Загрузка списка пользователей"""
    filepath = DATA_DIR / "users.json"
    if not filepath.exists():
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("users", [])


def get_user_documents_count(user_email: str) -> int:
    """Подсчёт документов пользователя"""
    filepath = DATA_DIR / "documents.json"
    if not filepath.exists():
        return 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    documents = data.get("documents", [])
    return len([d for d in documents if d.get("user_email") == user_email])


@router.get("/", response_class=HTMLResponse)
async def users_list(request: Request, page: int = 1, per_page: int = 50):
    """Список пользователей"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    all_users = load_users()
    
    # Добавляем статистику для каждого пользователя
    users_with_stats = []
    for user in all_users:
        user_copy = user.copy()
        user_copy["documents_count"] = get_user_documents_count(user.get("email", ""))
        users_with_stats.append(user_copy)
    
    # Сортируем по дате регистрации (новые первые)
    users_with_stats.sort(
        key=lambda u: u.get("created_at", ""), 
        reverse=True
    )
    
    # Пагинация
    total = len(users_with_stats)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    users_page = users_with_stats[start:end]
    
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
        )
    )
