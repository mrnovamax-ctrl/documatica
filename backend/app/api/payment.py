"""
Интеграция с Т-Банком (Тинькофф) Эквайринг API
Документация: https://www.tbank.ru/kassa/dev/payments/
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Payment
from app.api.auth import get_current_user_db
from app.services.billing import BillingService
from app.core.config import settings

router = APIRouter(prefix="/payment", tags=["payment"])

# Тбанк API endpoints
TBANK_API_URL = "https://securepay.tinkoff.ru/v2"
TBANK_TEST_API_URL = "https://rest-api-test.tinkoff.ru/v2"


def is_mock_mode():
    """Проверить, включён ли mock-режим для тестирования"""
    return getattr(settings, 'TBANK_MOCK', False)


def get_api_url():
    """Получить URL API в зависимости от режима"""
    # Используем тестовый режим если не настроен production
    if getattr(settings, 'TBANK_PRODUCTION', False):
        return TBANK_API_URL
    return TBANK_TEST_API_URL


def generate_token(data: dict, password: str) -> str:
    """
    Генерация токена для подписи запроса.
    Алгоритм: 
    1. Добавить Password в словарь
    2. Отсортировать по ключам
    3. Склеить значения в строку
    4. SHA256 хеш
    """
    # Исключаем вложенные объекты и массивы
    filtered = {k: v for k, v in data.items() if not isinstance(v, (dict, list))}
    filtered['Password'] = password
    
    # Сортируем по ключам и склеиваем значения
    sorted_items = sorted(filtered.items())
    concat = ''.join(str(v) for k, v in sorted_items)
    
    # SHA256
    return hashlib.sha256(concat.encode('utf-8')).hexdigest()


class CreatePaymentRequest(BaseModel):
    tariff: str  # "subscription" или "pay_per_doc"
    package_count: Optional[int] = None  # Для pay_per_doc: количество документов


class PaymentResponse(BaseModel):
    success: bool
    payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Создать платёж в Т-Банке"""
    
    terminal_key = getattr(settings, 'TBANK_TERMINAL_KEY', None)
    terminal_password = getattr(settings, 'TBANK_PASSWORD', None)
    
    if not terminal_key or not terminal_password:
        raise HTTPException(status_code=500, detail="Платёжная система не настроена")
    
    # Определяем сумму
    if request.tariff == "subscription":
        amount = 300 * 100  # В копейках
        description = "Подписка Documatica на 1 месяц"
        docs_count = 0
    elif request.tariff == "pay_per_doc":
        if not request.package_count or request.package_count < 1:
            raise HTTPException(status_code=400, detail="Укажите количество документов")
        
        # Скидки на пакеты
        if request.package_count >= 100:
            price_per_doc = 12  # 20% скидка
        elif request.package_count >= 50:
            price_per_doc = 13.5  # 10% скидка
        else:
            price_per_doc = 15
        
        amount = int(request.package_count * price_per_doc * 100)  # В копейках
        description = f"Пакет {request.package_count} документов Documatica"
        docs_count = request.package_count
    else:
        raise HTTPException(status_code=400, detail="Неизвестный тариф")
    
    # Генерируем уникальный order_id
    order_id = str(uuid.uuid4())
    
    # Создаём запись о платеже
    payment = Payment(
        user_id=current_user.id,
        tbank_order_id=order_id,
        amount=amount // 100,  # Храним в рублях
        payment_type=request.tariff,
        documents_count=docs_count if docs_count > 0 else None,
        status="pending"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Mock-режим для тестирования (без реального Тбанка)
    if is_mock_mode():
        payment.tbank_payment_id = f"MOCK-{order_id[:8]}"
        payment.status = "created"
        db.commit()
        
        # В mock-режиме сразу возвращаем URL на страницу успеха
        mock_payment_url = f"{settings.BASE_URL}/dashboard/payment/mock?order_id={order_id}&amount={amount}"
        
        return PaymentResponse(
            success=True,
            payment_id=order_id,
            payment_url=mock_payment_url
        )
    
    # Формируем запрос к Т-Банку
    success_url = f"{settings.BASE_URL}/dashboard/payment/success?order_id={order_id}"
    fail_url = f"{settings.BASE_URL}/dashboard/payment/fail?order_id={order_id}"
    notification_url = f"{settings.BASE_URL}/api/v1/payment/webhook"
    
    init_data = {
        "TerminalKey": terminal_key,
        "Amount": amount,
        "OrderId": order_id,
        "Description": description,
        "SuccessURL": success_url,
        "FailURL": fail_url,
        "NotificationURL": notification_url,
        "DATA": {
            "Email": current_user.email
        },
        "Receipt": {
            "Email": current_user.email,
            "Taxation": "usn_income",  # УСН доходы
            "Items": [
                {
                    "Name": description[:64],  # Максимум 64 символа
                    "Price": amount,
                    "Quantity": 1,
                    "Amount": amount,
                    "PaymentMethod": "full_payment",
                    "PaymentObject": "service",
                    "Tax": "none"  # Без НДС
                }
            ]
        }
    }
    
    # Генерируем токен из ВСЕХ полей первого уровня (кроме вложенных объектов)
    # По документации Т-Банка нужно включать все поля, не только базовые
    init_data["Token"] = generate_token(init_data, terminal_password)
    
    # Логирование для отладки
    print(f"[PAYMENT] T-Bank Init URL: {get_api_url()}/Init")
    print(f"[PAYMENT] T-Bank Init request: {init_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_api_url()}/Init",
                json=init_data,
                timeout=30.0
            )
            # Логирование ответа
            print(f"[PAYMENT] T-Bank Init response status: {response.status_code}")
            print(f"[PAYMENT] T-Bank Init response body: {response.text}")
            
            # Проверяем HTTP статус
            if response.status_code != 200:
                payment.status = "error"
                db.commit()
                raise HTTPException(
                    status_code=502, 
                    detail=f"Платёжная система вернула ошибку HTTP {response.status_code}"
                )
            result = response.json()
    except httpx.HTTPError as e:
        payment.status = "error"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Ошибка соединения с платёжной системой: {str(e)}")
    except json.JSONDecodeError as e:
        payment.status = "error"
        db.commit()
        raise HTTPException(status_code=502, detail="Некорректный ответ от платёжной системы")
    except Exception as e:
        payment.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ошибка платёжной системы: {str(e)}")
    
    if result.get("Success"):
        payment.tbank_payment_id = result.get("PaymentId")
        payment.status = "created"
        db.commit()
        
        return PaymentResponse(
            success=True,
            payment_id=order_id,
            payment_url=result.get("PaymentURL")
        )
    else:
        payment.status = "error"
        db.commit()
        
        return PaymentResponse(
            success=False,
            error=result.get("Message", "Ошибка создания платежа")
        )


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook от Т-Банка о статусе платежа"""
    
    try:
        data = await request.json()
    except:
        return {"error": "Invalid JSON"}
    
    terminal_key = getattr(settings, 'TBANK_TERMINAL_KEY', None)
    terminal_password = getattr(settings, 'TBANK_PASSWORD', None)
    
    if not terminal_key or not terminal_password:
        return {"error": "Not configured"}
    
    # Проверяем токен
    received_token = data.pop("Token", None)
    expected_token = generate_token(data, terminal_password)
    
    if received_token != expected_token:
        return {"error": "Invalid token"}
    
    order_id = data.get("OrderId")
    status = data.get("Status")
    
    if not order_id:
        return {"error": "No OrderId"}
    
    # Находим платёж
    payment = db.query(Payment).filter(Payment.tbank_order_id == order_id).first()
    if not payment:
        return {"error": "Payment not found"}
    
    # Обновляем статус
    old_status = payment.status
    
    if status == "AUTHORIZED":
        payment.status = "authorized"
    elif status == "CONFIRMED":
        payment.status = "confirmed"
        payment.confirmed_at = datetime.utcnow()
        
        # Начисляем пользователю
        if old_status != "confirmed":  # Защита от дублей
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user:
                billing = BillingService(db)
                if payment.payment_type == "subscription":
                    billing.activate_subscription(user, months=1)
                elif payment.payment_type == "pay_per_doc":
                    billing.add_purchased_documents(user, payment.documents_count)
    
    elif status == "REJECTED":
        payment.status = "rejected"
    elif status == "REFUNDED":
        payment.status = "refunded"
    elif status == "CANCELED":
        payment.status = "canceled"
    
    db.commit()
    
    return {"success": True}


class MockConfirmRequest(BaseModel):
    order_id: str
    status: str = "CONFIRMED"


@router.post("/mock-confirm")
async def mock_confirm_payment(
    request: MockConfirmRequest,
    db: Session = Depends(get_db)
):
    """Mock-подтверждение платежа для тестирования"""
    
    if not is_mock_mode():
        raise HTTPException(status_code=403, detail="Mock-режим отключён")
    
    # Находим платёж
    payment = db.query(Payment).filter(Payment.tbank_order_id == request.order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    
    old_status = payment.status
    
    if request.status == "CONFIRMED":
        payment.status = "confirmed"
        payment.confirmed_at = datetime.utcnow()
        
        # Начисляем пользователю
        if old_status != "confirmed":
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user:
                billing = BillingService(db)
                if payment.payment_type == "subscription":
                    billing.activate_subscription(user, months=1)
                elif payment.payment_type == "pay_per_doc":
                    billing.add_purchased_documents(user, payment.documents_count)
    else:
        payment.status = "canceled"
    
    db.commit()
    
    return {"success": True, "status": payment.status}


@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Получить статус платежа"""
    payment = db.query(Payment).filter(
        Payment.tbank_order_id == order_id,
        Payment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    
    return {
        "order_id": payment.tbank_order_id,
        "status": payment.status,
        "amount": float(payment.amount),
        "payment_type": payment.payment_type,
        "documents_count": payment.documents_count,
        "created_at": payment.created_at.isoformat(),
        "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None
    }


@router.get("/history")
async def get_payment_history(
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Получить историю платежей пользователя"""
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).limit(50).all()
    
    return [
        {
            "order_id": p.tbank_order_id,
            "status": p.status,
            "amount": float(p.amount),
            "payment_type": p.payment_type,
            "documents_count": p.documents_count,
            "created_at": p.created_at.isoformat(),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None
        }
        for p in payments
    ]
