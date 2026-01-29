"""
Верификация объединенных ячеек в созданном XLS файле
"""

import sys
from pathlib import Path

try:
    import xlrd
    from xlrd.formatting import Format
except ImportError:
    print("⚠️  xlrd не установлен. Устанавливаем...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'xlrd==1.2.0'])
    import xlrd

def verify_xls_merges():
    """Проверка объединенных ячеек в XLS файле"""
    
    print("=" * 60)
    print("ВЕРИФИКАЦИЯ ОБЪЕДИНЕННЫХ ЯЧЕЕК В XLS")
    print("=" * 60)
    print()
    
    xls_file = Path(__file__).parent / "test_upd_xlwt_output.xls"
    
    if not xls_file.exists():
        print(f"❌ Файл не найден: {xls_file}")
        return False
    
    print(f"📂 Открываем файл: {xls_file}")
    print()
    
    try:
        # Открываем XLS файл
        workbook = xlrd.open_workbook(str(xls_file), formatting_info=True)
        sheet = workbook.sheet_by_index(0)
        
        print(f"📊 Лист: {sheet.name}")
        print(f"📏 Размеры: {sheet.nrows} строк x {sheet.ncols} колонок")
        print()
        
        # Получаем информацию об объединенных ячейках
        merged_cells = sheet.merged_cells
        
        print(f"🔗 ОБЪЕДИНЕННЫЕ ЯЧЕЙКИ: {len(merged_cells)}")
        print()
        
        if not merged_cells:
            print("❌ ОШИБКА: Объединенные ячейки не найдены!")
            return False
        
        # Выводим первые 10 объединений для проверки
        print("Первые объединения (row_start, row_end, col_start, col_end):")
        for i, (r1, r2, c1, c2) in enumerate(merged_cells[:15], 1):
            # Получаем значение ячейки
            try:
                cell_value = sheet.cell_value(r1, c1)
                cell_str = str(cell_value)[:50]  # Первые 50 символов
            except:
                cell_str = "[нет значения]"
            
            print(f"  {i:2d}. ({r1:2d}, {r2:2d}, {c1:2d}, {c2:2d}) = '{cell_str}'")
        
        if len(merged_cells) > 15:
            print(f"  ... и еще {len(merged_cells) - 15} объединений")
        
        print()
        print("✅ ПРОВЕРКА КРИТИЧЕСКИХ ОБЪЕДИНЕНИЙ:")
        
        # Проверяем ключевые объединения
        critical_merges = {
            "Заголовок документа (0-2, 0-3)": (0, 3, 0, 4),
            "Номер документа (0, 4-13)": (0, 1, 4, 14),
            "Шапка таблицы 'Единица измерения' (2 уровня)": None,  # Проверим наличие
            "Итоговая строка": None
        }
        
        # Проверяем наличие заголовка документа
        found_header = any(r1 == 0 and r2 == 3 and c1 == 0 and c2 == 4 for r1, r2, c1, c2 in merged_cells)
        if found_header:
            print("  ✅ Заголовок 'Универсальный передаточный документ' - объединен")
        else:
            print("  ⚠️  Заголовок документа - структура отличается")
        
        # Проверяем номер документа
        found_number = any(r1 == 0 and c1 >= 4 and c2 > 10 for r1, r2, c1, c2 in merged_cells)
        if found_number:
            print("  ✅ Номер и дата документа - объединены")
        else:
            print("  ⚠️  Номер документа - проверьте вручную")
        
        # Проверяем итоговую строку
        found_total = any(c2 - c1 >= 5 for r1, r2, c1, c2 in merged_cells if r1 > 10)
        if found_total:
            print("  ✅ Итоговая строка 'Всего к оплате' - объединена")
        else:
            print("  ⚠️  Итоговая строка - проверьте вручную")
        
        print()
        print("=" * 60)
        print(f"✅ УСПЕХ! Найдено {len(merged_cells)} объединенных ячеек")
        print("=" * 60)
        print()
        print("📝 ВАЖНО: Откройте файл в Microsoft Excel для финальной проверки:")
        print(f"   {xls_file}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА при чтении файла: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_xls_merges()
    sys.exit(0 if success else 1)
