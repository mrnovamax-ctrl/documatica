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
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    
    # Статус верификации
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Сброс пароля
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
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
