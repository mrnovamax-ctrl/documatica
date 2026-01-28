"""
API для промокодов
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Promocode, PromocodeUsage
from app.api.auth import get_current_user_db
from app.services.billing import BillingService

router = APIRouter(prefix="/promocodes", tags=["promocodes"])


class ApplyPromocodeRequest(BaseModel):
    code: str


class ApplyPromocodeResponse(BaseModel):
    success: bool
    message: str
    promo_type: Optional[str] = None
    benefit: Optional[str] = None


@router.post("/apply", response_model=ApplyPromocodeResponse)
async def apply_promocode(
    request: ApplyPromocodeRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Применить промокод"""
    code = request.code.strip().upper()
    
    # Ищем промокод
    promocode = db.query(Promocode).filter(
        Promocode.code == code,
        Promocode.is_active == True
    ).first()
    
    if not promocode:
        return ApplyPromocodeResponse(
            success=False,
            message="Промокод не найден или неактивен"
        )
    
    # Проверяем срок действия
    now = datetime.utcnow()
    if promocode.valid_from and now < promocode.valid_from:
        return ApplyPromocodeResponse(
            success=False,
            message="Промокод еще не активен"
        )
    
    if promocode.valid_until and now > promocode.valid_until:
        return ApplyPromocodeResponse(
            success=False,
            message="Срок действия промокода истек"
        )
    
    # Проверяем лимит использований
    if promocode.max_uses and promocode.uses_count >= promocode.max_uses:
        return ApplyPromocodeResponse(
            success=False,
            message="Лимит использований промокода исчерпан"
        )
    
    # Проверяем, не использовал ли пользователь этот промокод
    existing_usage = db.query(PromocodeUsage).filter(
        PromocodeUsage.promocode_id == promocode.id,
        PromocodeUsage.user_id == current_user.id
    ).first()
    
    if existing_usage:
        return ApplyPromocodeResponse(
            success=False,
            message="Вы уже использовали этот промокод"
        )
    
    # Применяем промокод
    billing = BillingService(db)
    benefit = ""
    
    if promocode.promo_type == "subscription":
        # Активируем подписку
        days = promocode.subscription_days or 30
        billing.activate_subscription(current_user, months=days // 30)
        benefit = f"Подписка на {days} дней активирована"
        
    elif promocode.promo_type == "documents":
        # Добавляем документы
        count = promocode.documents_count or 10
        billing.add_purchased_documents(current_user, count)
        benefit = f"Добавлено {count} документов"
    
    # Записываем использование
    usage = PromocodeUsage(
        promocode_id=promocode.id,
        user_id=current_user.id
    )
    db.add(usage)
    
    # Увеличиваем счетчик использований
    promocode.uses_count = (promocode.uses_count or 0) + 1
    
    db.commit()
    
    return ApplyPromocodeResponse(
        success=True,
        message="Промокод успешно применен",
        promo_type=promocode.promo_type,
        benefit=benefit
    )


@router.get("/check/{code}")
async def check_promocode(
    code: str,
    db: Session = Depends(get_db)
):
    """Проверить промокод без применения"""
    code = code.strip().upper()
    
    promocode = db.query(Promocode).filter(
        Promocode.code == code,
        Promocode.is_active == True
    ).first()
    
    if not promocode:
        return {"valid": False, "message": "Промокод не найден"}
    
    now = datetime.utcnow()
    if promocode.valid_until and now > promocode.valid_until:
        return {"valid": False, "message": "Срок действия истек"}
    
    if promocode.max_uses and promocode.uses_count >= promocode.max_uses:
        return {"valid": False, "message": "Лимит исчерпан"}
    
    # Описание бонуса
    benefit = ""
    if promocode.promo_type == "subscription":
        days = promocode.subscription_days or 30
        price = promocode.subscription_price
        if price:
            benefit = f"Подписка на {days} дней за {price} руб"
        else:
            benefit = f"Бесплатная подписка на {days} дней"
    elif promocode.promo_type == "documents":
        benefit = f"{promocode.documents_count} бесплатных документов"
    elif promocode.promo_type == "discount":
        benefit = f"Скидка {promocode.discount_percent}%"
    
    return {
        "valid": True,
        "promo_type": promocode.promo_type,
        "benefit": benefit
    }
