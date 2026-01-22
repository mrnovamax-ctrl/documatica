"""
Pydantic схемы для УПД (Универсальный Передаточный Документ)
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    """Товар/услуга в УПД"""
    row_number: int = Field(..., description="Номер строки", ge=1)
    name: str = Field(..., description="Наименование товара/услуги", min_length=1, max_length=1000)
    unit_code: Optional[str] = Field(None, description="Код единицы измерения по ОКЕИ")
    unit_name: str = Field("шт", description="Наименование единицы измерения")
    quantity: Decimal = Field(..., description="Количество", ge=0)
    price: Decimal = Field(..., description="Цена за единицу без НДС", ge=0)
    amount_without_vat: Decimal = Field(..., description="Стоимость без НДС", ge=0)
    vat_rate: str = Field("20%", description="Ставка НДС (20%, 10%, 0%, без НДС)")
    vat_amount: Decimal = Field(..., description="Сумма НДС", ge=0)
    amount_with_vat: Decimal = Field(..., description="Стоимость с НДС", ge=0)
    country_code: Optional[str] = Field("643", description="Код страны происхождения")
    country_name: Optional[str] = Field("Россия", description="Наименование страны")
    customs_declaration: Optional[str] = Field(None, description="Номер ТД")


class CompanyInfo(BaseModel):
    """Информация о компании (продавец/покупатель)"""
    name: str = Field("", description="Наименование организации")
    inn: str = Field("", description="ИНН")
    kpp: Optional[str] = Field(None, description="КПП")
    address: str = Field("", description="Адрес")
    bank_name: Optional[str] = Field(None, description="Наименование банка")
    bank_bik: Optional[str] = Field(None, description="БИК банка")
    bank_account: Optional[str] = Field(None, description="Расчётный счёт")
    bank_corr_account: Optional[str] = Field(None, description="Корр. счёт")


class SignerInfo(BaseModel):
    """Информация о подписанте"""
    position: str = Field(..., description="Должность")
    full_name: str = Field(..., description="ФИО")
    basis: Optional[str] = Field("Устав", description="Основание полномочий")


class UPDRequest(BaseModel):
    """Запрос на генерацию УПД"""
    # Основные реквизиты документа
    document_number: str = Field(..., description="Номер УПД", min_length=1)
    document_date: date = Field(..., description="Дата УПД")
    correction_number: Optional[str] = Field(None, description="Номер исправления")
    correction_date: Optional[date] = Field(None, description="Дата исправления")
    
    # Статус документа (1 - счёт-фактура и передаточный документ, 2 - передаточный документ)
    status: int = Field(1, description="Статус УПД", ge=1, le=2)
    
    # Участники сделки
    seller: CompanyInfo = Field(..., description="Продавец")
    buyer: CompanyInfo = Field(..., description="Покупатель")
    consignor: Optional[str] = Field(None, description="Грузоотправитель (текст)")
    consignee: Optional[str] = Field(None, description="Грузополучатель (текст)")
    
    # Товары/услуги
    items: List[ProductItem] = Field(..., description="Товары/услуги", min_length=1)
    
    # Итоги
    total_amount_without_vat: Decimal = Field(..., description="Итого без НДС")
    total_vat_amount: Decimal = Field(..., description="Итого НДС")
    total_amount_with_vat: Decimal = Field(..., description="Итого с НДС")
    
    # Дополнительные сведения
    currency_code: str = Field("643", description="Код валюты")
    currency_name: str = Field("Российский рубль", description="Наименование валюты")
    gov_contract_id: Optional[str] = Field(None, description="Идентификатор гос. контракта")
    payment_document: Optional[str] = Field(None, description="К платёжно-расчётному документу")
    shipping_document: Optional[str] = Field(None, description="Документ об отгрузке")
    contract_info: Optional[str] = Field(None, description="Основание передачи (договор)")
    transport_info: Optional[str] = Field(None, description="Данные о транспортировке")
    
    # Передача товара/услуги (подписант продавца)
    shipping_date: Optional[date] = Field(None, description="Дата отгрузки/передачи")
    other_shipping_info: Optional[str] = Field(None, description="Иные сведения об отгрузке")
    seller_signer: Optional[SignerInfo] = Field(None, description="Кто передал товар")
    seller_responsible: Optional[SignerInfo] = Field(None, description="Ответственный за правильность оформления (продавец)")
    economic_entity: Optional[str] = Field(None, description="Наименование экономического субъекта (продавец)")
    
    # Получение товара/услуги (подписант покупателя)
    receiving_date: Optional[date] = Field(None, description="Дата получения/приемки")
    other_receiving_info: Optional[str] = Field(None, description="Иные сведения о получении")
    buyer_signer: Optional[SignerInfo] = Field(None, description="Кто получил товар")
    buyer_responsible: Optional[SignerInfo] = Field(None, description="Ответственный за правильность оформления (покупатель)")
    buyer_economic_entity: Optional[str] = Field(None, description="Наименование экономического субъекта (покупатель)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_number": "17",
                "document_date": "2026-01-16",
                "status": 1,
                "seller": {
                    "name": "ООО \"ТехноСофт\"",
                    "inn": "7707123456",
                    "kpp": "770701001",
                    "address": "123456, г. Москва, ул. Программистов, д. 42"
                },
                "buyer": {
                    "name": "ООО \"Партнер Плюс\"",
                    "inn": "7708654321",
                    "kpp": "770801001",
                    "address": "654321, г. Санкт-Петербург, пр. Невский, д. 100"
                },
                "items": [
                    {
                        "row_number": 1,
                        "name": "Разработка веб-приложения",
                        "unit_name": "усл",
                        "quantity": 1,
                        "price": 150000,
                        "amount_without_vat": 150000,
                        "vat_rate": "20%",
                        "vat_amount": 30000,
                        "amount_with_vat": 180000
                    }
                ],
                "total_amount_without_vat": 150000,
                "total_vat_amount": 30000,
                "total_amount_with_vat": 180000
            }
        }


class UPDResponse(BaseModel):
    """Ответ с сгенерированным УПД"""
    success: bool
    message: str
    document_number: str
    filename: str
    pdf_base64: Optional[str] = Field(None, description="PDF в base64 (если запрошено)")
    download_url: Optional[str] = Field(None, description="URL для скачивания")


class PreviewCompanyInfo(BaseModel):
    """Информация о компании для предпросмотра (мягкая валидация)"""
    name: Optional[str] = Field("", description="Наименование организации")
    inn: Optional[str] = Field("", description="ИНН")
    kpp: Optional[str] = Field(None, description="КПП")
    address: Optional[str] = Field("", description="Адрес")


class PreviewProductItem(BaseModel):
    """Товар/услуга для предпросмотра (мягкая валидация)"""
    row_number: Optional[int] = Field(1, description="Номер строки")
    name: Optional[str] = Field("Товар", description="Наименование")
    unit_code: Optional[str] = Field(None, description="Код единицы")
    unit_name: Optional[str] = Field("шт", description="Единица измерения")
    quantity: Optional[Decimal] = Field(0, description="Количество")
    price: Optional[Decimal] = Field(0, description="Цена")
    amount_without_vat: Optional[Decimal] = Field(0, description="Сумма без НДС")
    vat_rate: Optional[str] = Field("20%", description="Ставка НДС")
    vat_amount: Optional[Decimal] = Field(0, description="Сумма НДС")
    amount_with_vat: Optional[Decimal] = Field(0, description="Сумма с НДС")
    country_code: Optional[str] = Field("643", description="Код страны")
    country_name: Optional[str] = Field("Россия", description="Страна")
    customs_declaration: Optional[str] = Field(None, description="ТД")


class PreviewSignerInfo(BaseModel):
    """Информация о подписанте для предпросмотра"""
    position: Optional[str] = Field("", description="Должность")
    full_name: Optional[str] = Field("", description="ФИО")
    basis: Optional[str] = Field("Устав", description="Основание")


class UPDPreviewRequest(BaseModel):
    """Запрос на предпросмотр УПД (мягкая валидация)"""
    document_number: Optional[str] = Field("1", description="Номер УПД")
    document_date: Optional[date] = Field(None, description="Дата УПД")
    correction_number: Optional[str] = Field(None, description="Номер исправления")
    correction_date: Optional[date] = Field(None, description="Дата исправления")
    status: Optional[int] = Field(1, description="Статус УПД")
    
    seller: Optional[PreviewCompanyInfo] = Field(default_factory=PreviewCompanyInfo)
    buyer: Optional[PreviewCompanyInfo] = Field(default_factory=PreviewCompanyInfo)
    consignor: Optional[str] = Field(None, description="Грузоотправитель")
    consignee: Optional[str] = Field(None, description="Грузополучатель")
    
    items: Optional[List[PreviewProductItem]] = Field(default_factory=list)
    
    total_amount_without_vat: Optional[Decimal] = Field(0, description="Итого без НДС")
    total_vat_amount: Optional[Decimal] = Field(0, description="Итого НДС")
    total_amount_with_vat: Optional[Decimal] = Field(0, description="Итого с НДС")
    
    currency_code: Optional[str] = Field("643", description="Код валюты")
    currency_name: Optional[str] = Field("Российский рубль", description="Валюта")
    gov_contract_id: Optional[str] = Field(None, description="Гос. контракт")
    payment_document: Optional[str] = Field(None, description="Платежный документ")
    shipping_document: Optional[str] = Field(None, description="Документ об отгрузке")
    contract_info: Optional[str] = Field(None, description="Договор")
    transport_info: Optional[str] = Field(None, description="Транспортировка")
    
    shipping_date: Optional[date] = Field(None, description="Дата отгрузки")
    other_shipping_info: Optional[str] = Field(None, description="Иные сведения")
    seller_signer: Optional[PreviewSignerInfo] = Field(None, description="Подписант продавца")
    seller_responsible: Optional[PreviewSignerInfo] = Field(None, description="Ответственный продавца")
    economic_entity: Optional[str] = Field(None, description="Экономический субъект")
    
    receiving_date: Optional[date] = Field(None, description="Дата получения")
    other_receiving_info: Optional[str] = Field(None, description="Иные сведения")
    buyer_signer: Optional[PreviewSignerInfo] = Field(None, description="Подписант покупателя")
    buyer_responsible: Optional[PreviewSignerInfo] = Field(None, description="Ответственный покупателя")
    buyer_economic_entity: Optional[str] = Field(None, description="Экономический субъект покупателя")
