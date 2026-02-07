"""
Pydantic схемы для авторизации
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    smart_token: Optional[str] = None  # Yandex SmartCaptcha token


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    is_verified: bool
    subscription_plan: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class VerifyEmail(BaseModel):
    token: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    success: bool
    message: str
