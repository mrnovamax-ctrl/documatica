# Система конструкторов документов v12.0

## Обзор

Система конструкторов документов Documatica v12.0 предоставляет единую архитектуру для быстрого создания новых форм генерации документов (УПД, счета, акты, накладные и т.д.).

## Структура файлов

```
backend/app/templates/dashboard/
├── base_constructor.html          # Базовый шаблон конструктора
├── macros/
│   └── form_macros.html          # Jinja2 макросы для форм
├── upd/
│   └── create_v12.html           # Конструктор УПД (референс)
└── invoice/
    ├── create.html               # Старая версия (deprecated)
    └── create_v12.html           # Новая версия на базе системы

backend/static/js/
└── constructor-core.js           # Общие JS функции для конструкторов
```

## Создание нового конструктора

### 1. Создать шаблон

```html
{% extends "dashboard/base_constructor.html" %}
{% from 'dashboard/macros/form_macros.html' import form_card, form_row, form_input, form_select, ... %}

{% block title %}Создать документ{% endblock %}
{% block page_tag %}Конструктор{% endblock %}
{% block page_title %}Новый <span class="accent">документ</span>{% endblock %}

{% block form_content %}
<form id="document-form">
  
  {% call form_card('01', 'Реквизиты документа') %}
    {% call form_row(2) %}
      {{ form_input('doc-number', 'Номер', 'Авто', 'text', true) }}
      {{ form_date('doc-date', 'Дата', 'ДД.ММ.ГГГГ', true) }}
    {% endcall %}
  {% endcall %}
  
  {{ form_actions('Скачать PDF') }}
  
</form>
{% endblock %}

{% block extra_scripts %}
<script>
$(document).ready(function() {
    const CC = window.ConstructorCore;
    
    // Инициализация...
    CC.initDatePickers('.date-picker');
    
    // Сбор данных формы
    function collectFormData() {
        return {
            doc_number: $('#doc-number').val(),
            doc_date: CC.dateToISO($('#doc-date').val())
        };
    }
    
    // Генерация
    CC.initFormGeneration({
        formSelector: '#document-form',
        apiEndpoint: '/api/v1/documents/xxx/generate',
        collectDataFn: collectFormData,
        filename: (data) => `Document_${data.doc_number}.pdf`
    });
});
</script>
{% endblock %}
```

### 2. Создать роутер

```python
# backend/app/dashboard/document.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()

@router.get("/create/", response_class=HTMLResponse)
async def document_create(request: Request):
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/document/create_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Создать документ — Documatica",
            active_menu="document",
        )
    )
```

## Доступные макросы

### form_card
```html
{% call form_card('01', 'Заголовок секции') %}
  <!-- содержимое -->
{% endcall %}
```

### form_row
```html
{% call form_row(2) %}  {# 1-4 колонки #}
  {{ form_input(...) }}
  {{ form_input(...) }}
{% endcall %}
```

### form_input
```html
{{ form_input(id, label, placeholder, type, required, maxlength, value, class_extra, readonly) }}
```

### form_input_with_btn
```html
{{ form_input_with_btn(id, label, placeholder, btn_id, btn_icon, required, maxlength, btn_title) }}
{# btn_icon: 'search', 'auto', 'refresh', 'calendar' #}
```

### form_select
```html
{{ form_select(id, label, options, selected, required) }}
{# options: ['шт', 'кг'] или [{'value': '1', 'label': 'Один'}] #}
```

### form_date
```html
{{ form_date(id, label, placeholder, required) }}
```

### form_number
```html
{{ form_number(id, label, value, min, max, step, required, class_extra) }}
```

### form_radio_group
```html
{{ form_radio_group(name, options, selected, label) }}
{# options: [{'value': '1', 'label': 'Опция 1'}] #}
```

### form_checkbox
```html
{{ form_checkbox(id, title, description, checked) }}
```

### form_divider
```html
{{ form_divider('24px') }}
```

### product_row
```html
{{ product_row(1, ['шт', 'усл', 'кг']) }}
```

### add_product_btn
```html
{{ add_product_btn('add-product', 'Добавить позицию') }}
```

### form_totals
```html
{{ form_totals(show_vat=true) }}
```

### form_actions
```html
{{ form_actions('Скачать PDF', show_draft=true, show_template=true, show_preview=true) }}
```

## JavaScript API (ConstructorCore)

### Уведомления
```javascript
CC.showNotification('success', 'Сообщение');  // success, danger, warning, info
```

