#!/usr/bin/env python3
"""
Тест рендеринга шаблона УПД с проверкой проблемных полей
"""

import sys
sys.path.insert(0, '/opt/beget/documatica/backend')

from app.core.templates import templates
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Путь к шаблонам
TEMPLATES_DIR = Path('/opt/beget/documatica/backend/app/templates')

# Создаем Jinja2 Environment
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Загружаем шаблон
template = jinja_env.get_template("upd_template.html")

# Тестовые данные с проблемными полями
test_data = {
    "document_number": "TEST-999",
    "document_date": "02.02.2026",
    "status": 1,
    
    "seller": {
        "name": "ООО Тест",
        "inn": "1234567890",
        "kpp": "123456789",
        "address": "Тестовый адрес"
    },
    
    "buyer": {
        "name": "ООО Покупатель",
        "inn": "0987654321",
        "kpp": "987654321",
        "address": "Адрес покупателя"
    },
    
    "items": [{
        "name": "Тест товар",
        "unit_name": "шт",
        "quantity": 1,
        "price": 1000,
        "amount_without_vat": 1000,
        "vat_rate": "20%",
        "vat_amount": 200,
        "amount_with_vat": 1200,
        "country_name": "Россия",
        "country_code": "643"
    }],
    
    "total_amount_without_vat": 1000,
    "total_vat_amount": 200,
    "total_amount_with_vat": 1200,
    
    # ПРОБЛЕМНЫЕ ПОЛЯ - используем алиасы для шаблона
    "transfer_date": "02.02.2026",  # алиас для shipping_date
    "other_transfer_info": "Тестовая информация об отгрузке",  # алиас для other_shipping_info
    "receipt_date": "03.02.2026",  # алиас для receiving_date
    "other_receipt_info": "Тестовая информация о получении",  # алиас для other_receiving_info
    
    # Также добавим оригинальные поля
    "shipping_date": "02.02.2026",
    "other_shipping_info": "Тестовая информация об отгрузке",
    "receiving_date": "03.02.2026",
    "other_receiving_info": "Тестовая информация о получении",
}

print("=" * 80)
print("ТЕСТ РЕНДЕРИНГА ШАБЛОНА УПД")
print("=" * 80)
print()
print("Проверяемые поля в template_data:")
print(f"  transfer_date: {test_data.get('transfer_date')}")
print(f"  other_transfer_info: {test_data.get('other_transfer_info')}")
print(f"  receipt_date: {test_data.get('receipt_date')}")
print(f"  other_receipt_info: {test_data.get('other_receipt_info')}")
print()

try:
    # Рендерим HTML
    html_content = template.render(**test_data)
    
    # Проверяем наличие полей в HTML
    checks = {
        "transfer_date": "02.02.2026" in html_content,
        "other_transfer_info": "Тестовая информация об отгрузке" in html_content,
        "receipt_date": "03.02.2026" in html_content,
        "other_receipt_info": "Тестовая информация о получении" in html_content,
    }
    
    print("Результаты проверки в HTML:")
    for field, found in checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} {field}: {'НАЙДЕНО' if found else 'НЕ НАЙДЕНО'}")
    
    print()
    
    if all(checks.values()):
        print("✓ ВСЕ ПОЛЯ ПРИСУТСТВУЮТ В HTML!")
    else:
        print("✗ НЕКОТОРЫЕ ПОЛЯ ОТСУТСТВУЮТ!")
        print()
        print("Сохраняем HTML для ручной проверки...")
        with open('/opt/beget/documatica/backend/test_upd_output.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Файл сохранен: /opt/beget/documatica/backend/test_upd_output.html")
        
        # Ищем блоки [11], [12], [16], [17] в HTML
        print()
        print("Поиск блоков в HTML:")
        if "[11]" in html_content:
            print("  ✓ Блок [11] (Дата отгрузки) найден")
        if "[12]" in html_content:
            print("  ✓ Блок [12] (Иные сведения об отгрузке) найден")
        if "[16]" in html_content:
            print("  ✓ Блок [16] (Дата получения) найден")
        if "[17]" in html_content:
            print("  ✓ Блок [17] (Иные сведения о получении) найден")
    
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"✗ ОШИБКА при рендеринге: {e}")
    import traceback
    traceback.print_exc()
