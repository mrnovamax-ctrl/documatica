"""
Модели базы данных
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    name = Column(String(255), nullable=True)
    
    # Статус верификации
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Сброс пароля
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # OAuth провайдеры
    yandex_id = Column(String(100), unique=True, nullable=True, index=True)
    auth_provider = Column(String(50), default="email")  # email, yandex
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Тарифы и лимиты
    subscription_plan = Column(String(50), default="free")  # free, subscription, pay_per_doc
    subscription_expires = Column(DateTime, nullable=True)
    
    # Счётчики использования
    free_generations_used = Column(Integer, default=0)  # Использовано бесплатных генераций (макс 5)
    subscription_docs_used = Column(Integer, default=0)  # Использовано документов по подписке в текущем месяце
    purchased_docs_remaining = Column(Integer, default=0)  # Остаток купленных поштучно документов
    
    # Связи
    inn_usages = relationship("INNUsage", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"


class INNUsage(Base):
    """Отслеживание использования ИНН для защиты от мультиаккаунтности"""
    __tablename__ = "inn_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), index=True, nullable=False)  # ИНН (10 или 12 цифр)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Счётчик бесплатных генераций для этого ИНН (глобально)
    free_generations_count = Column(Integer, default=0)
    
    first_used_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="inn_usages")
    
    def __repr__(self):
        return f"<INNUsage inn={self.inn} user_id={self.user_id}>"


class Payment(Base):
    """История платежей"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Тинькофф данные
    tbank_payment_id = Column(String(100), unique=True, nullable=True)
    tbank_order_id = Column(String(100), unique=True, nullable=False)
    
    # Детали платежа
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма в рублях
    payment_type = Column(String(50), nullable=False)  # subscription, documents
    documents_count = Column(Integer, nullable=True)  # Кол-во документов (для pay_per_doc)
    
    # Статус
    status = Column(String(50), default="pending")  # pending, confirmed, rejected, refunded
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.id} user={self.user_id} amount={self.amount}>"


class GlobalINNLimit(Base):
    """Глобальный лимит по ИНН (независимо от аккаунта)"""
    __tablename__ = "global_inn_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=False)
    free_generations_used = Column(Integer, default=0)  # Сколько бесплатных генераций сделано по этому ИНН
    first_used_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GlobalINNLimit inn={self.inn} used={self.free_generations_used}>"


class Promocode(Base):
    """Промокоды"""
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # Код промокода
    
    # Тип промокода
    promo_type = Column(String(50), nullable=False)  # subscription, discount, documents
    
    # Параметры
    subscription_days = Column(Integer, nullable=True)  # Дней подписки (для subscription)
    subscription_price = Column(Integer, nullable=True)  # Цена подписки по промокоду
    discount_percent = Column(Integer, nullable=True)  # Процент скидки (для discount)
    documents_count = Column(Integer, nullable=True)  # Кол-во документов (для documents)
    
    # Ограничения
    is_active = Column(Boolean, default=True)
    is_reusable = Column(Boolean, default=True)  # Многоразовый (можно на разных аккаунтах)
    max_uses = Column(Integer, nullable=True)  # Макс. использований (null = без лимита)
    uses_count = Column(Integer, default=0)  # Текущее кол-во использований
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Метаданные
    description = Column(String(255), nullable=True)  # Описание для админки
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    usages = relationship("PromocodeUsage", back_populates="promocode")
    
    def __repr__(self):
        return f"<Promocode {self.code} type={self.promo_type}>"


class PromocodeUsage(Base):
    """История использования промокодов"""
    __tablename__ = "promocode_usages"
    
    id = Column(Integer, primary_key=True, index=True)
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    activated_at = Column(DateTime, default=datetime.utcnow)
    
    promocode = relationship("Promocode", back_populates="usages")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PromocodeUsage promo={self.promocode_id} user={self.user_id}>"


class GuestDraft(Base):
    """Черновики документов гостей (неавторизованных пользователей)"""
    __tablename__ = "guest_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_token = Column(String(64), unique=True, index=True, nullable=False)  # Уникальный токен для доступа
    
    # Тип документа
    document_type = Column(String(50), nullable=False)  # upd, akt, invoice
    
    # Данные документа (JSON)
    document_data = Column(Text, nullable=False)
    
    # Связь с пользователем (после регистрации)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Идентификация гостя
    session_id = Column(String(100), nullable=True)  # Для связи с сессией браузера
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    
    # Статус
    is_claimed = Column(Boolean, default=False)  # Привязан к пользователю
    is_converted = Column(Boolean, default=False)  # Сгенерирован PDF
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Когда истечёт (7 дней)
    
    user = relationship("User")
    
    def __repr__(self):
        return f"<GuestDraft {self.draft_token[:8]}... type={self.document_type}>"