### Форматирование
```javascript
CC.formatCurrency(1000);  // "1 000,00 руб."
CC.formatNumber(1234.5);  // "1 234,50"
```

### Даты
```javascript
CC.initDatePickers('.date-picker');
CC.getTodayFormatted();   // "25.01.2025"
CC.dateToISO('25.01.2025');  // "2025-01-25"
CC.dateFromISO('2025-01-25');  // "25.01.2025"
```

### Поиск по ИНН
```javascript
CC.initINNSearch('#btn', '#inn-input', {
    name: '#name-field',
    inn: '#inn-field',
    kpp: '#kpp-field',
    address: '#address-field'
}, onSuccessCallback);

// Или напрямую
const company = await CC.searchCompanyByINN('7707123456');
```

### Поиск банка по БИК
```javascript
const bank = await CC.searchBankByBIK('044525225');
```

### Таблица товаров
```javascript
CC.initProductsTable({
    containerSelector: '#products-container',
    addBtnSelector: '#add-product',
    onCalculate: calculateTotals,
    units: ['шт', 'усл', 'кг']
});

const products = CC.collectProductsData({ rate: '20', type: 'on-top' });
```

### Расчет итогов
```javascript
CC.calculateTotals(
    { rate: '20', type: 'on-top' },
    { withoutVat: '#total-without-vat', vat: '#total-vat', withVat: '#total-with-vat' }
);
```

### Preview
```javascript
CC.initPreview({
    iframeSelector: '#sidebar-preview-iframe',
    refreshBtnSelector: '#refresh-preview',
    previewBtnSelector: '#preview-btn',
    apiEndpoint: '/api/v1/documents/xxx/preview',
    collectDataFn: collectFormData
});
```

### Генерация документа
```javascript
CC.initFormGeneration({
    formSelector: '#document-form',
    apiEndpoint: '/api/v1/documents/xxx/generate',
    collectDataFn: collectFormData,
    filename: (data) => `Doc_${data.number}.pdf`
});
```

### Черновики и шаблоны
```javascript
CC.initDraftSave('draft_key', collectFormData, '#save-draft');
const draft = CC.loadDraft('draft_key');

CC.initTemplateSave(collectFormData, 'doc_type', (data) => data.name, '#save-template');
```

### ИИ анализ
```javascript
CC.initAIAnalysis({
    btnSelector: '#ai-analyze-btn',
    resultSelector: '#ai-analysis-result',
    apiEndpoint: '/api/v1/ai/analyze-xxx',
    collectDataFn: () => ({ field: 'value' })
});
```

### Автонумерация
```javascript
CC.initAutoNumber('#auto-btn', '#number-input', (num) => console.log('Номер:', num));
```

## CSS классы

| Класс | Назначение |
|-------|------------|
| `.constructor-layout-v12` | Главный grid layout (form + preview) |
| `.form-card-v12` | Карточка секции формы |
| `.form-card-compact` | Компактная версия карточки |
| `.form-section-header-v12` | Заголовок секции (01. Название) |
| `.form-row-v12` | Ряд полей с grid |
| `.form-row-v12.cols-2/3/4` | Количество колонок |
| `.form-group-v12` | Контейнер поля |
| `.form-label-v12` | Метка поля |
| `.form-input-v12` | Текстовое поле |
| `.form-select-v12` | Выпадающий список |
| `.form-textarea-v12` | Многострочное поле |
| `.input-with-btn-v12` | Поле с кнопкой |
| `.input-btn` | Кнопка внутри поля |
| `.product-row-v12` | Строка товара |
| `.add-product-v12` | Кнопка добавить товар |
| `.form-totals-v12` | Блок итогов |
| `.form-actions-v12` | Кнопки действий |
| `.form-btn-primary-v12` | Основная кнопка |
| `.form-btn-secondary-v12` | Вторичная кнопка |
| `.preview-panel-v12` | Панель предпросмотра |
| `.preview-column-v12` | Колонка предпросмотра |
| `.ai-analysis-panel-v12` | Панель ИИ анализа |
| `.toast-v12` | Уведомление |

## Миграция старых конструкторов

1. Создать `create_v12.html` на базе `base_constructor.html`
2. Перенести логику сбора данных в `collectFormData()`
3. Заменить inline JS на вызовы ConstructorCore
4. Обновить роутер для использования нового шаблона
5. Протестировать все функции
6. Удалить старый файл или оставить как backup
