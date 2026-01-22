"""
Pydantic схемы для организаций и контрагентов
"""

from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import uuid


class SignerData(BaseModel):
    """Данные подписанта"""
    position: Optional[str] = Field(None, description="Должность")
    full_name: Optional[str] = Field(None, description="ФИО")
    signature_base64: Optional[str] = Field(None, description="Подпись (base64)")


class OrganizationBase(BaseModel):
    """Базовые поля организации"""
    org_type: Literal["ooo", "ip"] = Field("ooo", description="Тип организации: ooo или ip")
    name: str = Field("", description="Название организации / ФИО ИП")
    inn: str = Field("", description="ИНН")
    kpp: Optional[str] = Field(None, description="КПП (только для ООО)")
    ogrn: Optional[str] = Field(None, description="ОГРН / ОГРНИП")
    address: str = Field("", description="Юридический адрес")
    vat_type: str = Field("20", description="Ставка НДС по умолчанию")
    
    # Банковские реквизиты
    bank_name: Optional[str] = Field(None, description="Название банка")
    bank_bik: Optional[str] = Field(None, description="БИК банка")
    bank_account: Optional[str] = Field(None, description="Расчетный счет")
    bank_corr_account: Optional[str] = Field(None, description="Корр. счет")
    
    # Для ИП
    certificate_number: Optional[str] = Field(None, description="Номер свидетельства (для ИП)")
    certificate_date: Optional[date] = Field(None, description="Дата выдачи свидетельства (для ИП)")
    
    # Руководитель
    director: Optional[str] = Field(None, description="ФИО руководителя")
    director_name: Optional[str] = Field(None, description="ФИО руководителя (alias)")
    director_signature: Optional[str] = Field(None, description="Подпись руководителя (base64)")
    
    # Логотип
    logo_url: Optional[str] = Field(None, description="URL логотипа организации")
    
    # Печать
    stamp_base64: Optional[str] = Field(None, description="Печать организации (base64)")
    
    # Главный бухгалтер
    accountant_name: Optional[str] = Field(None, description="ФИО главного бухгалтера")
    accountant_signature: Optional[str] = Field(None, description="Подпись бухгалтера (base64)")
    
    # Ответственный за правильность оформления
    responsible_position: Optional[str] = Field(None, description="Должность ответственного")
    responsible_name: Optional[str] = Field(None, description="ФИО ответственного")
    responsible_signature: Optional[str] = Field(None, description="Подпись ответственного (base64)")
    
    # Товар передал
    transfer_position: Optional[str] = Field(None, description="Должность - кто передаёт товар")
    transfer_name: Optional[str] = Field(None, description="ФИО - кто передаёт товар")
    transfer_signature: Optional[str] = Field(None, description="Подпись передающего (base64)")
    
    # Наименование экономического субъекта
    economic_entity: Optional[str] = Field(None, description="Наименование экономического субъекта")


class OrganizationCreate(OrganizationBase):
    """Создание организации"""
    pass


class OrganizationUpdate(BaseModel):
    """Обновление организации (все поля опциональны)"""
    org_type: Optional[Literal["ooo", "ip"]] = None
    name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    address: Optional[str] = None
    vat_type: Optional[str] = None
    bank_name: Optional[str] = None
    bank_bik: Optional[str] = None
    bank_account: Optional[str] = None
    bank_corr_account: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_date: Optional[date] = None
    director: Optional[str] = None
    director_name: Optional[str] = None
    director_signature: Optional[str] = None
    logo_url: Optional[str] = None
    stamp_base64: Optional[str] = None
    accountant_name: Optional[str] = None
    accountant_signature: Optional[str] = None
    responsible_position: Optional[str] = None
    responsible_name: Optional[str] = None
    responsible_signature: Optional[str] = None
    transfer_position: Optional[str] = None
    transfer_name: Optional[str] = None
    transfer_signature: Optional[str] = None
    economic_entity: Optional[str] = None


class Organization(OrganizationBase):
    """Организация с ID"""
    id: str = Field(..., description="Уникальный ID организации")
    created_at: str = Field(..., description="Дата создания")
    updated_at: str = Field(..., description="Дата обновления")


class ContractorBase(BaseModel):
    """Базовые поля контрагента (клиента)"""
    org_type: Literal["ooo", "ip"] = Field("ooo", description="Тип: ooo или ip")
    name: str = Field("", description="Название организации / ФИО ИП")
    inn: str = Field("", description="ИНН")
    kpp: Optional[str] = Field(None, description="КПП (только для ООО)")
    ogrn: Optional[str] = Field(None, description="ОГРН / ОГРНИП")
    address: str = Field("", description="Юридический адрес")
    
    # Логотип
    logo_url: Optional[str] = Field(None, description="URL логотипа контрагента")
    
    # Руководитель
    director: Optional[str] = Field(None, description="ФИО руководителя")
    
    # Банковские реквизиты
    bank_name: Optional[str] = Field(None, description="Наименование банка")
    bank_bik: Optional[str] = Field(None, description="БИК банка")
    bank_account: Optional[str] = Field(None, description="Расчетный счет")
    bank_corr_account: Optional[str] = Field(None, description="Корреспондентский счет")
    
    # Контактные данные
    phone: Optional[str] = Field(None, description="Телефон")
    email: Optional[str] = Field(None, description="Email")
    contact_person: Optional[str] = Field(None, description="Контактное лицо")
    
    # Для подписи документов со стороны покупателя
    receiver_position: Optional[str] = Field(None, description="Должность получателя товара")
    receiver_name: Optional[str] = Field(None, description="ФИО получателя товара")
    
    # Ответственный за правильность оформления (покупатель)
    responsible_position: Optional[str] = Field(None, description="Должность ответственного")
    responsible_name: Optional[str] = Field(None, description="ФИО ответственного")
    
    # Наименование экономического субъекта
    economic_entity: Optional[str] = Field(None, description="Наименование экономического субъекта")


class ContractorCreate(ContractorBase):
    """Создание контрагента"""
    pass


class ContractorUpdate(BaseModel):
    """Обновление контрагента"""
    org_type: Optional[Literal["ooo", "ip"]] = None
    name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    director: Optional[str] = None
    bank_name: Optional[str] = None
    bank_bik: Optional[str] = None
    bank_account: Optional[str] = None
    bank_corr_account: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    receiver_position: Optional[str] = None
    receiver_name: Optional[str] = None
    responsible_position: Optional[str] = None
    responsible_name: Optional[str] = None
    economic_entity: Optional[str] = None


class Contractor(ContractorBase):
    """Контрагент с ID"""
    id: str = Field(..., description="Уникальный ID контрагента")
    created_at: str = Field(..., description="Дата создания")
    updated_at: str = Field(..., description="Дата обновления")
