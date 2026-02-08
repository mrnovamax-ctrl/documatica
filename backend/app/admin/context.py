"""
Admin Context - общие функции для админки
"""

import os
import hashlib
from typing import Optional, Any, Dict
from fastapi import Request
from fastapi.responses import RedirectResponse

# Захардкоженные креды админа (в продакшене лучше в .env)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Пароль по умолчанию: documatica2026
# SHA256 hash
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH", 
    "7f8b2dcc138f813802af2c9ccf130f56fad331756541e73315262eb46383ddf7"  # documatica2026
)

# Секретный ключ для подписи токена
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin-secret-key-documatica-2026")


def hash_password(password: str) -> str:
    """Хеширование пароля SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_admin(username: str, password: str) -> bool:
    """Проверка логина и пароля админа"""
    if username != ADMIN_USERNAME:
        return False
    return hash_password(password) == ADMIN_PASSWORD_HASH


def create_admin_token() -> str:
    """Создание простого токена для админа"""
    import time
    import hmac
    timestamp = str(int(time.time()))
    signature = hmac.new(
        ADMIN_SECRET.encode(),
        f"{ADMIN_USERNAME}:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{timestamp}:{signature}"


def verify_admin_token(token: str) -> bool:
    """Проверка токена админа"""
    if not token:
        return False
    try:
        import time
        import hmac
        parts = token.split(":")
        if len(parts) != 2:
            return False
        timestamp, signature = parts
        
        # Проверяем подпись
        expected = hmac.new(
            ADMIN_SECRET.encode(),
            f"{ADMIN_USERNAME}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected:
            return False
        
        # Токен живёт 24 часа
        if int(time.time()) - int(timestamp) > 86400:
            return False
        
        return True
    except Exception:
        return False


def get_admin_from_request(request: Request) -> Optional[str]:
    """Получение админа из cookie"""
    token = request.cookies.get("admin_token")
    if token and verify_admin_token(token):
        return ADMIN_USERNAME
    return None


def require_admin(request: Request) -> Optional[RedirectResponse]:
    """
    Проверка что пользователь - админ.
    Возвращает RedirectResponse если не авторизован, None если всё ок.
    """
    admin = get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/admin/login/", status_code=302)
    return None


def get_admin_context(
    request: Request,
    title: str = "Админ-панель — Documatica",
    active_menu: str = "dashboard",
    **kwargs
) -> Dict[str, Any]:
    """
    Базовый контекст для страниц админки
    """
    admin = get_admin_from_request(request)
    
    return {
        "request": request,
        "title": title,
        "active_menu": active_menu,
        "admin_username": admin,
        "menu_items": [
            {"id": "dashboard", "title": "Статистика", "url": "/admin/", "icon": "ri-dashboard-line"},
            {"id": "pages", "title": "Страницы", "url": "/admin/pages/", "icon": "ri-layout-grid-line"},
            {"section": "Контент"},
            {"id": "articles", "title": "Статьи", "url": "/admin/articles/", "icon": "ri-article-line"},
            {"id": "categories", "title": "Категории статей", "url": "/admin/categories/", "icon": "ri-folder-line"},
            {"id": "hubs", "title": "Хабы", "url": "/admin/hubs/", "icon": "ri-bookmark-line"},
            {"id": "users", "title": "Пользователи", "url": "/admin/users/", "icon": "ri-user-line"},
            {"id": "payments", "title": "Платежи", "url": "/admin/payments/", "icon": "ri-cash-line"},
            {"id": "promocodes", "title": "Промокоды", "url": "/admin/promocodes/", "icon": "ri-price-tag-3-line"},
            {"id": "shortcodes", "title": "Шорткоды", "url": "/admin/shortcodes/", "icon": "ri-code-s-slash-line"},
            {"id": "news_sidebar", "title": "Сайдбар новостей", "url": "/admin/news-sidebar/", "icon": "ri-layout-right-line"},
            {"section": "SEO"},
            {"id": "seo_tools", "title": "SEO-инструменты", "url": "/admin/seo-tools/", "icon": "ri-search-line"},
        ],
        **kwargs
    }
