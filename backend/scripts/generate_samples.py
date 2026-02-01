#!/usr/bin/env python3
"""
Скрипт для генерации образцов документов в PDF
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from decimal import Decimal
import io

from app.schemas.upd import UPDRequest, CompanyInfo, ProductItem, SignerInfo
from app.api.documents import number_to_words_ru
from jinja2 import Environment, FileSystemLoader

# Попытка импорта WeasyPrint
try:
    from weasyprint import HTML as WeasyHTML
    WEASYPRINT_AVAILABLE = True
except (OSError, ImportError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"⚠️  WeasyPrint не доступен: {e}")
    print("Установите WeasyPrint для генерации PDF")
    sys.exit(1)

# Пути
TEMPLATES_DIR = Path(__file__).parent.parent / "app" / "templates"
SAMPLES_DIR = Path(__file__).parent.parent / "app" / "static" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Настройка Jinja2
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True
)


def format_date_short(date_obj) -> str:
    """Форматирование даты в короткий формат DD.MM.YYYY"""
    if date_obj is None:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%d.%m.%Y")


def format_date(date_obj) -> str:
    """Форматирование даты в русский формат"""
    if date_obj is None:
        return ""
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year} г."


def generate_upd_pdf(request: UPDRequest, filename: str):
    """Генерирует PDF УПД и сохраняет в файл"""
    
    # Загружаем шаблон
    template = jinja_env.get_template("upd_template.html")
    
    # Подготовка данных для шаблона
    template_data = {
        # Основные реквизиты
        "document_number": request.document_number,
        "document_date": format_date_short(request.document_date),
        "correction_number": request.correction_number,
        "correction_date": format_date_short(request.correction_date) if request.correction_date else None,
        "status": request.status,
        
        # Продавец
        "seller": request.seller.model_dump(),
        
        # Покупатель
        "buyer": request.buyer.model_dump(),
        
        # Грузоотправитель/грузополучатель
        "consignor": request.consignor,
        "consignee": request.consignee,
        
        # Товары/услуги
        "items": [
            {
                **item.model_dump(),
                "quantity": float(item.quantity),
                "price": float(item.price),
                "amount_without_vat": float(item.amount_without_vat),
                "vat_amount": float(item.vat_amount),
                "amount_with_vat": float(item.amount_with_vat),
            }
            for item in request.items
        ],
        
        # Итоги
        "total_amount_without_vat": float(request.total_amount_without_vat),
        "total_vat_amount": float(request.total_vat_amount),
        "total_amount_with_vat": float(request.total_amount_with_vat),
        
        # Дополнительные сведения
        "currency_code": request.currency_code,
        "currency_name": request.currency_name,
        "gov_contract_id": request.gov_contract_id,
        "payment_document": request.payment_document,
        "shipping_document": request.shipping_document,
        "contract_info": request.contract_info,
        "transport_info": request.transport_info,
        
        # Даты и подписанты
        "shipping_date": format_date(request.shipping_date) if request.shipping_date else None,
        "receiving_date": format_date(request.receiving_date) if request.receiving_date else None,
        "seller_signer": request.seller_signer.model_dump() if request.seller_signer else None,
        "seller_responsible": request.seller_responsible.model_dump() if request.seller_responsible else None,
        "buyer_signer": request.buyer_signer.model_dump() if request.buyer_signer else None,
        "buyer_responsible": request.buyer_responsible.model_dump() if request.buyer_responsible else None,
        "economic_entity": request.economic_entity,
        "buyer_economic_entity": request.buyer_economic_entity,
        "seller_org_type": request.seller_org_type,
    }
    
    # Рендерим HTML
    html_content = template.render(**template_data)
    
    # Генерируем PDF
    output_path = SAMPLES_DIR / filename
    WeasyHTML(string=html_content).write_pdf(output_path)
    
    print(f"✅ Создан: {output_path}")


def generate_invoice_pdf(data: dict, filename: str):
    """Генерирует PDF счета и сохраняет в файл"""
    template = jinja_env.get_template("invoice_template.html")

    total_with_vat = float(data.get("total_with_vat", 0))
    template_data = {
        "invoice_number": data.get("invoice_number", ""),
        "invoice_date": data.get("invoice_date", ""),
        "contract_info": data.get("contract_info", ""),
        "payment_due": data.get("payment_due"),
        "invoice_note": data.get("invoice_note", ""),
        "supplier": data.get("supplier", {}),
        "bank": data.get("bank", {}),
        "signers": data.get("signers", {}),
        "client": data.get("client", {}),
        "items": data.get("items", []),
        "vat_rate": data.get("vat_rate", "20%"),
        "vat_amount": float(data.get("vat_amount", 0)),
        "total_without_vat": float(data.get("total_without_vat", 0)),
        "total_with_vat": total_with_vat,
        "amount_in_words": number_to_words_ru(total_with_vat).capitalize(),
        "supplier_org_type": data.get("supplier_org_type", "ooo"),
        "supplier_stamp_image": data.get("supplier_stamp_image"),
        "director_signature": data.get("director_signature"),
        "accountant_signature": data.get("accountant_signature"),
    }

    html_content = template.render(**template_data)
    output_path = SAMPLES_DIR / filename
    WeasyHTML(string=html_content).write_pdf(output_path)
    print(f"✅ Создан: {output_path}")


def generate_akt_pdf(data: dict, filename: str):
    """Генерирует PDF акта и сохраняет в файл"""
    template = jinja_env.get_template("akt_template.html")

    total_amount = float(data.get("total_amount", 0))
    total_vat = float(data.get("total_vat", 0))
    total_without_vat = float(data.get("total_without_vat", total_amount))

    template_data = {
        "document_number": data.get("document_number", ""),
        "document_date_day": data.get("document_date_day", ""),
        "document_date_month": data.get("document_date_month", ""),
        "document_date_year": data.get("document_date_year", ""),
        "executor": data.get("executor", {}),
        "customer": data.get("customer", {}),
        "contract_number": data.get("contract_number"),
        "contract_date": data.get("contract_date"),
        "items": data.get("items", []),
        "vat_rate": data.get("vat_rate", "none"),
        "total_without_vat": total_without_vat,
        "total_vat": total_vat,
        "total_amount": total_amount,
        "total_amount_words": number_to_words_ru(total_amount).capitalize(),
        "total_vat_words": number_to_words_ru(total_vat).capitalize(),
        "notes": data.get("notes"),
        "customer_signatory": data.get("customer_signatory"),
        "executor_signatory": data.get("executor_signatory"),
        "executor_org_type": data.get("executor_org_type", "ooo"),
        "executor_signature": data.get("executor_signature"),
        "executor_stamp_image": data.get("executor_stamp_image"),
    }

    html_content = template.render(**template_data)
    output_path = SAMPLES_DIR / filename
    WeasyHTML(string=html_content).write_pdf(output_path)
    print(f"✅ Создан: {output_path}")


def main():
    """Генерирует образцы УПД и счета"""
    
    print("🚀 Начинаем генерацию образцов УПД...\n")
    
    # ==============================================
    # ОБРАЗЕЦ 1: УПД с НДС (Статус 1) для ООО
    # ==============================================
    
    upd_with_vat = UPDRequest(
        document_number="00000123",
        document_date=date(2026, 1, 15),
        status=1,
        
        seller=CompanyInfo(
            name='ООО "Техносервис"',
            inn="7704123456",
            kpp="770401001",
            address="119021, г. Москва, ул. Льва Толстого, д. 16"
        ),
        
        buyer=CompanyInfo(
            name='ООО "Строительная компания"',
            inn="7708765432",
            kpp="770801001",
            address="115054, г. Москва, Космодамианская наб., д. 52, стр. 5"
        ),
        
        consignor="Тот же",
        consignee="Тот же",
        
        items=[
            ProductItem(
                row_number=1,
                name="Компьютер Dell OptiPlex 7080",
                unit_name="шт",
                quantity=Decimal("10"),
                price=Decimal("45000.00"),
                amount_without_vat=Decimal("450000.00"),
                vat_rate="20%",
                vat_amount=Decimal("90000.00"),
                amount_with_vat=Decimal("540000.00"),
                country_code="643",
                country_name="Россия"
            ),
            ProductItem(
                row_number=2,
                name='Монитор Samsung 27"',
                unit_name="шт",
                quantity=Decimal("10"),
                price=Decimal("15000.00"),
                amount_without_vat=Decimal("150000.00"),
                vat_rate="20%",
                vat_amount=Decimal("30000.00"),
                amount_with_vat=Decimal("180000.00"),
                country_code="643",
                country_name="Россия"
            ),
        ],
        
        total_amount_without_vat=Decimal("600000.00"),
        total_vat_amount=Decimal("120000.00"),
        total_amount_with_vat=Decimal("720000.00"),
        
        currency_code="643",
        currency_name="Российский рубль",
        contract_info='Договор поставки № 15/2026 от 10.01.2026',
        
        shipping_date=date(2026, 1, 15),
        receiving_date=date(2026, 1, 15),
        
        seller_signer=SignerInfo(
            position="Генеральный директор",
            full_name="Иванов Иван Иванович",
            basis="Устав"
        ),
        
        seller_responsible=SignerInfo(
            position="Главный бухгалтер",
            full_name="Петрова Анна Сергеевна",
            basis="Устав"
        ),
        
        buyer_signer=SignerInfo(
            position="Генеральный директор",
            full_name="Сидоров Петр Константинович",
            basis="Устав"
        ),
        
        economic_entity='ООО "Техносервис"',
        seller_org_type="ooo"
    )
    
    generate_upd_pdf(upd_with_vat, "upd-obrazec-s-nds.pdf")
    
    # ==============================================
    # ОБРАЗЕЦ 2: УПД без НДС (Статус 2) для ИП
    # ==============================================
    
    upd_without_vat = UPDRequest(
        document_number="45",
        document_date=date(2026, 1, 20),
        status=2,
        
        seller=CompanyInfo(
            name="ИП Смирнов Алексей Владимирович",
            inn="780112345678",
            kpp=None,
            address="197022, г. Санкт-Петербург, пр. Медиков, д. 3, кв. 45"
        ),
        
        buyer=CompanyInfo(
            name='ООО "Бизнес Решения"',
            inn="7801234567",
            kpp="780101001",
            address="197022, г. Санкт-Петербург, ул. Ленина, д. 10"
        ),
        
        consignor="Тот же",
        consignee="Тот же",
        
        items=[
            ProductItem(
                row_number=1,
                name="Консультационные услуги по налоговому учету",
                unit_name="час",
                quantity=Decimal("20"),
                price=Decimal("3000.00"),
                amount_without_vat=Decimal("60000.00"),
                vat_rate="Без НДС",
                vat_amount=Decimal("0.00"),
                amount_with_vat=Decimal("60000.00"),
                country_code="643",
                country_name="Россия"
            ),
            ProductItem(
                row_number=2,
                name="Подготовка налоговой отчетности",
                unit_name="услуга",
                quantity=Decimal("1"),
                price=Decimal("15000.00"),
                amount_without_vat=Decimal("15000.00"),
                vat_rate="Без НДС",
                vat_amount=Decimal("0.00"),
                amount_with_vat=Decimal("15000.00"),
                country_code="643",
                country_name="Россия"
            ),
        ],
        
        total_amount_without_vat=Decimal("75000.00"),
        total_vat_amount=Decimal("0.00"),
        total_amount_with_vat=Decimal("75000.00"),
        
        currency_code="643",
        currency_name="Российский рубль",
        contract_info='Договор оказания услуг № 8-КС/2026 от 05.01.2026',
        
        shipping_date=date(2026, 1, 20),
        receiving_date=date(2026, 1, 20),
        
        seller_signer=SignerInfo(
            position="Индивидуальный предприниматель",
            full_name="Смирнов Алексей Владимирович",
            basis="Свидетельство о регистрации"
        ),
        
        buyer_signer=SignerInfo(
            position="Генеральный директор",
            full_name="Кузнецов Дмитрий Александрович",
            basis="Устав"
        ),
        
        economic_entity="ИП Смирнов Алексей Владимирович",
        seller_org_type="ip"
    )
    
    generate_upd_pdf(upd_without_vat, "upd-obrazec-bez-nds.pdf")
    
    # ==============================================
    # ОБРАЗЕЦ 3: УПД для ИП с товарами
    # ==============================================
    
    upd_ip = UPDRequest(
        document_number="78",
        document_date=date(2026, 1, 25),
        status=2,
        
        seller=CompanyInfo(
            name="ИП Петров Игорь Сергеевич",
            inn="773012345678",
            kpp=None,
            address="123456, г. Москва, ул. Предпринимательская, д. 5, кв. 102"
        ),
        
        buyer=CompanyInfo(
            name='ООО "Торговый дом Альфа"',
            inn="7725123456",
            kpp="772501001",
            address="125009, г. Москва, ул. Тверская, д. 25"
        ),
        
        consignor="Тот же",
        consignee="Тот же",
        
        items=[
            ProductItem(
                row_number=1,
                name="Канцелярские товары (набор)",
                unit_name="компл",
                quantity=Decimal("50"),
                price=Decimal("850.00"),
                amount_without_vat=Decimal("42500.00"),
                vat_rate="Без НДС",
                vat_amount=Decimal("0.00"),
                amount_with_vat=Decimal("42500.00"),
                country_code="643",
                country_name="Россия"
            ),
            ProductItem(
                row_number=2,
                name="Бумага офисная А4, 500 листов",
                unit_name="уп",
                quantity=Decimal("100"),
                price=Decimal("250.00"),
                amount_without_vat=Decimal("25000.00"),
                vat_rate="Без НДС",
                vat_amount=Decimal("0.00"),
                amount_with_vat=Decimal("25000.00"),
                country_code="643",
                country_name="Россия"
            ),
            ProductItem(
                row_number=3,
                name="Папки-регистраторы",
                unit_name="шт",
                quantity=Decimal("200"),
                price=Decimal("120.00"),
                amount_without_vat=Decimal("24000.00"),
                vat_rate="Без НДС",
                vat_amount=Decimal("0.00"),
                amount_with_vat=Decimal("24000.00"),
                country_code="643",
                country_name="Россия"
            ),
        ],
        
        total_amount_without_vat=Decimal("91500.00"),
        total_vat_amount=Decimal("0.00"),
        total_amount_with_vat=Decimal("91500.00"),
        
        currency_code="643",
        currency_name="Российский рубль",
        contract_info='Договор поставки № 25-ТД от 15.01.2026',
        
        shipping_date=date(2026, 1, 25),
        receiving_date=date(2026, 1, 25),
        
        seller_signer=SignerInfo(
            position="Индивидуальный предприниматель",
            full_name="Петров Игорь Сергеевич",
            basis="Свидетельство о регистрации"
        ),
        
        buyer_signer=SignerInfo(
            position="Генеральный директор",
            full_name="Волков Андрей Николаевич",
            basis="Устав"
        ),
        
        economic_entity="ИП Петров Игорь Сергеевич",
        seller_org_type="ip"
    )
    
    generate_upd_pdf(upd_ip, "upd-obrazec-ip.pdf")
    
    # ==============================================
    # ОБРАЗЕЦ 4: Счет на оплату (ООО, с НДС)
    # ==============================================
    invoice_data = {
        "invoice_number": "45",
        "invoice_date": "20.01.2026",
        "contract_info": "Договор № 12 от 10.01.2026",
        "invoice_note": "Оплата услуг по договору",
        "supplier": {
            "name": 'ООО "Техносервис"',
            "inn": "7704123456",
            "kpp": "770401001",
            "address": "г. Москва, ул. Тверская, д. 10",
        },
        "bank": {
            "name": "ПАО Сбербанк",
            "bik": "044525225",
            "account": "30101810400000000225",
            "settlement_account": "40702810900000000001",
        },
        "client": {
            "name": 'ООО "Бизнес Решения"',
            "inn": "7801234567",
            "kpp": "780101001",
            "address": "г. Санкт‑Петербург, ул. Невский, д. 1",
        },
        "items": [
            {
                "name": "Разработка сайта",
                "unit": "усл.",
                "quantity": 1,
                "price": 100000,
                "amount": 100000,
            }
        ],
        "vat_rate": "20%",
        "vat_amount": 20000,
        "total_without_vat": 100000,
        "total_with_vat": 120000,
        "supplier_org_type": "ooo",
    }
    generate_invoice_pdf(invoice_data, "schet-obrazec.pdf")

    # ==============================================
    # ОБРАЗЕЦ 5: Акт выполненных работ (ООО)
    # ==============================================
    akt_data = {
        "document_number": "15",
        "document_date_day": "26",
        "document_date_month": "января",
        "document_date_year": "2026",
        "executor": {
            "name": 'ООО "Техносервис"',
            "inn": "7704123456",
            "kpp": "770401001",
            "address": "г. Москва, ул. Тверская, д. 10",
        },
        "customer": {
            "name": 'ООО "Бизнес Решения"',
            "inn": "7801234567",
            "kpp": "780101001",
            "address": "г. Санкт‑Петербург, ул. Невский, д. 1",
        },
        "contract_number": "10",
        "contract_date": "01.01.2026",
        "items": [
            {
                "name": "Разработка сайта по договору № 10 от 01.01.2026",
                "quantity": 1,
                "unit": "шт.",
                "price": 100000,
                "amount": 100000,
            }
        ],
        "vat_rate": "20",
        "total_without_vat": 100000,
        "total_vat": 20000,
        "total_amount": 120000,
        "executor_signatory": "Иванов И.И.",
        "customer_signatory": "Петров П.П.",
        "executor_org_type": "ooo",
    }
    generate_akt_pdf(akt_data, "akt-obrazec.pdf")

    print("\n🎉 Все образцы успешно созданы!")
    print(f"📁 Директория: {SAMPLES_DIR}")


if __name__ == "__main__":
    main()
