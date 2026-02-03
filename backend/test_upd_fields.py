#!/usr/bin/env python3
"""
Тест проверки передачи всех полей в УПД
"""

import json
from datetime import date

# Тестовые данные
test_data = {
    "document_number": "TEST-123",
    "document_date": "2026-02-02",
    "status": 1,
    "seller": {
        "name": "ООО \"Тестовая компания\"",
        "inn": "7707123456",
        "kpp": "770701001",
        "address": "123456, г. Москва, ул. Тестовая, д. 1"
    },
    "buyer": {
        "name": "ООО \"Покупатель\"",
        "inn": "7708654321",
        "kpp": "770801001",
        "address": "654321, г. СПб, пр. Невский, д. 100"
    },
    "items": [
        {
            "row_number": 1,
            "name": "Тестовая услуга",
            "unit_name": "усл",
            "quantity": 1,
            "price": 10000,
            "amount_without_vat": 10000,
            "vat_rate": "20%",
            "vat_amount": 2000,
            "amount_with_vat": 12000
        }
    ],
    "total_amount_without_vat": 10000,
    "total_vat_amount": 2000,
    "total_amount_with_vat": 12000,
    
    # ПРОВЕРЯЕМЫЕ ПОЛЯ
    "shipping_document": "Накладная №456",
    "contract_info": "Договор №789 от 01.01.2026",
    "shipping_date": "2026-02-02",
    "other_shipping_info": "Дополнительная информация об отгрузке",
    "receiving_date": "2026-02-03",
    "other_receiving_info": "Дополнительная информация о получении",
    "seller_responsible": {
        "position": "Главный бухгалтер",
        "full_name": "Петрова П.П."
    },
    "buyer_responsible": {
        "position": "Менеджер по закупкам",
        "full_name": "Сидорова С.С."
    }
}

print("=" * 80)
print("ТЕСТОВЫЕ ДАННЫЕ ДЛЯ ПРОВЕРКИ ПОЛЕЙ УПД")
print("=" * 80)
print()
print("Проверяемые поля:")
print()
print(f"✓ shipping_document: {test_data.get('shipping_document')}")
print(f"✓ contract_info: {test_data.get('contract_info')}")
print(f"✓ shipping_date: {test_data.get('shipping_date')}")
print(f"✓ other_shipping_info: {test_data.get('other_shipping_info')}")
print(f"✓ receiving_date: {test_data.get('receiving_date')}")
print(f"✓ other_receiving_info: {test_data.get('other_receiving_info')}")
print(f"✓ seller_responsible.position: {test_data.get('seller_responsible', {}).get('position')}")
print(f"✓ seller_responsible.full_name: {test_data.get('seller_responsible', {}).get('full_name')}")
print(f"✓ buyer_responsible.position: {test_data.get('buyer_responsible', {}).get('position')}")
print(f"✓ buyer_responsible.full_name: {test_data.get('buyer_responsible', {}).get('full_name')}")
print()
print("=" * 80)
print("JSON для отправки в API:")
print("=" * 80)
print()
print(json.dumps(test_data, indent=2, ensure_ascii=False))
print()
print("=" * 80)
print("Команда для тестирования:")
print("=" * 80)
print()
print("curl -X POST http://localhost:8000/api/v1/documents/upd/generate \\")
print("  -H 'Content-Type: application/json' \\")
print("  -d @test_upd_fields.json \\")
print("  --output test_upd.pdf")
print()
print("Или через Python:")
print()
print("import requests")
print("response = requests.post(")
print("    'http://localhost:8000/api/v1/documents/upd/generate',")
print("    json=test_data")
print(")")
print()
