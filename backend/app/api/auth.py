"""
API endpoints для авторизации
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response, Header, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt

from app.database import get_db
from app.models import User
from app.schemas.auth import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    VerifyEmail, ForgotPassword, ResetPassword, MessageResponse
)
from app.services.email import send_verification_email, send_password_reset_email, send_welcome_email

router = APIRouter()

# Настройки
SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 дней

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("/register", response_model=MessageResponse)
async def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    print(f"[REGISTER] Попытка регистрации: {data.email}")
    
    # Проверяем существование пользователя
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        print(f"[REGISTER] ОТКАЗ: Email {data.email} уже зарегистрирован")
        
        # Разные сообщения в зависимости от статуса верификации
        if existing_user.is_verified:
            # Пользователь подтверждён - предлагаем войти или восстановить пароль
            raise HTTPException(
                status_code=400, 
                detail="Этот email уже зарегистрирован. Войдите в аккаунт или восстановите пароль."
            )
        else:
            # Пользователь не подтвердил email - переотправляем письмо
            verification_token = generate_token()
            verification_expires = datetime.utcnow() + timedelta(hours=24)
            existing_user.verification_token = verification_token
            existing_user.verification_expires = verification_expires
            db.commit()
            
            # Отправляем письмо повторно
            try:
                await send_verification_email(existing_user.email, verification_token)
                print(f"[REGISTER] Повторно отправлено письмо подтверждения на {data.email}")
            except Exception as e:
                print(f"[REGISTER] Ошибка отправки письма: {e}")
            
            raise HTTPException(
                status_code=400, 
                detail="Этот email уже зарегистрирован, но не подтверждён. Мы отправили новое письмо для подтверждения."
            )
    
    # Валидация пароля
    if len(data.password) < 6:
        print(f"[REGISTER] ОТКАЗ: Короткий пароль для {data.email}")
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 6 символов")
    
    # Создаём токен верификации
    verification_token = generate_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Создаём пользователя
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        name=data.name,
        verification_token=verification_token,
        verification_token_expires=verification_expires
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Отправляем письмо подтверждения
    send_verification_email(data.email, verification_token, data.name)
    
    print(f"[REGISTER] УСПЕХ: {data.email} зарегистрирован, ожидает подтверждения email")
    
    # Возвращаем успех без авто-логина (требуется подтверждение email)
    return MessageResponse(
        success=True,
        message="Регистрация успешна! Проверьте почту для подтверждения."
    )



@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Вход в систему"""
    
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    # Проверка для OAuth пользователей
    if user and not user.password_hash:
        raise HTTPException(
            status_code=401, 
            detail="Этот аккаунт создан через Яндекс. Используйте кнопку 'Войти через Яндекс'."
        )
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Проверка подтверждения email
    if not user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Email не подтверждён. Проверьте почту или запросите новое письмо."
        )
    
    # Обновляем время последнего входа
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Создаём токен
    access_token = create_access_token(user.id)
    
    # Устанавливаем cookie для SSR
    # secure=False для локальной разработки (HTTP), True для production (HTTPS)
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,  # Позволяем JS читать для logout
        secure=is_production,  # HTTPS only в production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmail, db: Session = Depends(get_db)):
    """Подтверждение email по токену"""
    
    user = db.query(User).filter(User.verification_token == data.token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или устаревший токен")
    
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Токен истёк. Запросите новое письмо.")
    
    # Подтверждаем email
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    # Отправляем welcome письмо
    send_welcome_email(user.email, user.name)
    
    return MessageResponse(
        success=True,
        message="Email успешно подтверждён! Теперь вы можете войти."
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(data: ForgotPassword, db: Session = Depends(get_db)):
    """Повторная отправка письма подтверждения"""
    
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if not user:
        # Не раскрываем информацию о существовании пользователя
        return MessageResponse(
            success=True,
            message="Если email зарегистрирован, письмо будет отправлено."
        )
    
    if user.is_verified:
        return MessageResponse(
            success=True,
            message="Email уже подтверждён. Вы можете войти."
        )
    
    # Генерируем новый токен
    verification_token = generate_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # Отправляем письмо
    send_verification_email(user.email, verification_token, user.name)
    
    return MessageResponse(
        success=True,
        message="Письмо отправлено! Проверьте почту."
    )


@router.post("/update-email", response_model=MessageResponse)
async def update_email_before_verification(
    data: dict,
    db: Session = Depends(get_db)
):
    """Изменение email до подтверждения (для регистрации)"""
    
    old_email = data.get("old_email", "").lower()
    new_email = data.get("new_email", "").lower()
    
    if not old_email or not new_email:
        raise HTTPException(status_code=400, detail="Укажите оба email адреса")
    
    if old_email == new_email:
        raise HTTPException(status_code=400, detail="Новый email совпадает со старым")
    
    # Находим пользователя по старому email
    user = db.query(User).filter(User.email == old_email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email уже подтверждён, изменение невозможно")
    
    # Проверяем, не занят ли новый email
    existing = db.query(User).filter(User.email == new_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован")
    
    # Обновляем email и генерируем новый токен
    verification_token = generate_token()
    user.email = new_email
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # Отправляем письмо на новый email
    send_verification_email(new_email, verification_token, user.name)
    
    return MessageResponse(
        success=True,
        message="Email обновлён, письмо отправлено на новый адрес."
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """Запрос на сброс пароля"""
    
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if not user:
        # Не раскрываем информацию о существовании пользователя
        return MessageResponse(
            success=True,
            message="Если email зарегистрирован, письмо будет отправлено."
        )
    
    # Генерируем токен сброса
    reset_token = generate_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Отправляем письмо
    send_password_reset_email(user.email, reset_token)
    
    return MessageResponse(
        success=True,
        message="Письмо с инструкциями отправлено на указанный email."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Сброс пароля по токену"""
    
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или устаревший токен")
    
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Токен истёк. Запросите сброс пароля заново.")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 6 символов")
    
    # Обновляем пароль
    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return MessageResponse(
        success=True,
        message="Пароль успешно изменён! Теперь вы можете войти."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Получить текущего пользователя по токену"""
    
    token = None
    
    # Сначала пробуем Header Authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Если нет Header, берём из cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserResponse.model_validate(user)

async def get_current_user_db(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя (SQLAlchemy модель) для внутреннего использования"""
    
    token = None
    
    # Сначала пробуем Header Authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Если нет Header, берём из cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Получить текущего пользователя или None если не авторизован.
    Используется для эндпоинтов где авторизация опциональна.
    """
    
    token = None
    
    # Сначала пробуем Header Authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Если нет Header, берём из cookie
    elif access_token:
        token = access_token
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user