#!/usr/bin/env python3
"""
Финальный тест: отправка полного запроса с проблемными полями
"""
import requests
import json

# Полные корректные тестовые данные
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
    
    # ПРОБЛЕМНЫЕ ПОЛЯ (проверяем передачу)
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
    
    # Дополнительные поля
    "shipping_document": "Накладная №456",
    "contract_info": "Договор №789 от 01.01.2026",
}

print("=" * 80)
print("ТЕСТ: Проверка передачи полей с фронтенда в PDF")
print("=" * 80)
print("\nОтправляемые ПРОБЛЕМНЫЕ поля:")
print(f"  shipping_date: {test_data['shipping_date']}")
print(f"  other_shipping_info: {test_data['other_shipping_info']}")
print(f"  receiving_date: {test_data['receiving_date']}")
print(f"  other_receiving_info: {test_data['other_receiving_info']}")
print(f"  seller_responsible: {test_data['seller_responsible']}")
print(f"  buyer_responsible: {test_data['buyer_responsible']}")

try:
    print("\n" + "=" * 80)
    print("Отправка POST запроса на /api/v1/documents/upd/generate...")
    print("=" * 80)
    
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upd/generate",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nСтатус: {response.status_code}")
    
    if response.status_code == 200:
        html = response.text
        
        # Сохраняем для проверки
        with open("/tmp/upd_final_test.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n✅ HTML сохранен в /tmp/upd_final_test.html")
        
        # Проверяем наличие данных
        print("\n" + "=" * 80)
        print("ПРОВЕРКА ДАННЫХ В HTML:")
        print("=" * 80)
        
        checks = [
            ("shipping_date (24.01.2026)", "24.01.2026" in html),
            ("other_shipping_info (23к23к23к)", "23к23к23к" in html),
            ("receiving_date (02.02.2026)", "02.02.2026" in html),
            ("seller_responsible.position (wefwe)", "wefwe" in html),
            ("buyer_responsible.position (wefwe)", "wefwe" in html),
        ]
        
        all_ok = True
        for field, found in checks:
            status = "✅" if found else "❌"
            print(f"{status} {field}: {'НАЙДЕНО' if found else 'НЕ НАЙДЕНО'}")
            if not found:
                all_ok = False
        
        if all_ok:
            print("\n🎉 ВСЕ ПОЛЯ УСПЕШНО ПЕРЕДАНЫ В HTML!")
        else:
            print("\n⚠️ НЕКОТОРЫЕ ПОЛЯ НЕ НАЙДЕНЫ В HTML!")
            print("\nОткройте /tmp/upd_final_test.html для визуальной проверки")
            
    elif response.status_code == 422:
        print("\n❌ Ошибка валидации:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Ошибка {response.status_code}:")
        print(response.text[:500])

except Exception as e:
    print(f"\n❌ Исключение: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
