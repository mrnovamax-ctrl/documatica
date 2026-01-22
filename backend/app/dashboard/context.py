"""
Общий контекст для Dashboard страниц
"""

import os
import jwt
from datetime import datetime
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User

SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"

# Гостевой пользователь
GUEST_USER = {
    "name": "Гость",
    "email": "",
    "initials": "Г",
    "is_authenticated": False,
}


def require_auth(request: Request):
    """
    Проверка авторизации для dashboard страниц.
    Возвращает RedirectResponse если пользователь не авторизован.
    """
    user = get_user_from_request(request)
    if not user.get("is_authenticated"):
        return RedirectResponse(url="/login/", status_code=302)
    return None


def get_user_from_request(request: Request) -> dict:
    """
    Получает пользователя из cookie access_token.
    
    Returns:
        dict с данными пользователя или GUEST_USER
    """
    token = request.cookies.get("access_token")
    
    if not token:
        return GUEST_USER
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            return GUEST_USER
        
        # Конвертируем в int (JWT хранит как строку)
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return GUEST_USER
            
        # Получаем пользователя из БД
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return GUEST_USER
                
            # Формируем инициалы
            name_parts = user.name.split() if user.name else []
            if len(name_parts) >= 2:
                initials = name_parts[0][0].upper() + name_parts[1][0].upper()
            elif len(name_parts) == 1:
                initials = name_parts[0][:2].upper()
            else:
                initials = "??"
                
            return {
                "id": str(user.id),
                "name": user.name or "Пользователь",
                "email": user.email,
                "initials": initials,
                "is_authenticated": True,
            }
        finally:
            db.close()
            
    except jwt.PyJWTError:
        return GUEST_USER


def get_dashboard_context(request: Request = None, **kwargs):
    """
    Возвращает базовый контекст для dashboard страниц.
    
    Args:
        request: FastAPI Request для получения cookie
        **kwargs: Дополнительные переменные контекста
        
    Returns:
        dict: Контекст с user и переданными параметрами
    """
    user = get_user_from_request(request) if request else GUEST_USER
    
    context = {
        "user": user,
        "current_year": datetime.now().year,
    }
    context.update(kwargs)
    return context
