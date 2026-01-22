"""
API для биллинга и тарифов
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User
from app.api.auth import get_current_user_db
from app.services.billing import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckGenerationRequest(BaseModel):
    seller_inn: str


class CheckGenerationResponse(BaseModel):
    can_generate: bool
    reason: str
    message: str
    limits: dict


@router.get("/limits")
async def get_limits(
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Получить текущие лимиты пользователя"""
    billing = BillingService(db)
    return billing.get_user_limits(current_user)


@router.post("/check", response_model=CheckGenerationResponse)
async def check_can_generate(
    request: CheckGenerationRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Проверить, может ли пользователь создать документ для указанного ИНН"""
    billing = BillingService(db)
    return billing.check_can_generate(current_user, request.seller_inn)


@router.get("/inn/{inn}")
async def check_inn_usage(
    inn: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Проверить использование бесплатных генераций для ИНН"""
    billing = BillingService(db)
    usage = billing.get_global_inn_usage(inn)
    return {
        "inn": inn,
        "free_generations_used": usage,
        "free_generations_limit": 5,
        "free_generations_remaining": max(0, 5 - usage)
    }


# Модели для тарифов
class TariffInfo(BaseModel):
    id: str
    name: str
    price: int
    description: str
    features: list


@router.get("/tariffs")
async def get_tariffs():
    """Получить список доступных тарифов"""
    return [
        {
            "id": "free",
            "name": "Бесплатный",
            "price": 0,
            "description": "5 бесплатных генераций документов",
            "features": [
                "5 документов бесплатно",
                "Все типы УПД",
                "Скачивание в PDF и Excel",
                "Ограничение по ИНН (5 документов на ИНН)"
            ]
        },
        {
            "id": "subscription",
            "name": "Подписка",
            "price": 300,
            "period": "месяц",
            "description": "50 документов в месяц",
            "features": [
                "50 документов в месяц",
                "Все типы УПД",
                "Приоритетная поддержка",
                "Без ограничений по ИНН",
                "История документов"
            ],
            "popular": True
        },
        {
            "id": "pay_per_doc",
            "name": "Пакет документов",
            "price": 15,
            "period": "за документ",
            "description": "Платите только за то, что используете",
            "features": [
                "Без срока действия",
                "Все типы УПД",
                "Скачивание в PDF и Excel",
                "Покупайте любое количество"
            ],
            "packages": [
                {"count": 10, "price": 150, "discount": 0},
                {"count": 50, "price": 675, "discount": 10},
                {"count": 100, "price": 1200, "discount": 20}
            ]
        }
    ]
