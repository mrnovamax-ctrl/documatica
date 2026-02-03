#!/usr/bin/env python3
"""
Тест: отправка запроса на /upd/generate с тестовыми данными
Проверяет, что API правильно обрабатывает данные
"""
import requests
import json
from datetime import date

# URL API (локальный сервер)
API_URL = "http://localhost:8000/api/v1/documents/upd/generate"

# Минимальные тестовые данные (как с фронтенда)
test_data = {
    "document_type": "upd",
    "document_number": "TEST-001",
    "document_date": str(date.today()),
    
    # Организации
    "seller": {
        "inn": "1234567890",
        "name": "ООО Тест Продавец",
        "address": "Москва"
    },
    "buyer": {
        "inn": "0987654321",
        "name": "ООО Тест Покупатель",
        "address": "Санкт-Петербург"
    },
    
    # Товары
    "items": [
        {
            "name": "Тестовый товар",
            "quantity": 1,
            "unit": "шт",
            "price": 100.00,
            "total": 100.00,
            "vat_rate": "20%",
            "vat_amount": 20.00,
            "total_with_vat": 120.00
        }
    ],
    
    # Итоги
    "total_amount_without_vat": 100.00,
    "total_vat_amount": 20.00,
    "total_amount_with_vat": 120.00,
    
    # ПРОБЛЕМНЫЕ ПОЛЯ
    "shipping_date": "2026-01-24",
    "other_shipping_info": "23к23к23к",
    "receiving_date": "2026-02-02",
    "other_receiving_info": "23к23к23к",
    
    "seller_responsible": {
        "position": "wefwe",
        "full_name": "wefwef"
    },
    "buyer_responsible": {
        "position": "wefwe",
        "full_name": "wefwef"
    },
    
    # Обязательные подписанты
    "seller_signer": {
        "position": "Директор",
        "full_name": "Иванов И.И."
    },
    "buyer_signer": {
        "position": "Директор",
        "full_name": "Петров П.П."
    }
}

print("=" * 80)
print("ТЕСТ: Отправка данных на /upd/generate")
print("=" * 80)
print("\nОтправляемые данные (проблемные поля):")
print(f"  shipping_date: {test_data['shipping_date']}")
print(f"  other_shipping_info: {test_data['other_shipping_info']}")
print(f"  receiving_date: {test_data['receiving_date']}")
print(f"  other_receiving_info: {test_data['other_receiving_info']}")
print(f"  seller_responsible: {test_data['seller_responsible']}")
print(f"  buyer_responsible: {test_data['buyer_responsible']}")

print("\n" + "=" * 80)
print("Отправка запроса...")
print("=" * 80)

try:
    response = requests.post(
        API_URL,
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nСтатус ответа: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ УПД успешно создан!")
        
        # Сохраняем HTML для проверки
        with open("/tmp/test_upd_output.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("\n📄 HTML сохранен в /tmp/test_upd_output.html")
        
        # Проверяем наличие данных в HTML
        html = response.text
        checks = {
            "transfer_date (24.01.2026)": "24.01.2026" in html,
            "other_transfer_info (23к23к23к)": "23к23к23к" in html,
            "receipt_date (02.02.2026)": "02.02.2026" in html,
            "seller_responsible.position (wefwe)": "wefwe" in html,
        }
        
        print("\n" + "=" * 80)
        print("ПРОВЕРКА ДАННЫХ В HTML:")
        print("=" * 80)
        for field, exists in checks.items():
            status = "✅" if exists else "❌"
            print(f"{status} {field}: {'НАЙДЕНО' if exists else 'НЕ НАЙДЕНО'}")
            
        if all(checks.values()):
            print("\n🎉 ВСЕ ПОЛЯ ПРИСУТСТВУЮТ В HTML!")
        else:
            print("\n⚠️ НЕКОТОРЫЕ ПОЛЯ ОТСУТСТВУЮТ!")
            
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Исключение: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
