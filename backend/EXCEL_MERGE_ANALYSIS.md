# Анализ объединения ячеек в Excel HTML

## Эталонный HTML (из Excel)

### 1. XML Namespaces
```html
<html xmlns:v="urn:schemas-microsoft-com:vml"
xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:x="urn:schemas-microsoft-com:office:excel"
xmlns="http://www.w3.org/TR/REC-html40">
```

### 2. Meta теги
```html
<meta http-equiv=Content-Type content="text/html; charset=windows-1251">
<meta name=ProgId content=Excel.Sheet>
<meta name=Generator content="Microsoft Excel 15">
```

### 3. Использование colspan/rowspan
**ВАЖНО:** Эталон использует **обычный colspan/rowspan БЕЗ префикса x:**

```html
<!-- Правильно (как в эталоне) -->
<td colspan=4 rowspan=3 class=xl97 width=82 style='width:62pt'>Универсальный передаточный документ</td>

<!-- НЕ используется x:colspan -->
```

### 4. CSS стили с MSO-атрибутами
```css
@page {
    margin:.39in .39in .39in .39in;
    mso-header-margin:0in;
    mso-footer-margin:0in;
    mso-page-orientation:landscape;
}

table {
    mso-displayed-decimal-separator:"\,";
    mso-displayed-thousand-separator:" ";
}
```

### 5. Column width definitions
```html
<col class=xl65 width=7 style='mso-width-source:userset;mso-width-alt:298;width:5pt'>
```

## Сравнение с текущим шаблоном

### Текущий шаблон УЖЕ правильно использует:
✅ XML namespaces  
✅ Meta теги для Excel  
✅ Обычный colspan/rowspan (не x:colspan)  
✅ MSO стили  

### Возможные проблемы:
1. **Кодировка:** Эталон использует windows-1251, текущий - UTF-8
2. **@page стили:** Текущий имеет `size: 330mm 240mm`, эталон - margins в дюймах
3. **Атрибуты без кавычек:** Эталон: `colspan=4`, текущий: `colspan="4"` 

### Примеры объединения из эталона:

```html
<!-- Строка 198: Заголовок документа -->
<td colspan=4 rowspan=3 class=xl97 width=82 style='width:62pt'>Универсальный передаточный<br />документ</td>

<!-- Строка 203: Номер счет-фактуры -->
<td colspan=8 class=xl97 width=117 style='width:88pt'>Счёт-фактура №</td>

<!-- Строка 208: Приложение к постановлению -->
<td colspan=36 rowspan=3 class=xl138 width=585 style='width:441pt'>Приложение № 1...</td>

<!-- Строка 271: Продавец -->
<td colspan=11 class=xl128>Продавец:</td>

<!-- Строка 443: Заголовки таблицы товаров -->
<td colspan=4 rowspan=2 class=xl108 width=82 style='width:62pt'>Код товара/ работ, услуг</td>
<td colspan=4 rowspan=2 class=xl121 width=28 style='width:21pt'>№<br />п/п</td>
```

## Рекомендации

1. ✅ **НЕ МЕНЯТЬ** структуру colspan/rowspan - она уже правильная
2. ✅ Текущий шаблон использует правильный подход
3. ⚠️ Проблема скорее всего в **рендеринге Excel**, а не в HTML структуре

## Вывод

Текущий `upd_template.html` уже использует **правильный формат** для объединения ячеек. 
Проблема может быть в:
- Способе сохранения файла (нужен XLS, а не XLSX)
- Настройках экспорта
- Версии Excel

**РЕШЕНИЕ:** Текущий HTML-шаблон уже корректен для XLS формата!
