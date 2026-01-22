"""
Сервис биллинга и проверки лимитов
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models import User, INNUsage, GlobalINNLimit, Payment

# Константы тарифов
FREE_GENERATIONS_LIMIT = 5  # Бесплатных генераций на аккаунт
FREE_INN_LIMIT = 5  # Бесплатных генераций на ИНН (глобально)
SUBSCRIPTION_DOCS_LIMIT = 50  # Документов в месяц по подписке
SUBSCRIPTION_PRICE = 300  # Рублей в месяц
DOCUMENT_PRICE = 15  # Рублей за документ


class BillingService:
    """Сервис проверки лимитов и списания документов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_limits(self, user: User) -> dict:
        """Получить информацию о лимитах пользователя"""
        
        now = datetime.utcnow()
        
        # Проверяем активность подписки
        subscription_active = False
        subscription_days_left = 0
        if user.subscription_plan == "subscription" and user.subscription_expires:
            if user.subscription_expires > now:
                subscription_active = True
                subscription_days_left = (user.subscription_expires - now).days
        
        return {
            "plan": user.subscription_plan,
            "subscription_active": subscription_active,
            "subscription_expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
            "subscription_days_left": subscription_days_left,
            
            # Бесплатные генерации
            "free_generations_used": user.free_generations_used or 0,
            "free_generations_limit": FREE_GENERATIONS_LIMIT,
            "free_generations_remaining": max(0, FREE_GENERATIONS_LIMIT - (user.free_generations_used or 0)),
            
            # Подписка
            "subscription_docs_used": user.subscription_docs_used or 0,
            "subscription_docs_limit": SUBSCRIPTION_DOCS_LIMIT,
            "subscription_docs_remaining": max(0, SUBSCRIPTION_DOCS_LIMIT - (user.subscription_docs_used or 0)) if subscription_active else 0,
            
            # Купленные документы
            "purchased_docs_remaining": user.purchased_docs_remaining or 0,
            
            # Общий остаток
            "can_generate": self._can_generate(user)[0],
        }
    
    def _can_generate(self, user: User, seller_inn: str = None) -> Tuple[bool, str]:
        """
        Проверить, может ли пользователь генерировать документ.
        Возвращает (can_generate, reason)
        """
        now = datetime.utcnow()
        
        # 1. Проверяем подписку
        if user.subscription_plan == "subscription":
            if user.subscription_expires and user.subscription_expires > now:
                if (user.subscription_docs_used or 0) < SUBSCRIPTION_DOCS_LIMIT:
                    return True, "subscription"
        
        # 2. Проверяем купленные документы
        if (user.purchased_docs_remaining or 0) > 0:
            return True, "purchased"
        
        # 3. Проверяем бесплатные генерации аккаунта
        if (user.free_generations_used or 0) < FREE_GENERATIONS_LIMIT:
            # Проверяем глобальный лимит по ИНН (если указан)
            if seller_inn:
                inn_limit = self.get_global_inn_usage(seller_inn)
                if inn_limit >= FREE_INN_LIMIT:
                    return False, "inn_limit_exceeded"
            return True, "free"
        
        return False, "no_limit"
    
    def check_can_generate(self, user: User, seller_inn: str = None) -> dict:
        """Проверить возможность генерации и вернуть детальную информацию"""
        can_generate, reason = self._can_generate(user, seller_inn)
        
        messages = {
            "subscription": "Документ будет создан по подписке",
            "purchased": "Документ будет создан из купленного пакета",
            "free": "Документ будет создан бесплатно",
            "inn_limit_exceeded": "Превышен лимит бесплатных генераций для этого ИНН. Оформите подписку или купите документы.",
            "no_limit": "Исчерпаны бесплатные генерации. Оформите подписку или купите документы."
        }
        
        return {
            "can_generate": can_generate,
            "reason": reason,
            "message": messages.get(reason, "Неизвестная ошибка"),
            "limits": self.get_user_limits(user)
        }
    
    def consume_generation(self, user: User, seller_inn: str) -> Tuple[bool, str]:
        """
        Списать генерацию документа.
        Возвращает (success, source) - источник списания
        """
        now = datetime.utcnow()
        
        # 1. Сначала пробуем подписку
        if user.subscription_plan == "subscription":
            if user.subscription_expires and user.subscription_expires > now:
                if (user.subscription_docs_used or 0) < SUBSCRIPTION_DOCS_LIMIT:
                    user.subscription_docs_used = (user.subscription_docs_used or 0) + 1
                    self.db.commit()
                    return True, "subscription"
        
        # 2. Затем купленные документы
        if (user.purchased_docs_remaining or 0) > 0:
            user.purchased_docs_remaining -= 1
            self.db.commit()
            return True, "purchased"
        
        # 3. Бесплатные генерации
        if (user.free_generations_used or 0) < FREE_GENERATIONS_LIMIT:
            # Проверяем глобальный лимит ИНН
            inn_usage = self.get_global_inn_usage(seller_inn)
            if inn_usage >= FREE_INN_LIMIT:
                return False, "inn_limit_exceeded"
            
            # Списываем бесплатную генерацию
            user.free_generations_used = (user.free_generations_used or 0) + 1
            self._increment_inn_usage(user.id, seller_inn)
            self.db.commit()
            return True, "free"
        
        return False, "no_limit"
    
    def get_global_inn_usage(self, inn: str) -> int:
        """Получить количество бесплатных генераций по ИНН (глобально)"""
        record = self.db.query(GlobalINNLimit).filter(GlobalINNLimit.inn == inn).first()
        return record.free_generations_used if record else 0
    
    def _increment_inn_usage(self, user_id: int, inn: str):
        """Увеличить счётчик использования ИНН"""
        # Глобальный счётчик
        global_record = self.db.query(GlobalINNLimit).filter(GlobalINNLimit.inn == inn).first()
        if global_record:
            global_record.free_generations_used += 1
            global_record.last_used_at = datetime.utcnow()
        else:
            global_record = GlobalINNLimit(inn=inn, free_generations_used=1)
            self.db.add(global_record)
        
        # Связь пользователь-ИНН
        user_inn = self.db.query(INNUsage).filter(
            INNUsage.user_id == user_id,
            INNUsage.inn == inn
        ).first()
        
        if user_inn:
            user_inn.free_generations_count += 1
            user_inn.last_used_at = datetime.utcnow()
        else:
            user_inn = INNUsage(
                user_id=user_id,
                inn=inn,
                free_generations_count=1
            )
            self.db.add(user_inn)
    
    def activate_subscription(self, user: User, months: int = 1):
        """Активировать подписку"""
        now = datetime.utcnow()
        
        # Если подписка уже есть, продлеваем
        if user.subscription_expires and user.subscription_expires > now:
            user.subscription_expires += timedelta(days=30 * months)
        else:
            user.subscription_expires = now + timedelta(days=30 * months)
            user.subscription_docs_used = 0  # Сбрасываем счётчик
        
        user.subscription_plan = "subscription"
        self.db.commit()
    
    def add_purchased_documents(self, user: User, count: int):
        """Добавить купленные документы"""
        user.purchased_docs_remaining = (user.purchased_docs_remaining or 0) + count
        if user.subscription_plan == "free":
            user.subscription_plan = "pay_per_doc"
        self.db.commit()
    
    def reset_monthly_subscription_usage(self, user: User):
        """Сбросить месячный счётчик подписки (вызывается cron'ом или при обновлении подписки)"""
        user.subscription_docs_used = 0
        self.db.commit()
