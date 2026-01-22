"""
Страницы авторизации (SSR)
"""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.database import get_db
from app.models import User

router = APIRouter()


@router.get("/login/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "title": "Вход — Documatica",
        }
    )


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
    
    return templates.TemplateResponse(
        request=request,
        name="auth/verify-result.html",
        context={
            "title": "Email подтверждён — Documatica",
            "success": True,
            "message": "Email успешно подтверждён! Теперь вы можете войти."
        }
    )
