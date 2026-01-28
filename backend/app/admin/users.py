"""
Admin Users - управление пользователями
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import User
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
async def users_list(request: Request, page: int = 1, per_page: int = 50, db: Session = Depends(get_db)):
    """Список пользователей из БД"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    # Общее количество пользователей
    total = db.query(func.count(User.id)).scalar() or 0
    
    # Пагинация
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page
    
    # Получаем пользователей из БД, сортировка по дате регистрации (новые первые)
    users_db = db.query(User).order_by(desc(User.created_at)).offset(offset).limit(per_page).all()
    
    # Преобразуем в формат для шаблона
    users_page = []
    for user in users_db:
        users_page.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tariff": user.subscription_plan,
            "subscription_expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
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
        )
    )
