"""
Страницы авторизации (SSR)
"""

import os
import jwt

RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.database import get_db, SessionLocal
from app.models import User
from app.services.email import send_welcome_email

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"


def validate_token(token: str) -> bool:
    """Проверяет валидность JWT токена"""
    if not token:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return False
        # Проверяем существование пользователя
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user is not None
        finally:
            db.close()
    except (jwt.PyJWTError, ValueError, TypeError):
        return False


@router.get("/login/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    token = request.cookies.get("access_token")
    
    # Если токен валиден - редирект на dashboard
    if token and validate_token(token):
        return RedirectResponse(url="/dashboard/", status_code=302)
    
    # Если токен невалиден - очищаем cookie и показываем страницу
    response = templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "title": "Вход — Documatica",
            "recaptcha_site_key": RECAPTCHA_SITE_KEY,
        }
    )
    
    # Удаляем невалидный токен из cookie
    if token:
        response.delete_cookie(key="access_token", path="/")
    
    return response


@router.get("/logout/")
async def logout_page(request: Request):
    """Выход из системы - удаляем cookie и редиректим на главную"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token", path="/")
    # Добавляем заголовок для очистки кеша
    response.headers["Clear-Site-Data"] = '"cookies", "storage"'
    return response


@router.get("/clear-session/", response_class=HTMLResponse)
async def clear_session_page(request: Request):
    """Страница для полной очистки сессии и токенов"""
    return templates.TemplateResponse(
        request=request,
        name="auth/clear-session.html",
        context={
            "title": "Очистка сессии — Documatica",
        }
    )


@router.get("/register/", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "title": "Регистрация — Documatica",
        }
    )


@router.get("/forgot-password/", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Страница восстановления пароля"""
    return templates.TemplateResponse(
        request=request,
        name="auth/forgot-password.html",
        context={
            "title": "Восстановление пароля — Documatica",
        }
    )


@router.get("/reset-password/", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None):
    """Страница сброса пароля (ввод нового пароля)"""
    return templates.TemplateResponse(
        request=request,
        name="auth/reset-password.html",
        context={
            "title": "Новый пароль — Documatica",
            "token": token,
        }
    )


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, token: str = None, db: Session = Depends(get_db)):
    """Страница подтверждения email - обрабатывает токен из письма"""
    
    if not token:
        return templates.TemplateResponse(
            request=request,
            name="auth/verify-result.html",
            context={
                "title": "Ошибка подтверждения — Documatica",
                "success": False,
                "message": "Токен не указан"
            }
        )
    
    # Ищем пользователя по токену
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="auth/verify-result.html",
            context={
                "title": "Ошибка подтверждения — Documatica",
                "success": False,
                "message": "Неверный или устаревший токен"
            }
        )
    
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        return templates.TemplateResponse(
            request=request,
            name="auth/verify-result.html",
            context={
                "title": "Ошибка подтверждения — Documatica",
                "success": False,
                "message": "Токен истёк. Запросите новое письмо."
            }
        )
    
    # Подтверждаем email
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    # Отправляем welcome письмо
    send_welcome_email(user.email, user.name)
    
    return templates.TemplateResponse(
        request=request,
        name="auth/verify-result.html",
        context={
            "title": "Email подтверждён — Documatica",
            "success": True,
            "message": "Email успешно подтверждён! Теперь вы можете войти."
        }
    )
