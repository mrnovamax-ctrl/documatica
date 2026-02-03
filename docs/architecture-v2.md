# Documatica v2 — Архитектура

> Дата: 2 февраля 2026
> Статус: Планирование

---

## 1. Обзор

### Текущие проблемы

| Проблема | Влияние |
|----------|---------|
| Монолитный `documents.py` (1945 строк) | Сложно поддерживать и расширять |
| Смешанное хранение (PostgreSQL + JSON файлы) | Race conditions, нет транзакций |
| Нет стандарта добавления документов | На УПД ушло 12+ дней, 300 документов = 10 лет |
| Один docker-compose | Нет изоляции dev/stage/prod |
| Файлы документов в локальной FS | Не работает для распределённой команды |

### Целевая архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCUMATICA v2                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  ┌───────────┐        │
│  │  PUBLIC   │  │ DASHBOARD │  │ DOCUMENT FACTORY  │  │   ADMIN   │        │
│  │  Website  │  │  Client   │  │   300+ plugins    │  │    CMS    │        │
│  └─────┬─────┘  └─────┬─────┘  └─────────┬─────────┘  └─────┬─────┘        │
│        │              │                  │                  │              │
│        └──────────────┴────────┬─────────┴──────────────────┘              │
│                                │                                            │
│                    ┌───────────┴───────────┐                               │
│                    │     EXPORT ENGINE     │                               │
│                    │  PDF + XLS + ФНС XML  │                               │
│                    │  Mapping DSL          │                               │
│                    └───────────┬───────────┘                               │
│                                │                                            │
│                    ┌───────────┴───────────┐                               │
│                    │     CORE SERVICES     │                               │
│                    │ Auth, Billing, Storage │                               │
│                    └───────────┬───────────┘                               │
│                                │                                            │
│                    ┌───────────┴───────────┐                               │
│                    │      PostgreSQL       │  ← Единственное хранилище     │
│                    └───────────────────────┘                               │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│   DEV                    STAGE                      PROD                   │
│   localhost:8000         stage.oplatanalogov.ru     oplatanalogov.ru       │
│   .env.dev               .env.stage                 .env.prod              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Модули

### 2.1 PUBLIC (Публичная часть)

**Назначение:** SEO-лендинги, информационные страницы, блог

**Текущее расположение:**
- Роуты: `backend/app/pages/`
- Шаблоны: `backend/app/templates/public/`
- Контент: `backend/content/`

**Изменения:** Минимальные, архитектура уже хорошая

---

### 2.2 DASHBOARD (Клиентский кабинет)

**Назначение:** Конструкторы документов, список документов, организации, контрагенты

**Текущее расположение:**
- Роуты: `backend/app/dashboard/`
- Шаблоны: `backend/app/templates/dashboard/`

**Изменения:**
- [ ] Удалить дубли шаблонов (`create.html` + `create_v12.html`)
- [ ] Унифицировать формы через shared компоненты

---

### 2.3 DOCUMENT FACTORY (Генератор документов)

**Назначение:** Plugin-система для 300+ типов документов

**Новая структура:**

```
backend/app/documents/
├── __init__.py                      # Auto-discovery
├── base.py                          # BaseDocumentPlugin
├── registry.py                      # DocumentRegistry
├── cli.py                           # Scaffold generator
│
├── categories/
│   ├── primary/                     # Первичные документы
│   │   ├── upd/
│   │   │   ├── __init__.py          # UPDPlugin class
│   │   │   ├── document.yaml        # DSL-конфиг
│   │   │   ├── schema.py            # Pydantic models
│   │   │   ├── mapping.yaml         # Export mapping
│   │   │   └── templates/
│   │   │       └── print.html
│   │   ├── invoice/
│   │   ├── akt/
│   │   └── torg_12/
│   │
│   ├── tax/                         # Налоговые
│   │   ├── schet_faktura/
│   │   └── korr_schet_faktura/
│   │
│   ├── contracts/                   # Договоры (100+)
│   │   ├── kupli_prodazhi/
│   │   ├── okazaniya_uslug/
│   │   └── ...
│   │
│   ├── hr/                          # Кадровые
│   └── accounting/                  # Бухгалтерские
│
└── templates/                       # Shared partials
    ├── partials/
    │   ├── company_info.html
    │   ├── items_table.html
    │   └── signatures.html
    └── macros/
        ├── currency.html
        └── dates.html
```

---

### 2.4 EXPORT ENGINE

**Назначение:** Генерация PDF/XLS/XML на лету

**Бизнес-модель:**
```
HTML preview  →  Бесплатно
PDF/XLS/XML   →  Платно (биллинг)
```

**Ничего не храним** — генерируем при запросе, отдаём, забываем.

**Новая структура:**

```
backend/app/export/
├── __init__.py
├── engine.py                        # ExportOrchestrator
├── pdf.py                           # WeasyPrint wrapper
├── excel.py                         # openpyxl wrapper  
├── xml.py                           # ФНС XML generator
└── mapping.py                       # DSL parser
```

**Mapping DSL формат:**

```yaml
# documents/upd/mapping.yaml
fields:
  document_number:
    source: form_data.document_number
    xls: { cell: "A3" }
    xml: { path: "Файл/Документ/СвСчФакт/@НомерСчФ" }
    
  document_date:
    source: form_data.document_date
    transform: date_ru
    xls: { cell: "B3", format: "date" }
    xml: { path: "Файл/Документ/СвСчФакт/@ДатаСчФ", transform: "date_fns" }

items:
  source: form_data.items
  xls:
    start_row: 20
    columns: { name: "A", quantity: "B", price: "C", amount: "D" }
  xml:
    parent: "Файл/Документ/ТаблСчФакт"
    element: "СведТов"
```

---

### 2.5 ADMIN (Админка)

**Назначение:** Управление контентом, пользователями, промокодами

**Текущее расположение:**
- Роуты: `backend/app/admin/`
- Шаблоны: `backend/app/templates/admin/`

**Изменения:** Минимальные

---

## 3. База данных

### 3.1 Целевая схема документов

```sql
-- Единственная таблица для документов
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,           -- upd, akt, invoice, torg_12...
    user_id INTEGER REFERENCES users(id),
    form_data JSONB NOT NULL,            -- Источник правды (~5 KB)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для поиска
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_number ON documents((form_data->>'document_number'));
CREATE INDEX idx_documents_date ON documents((form_data->>'document_date'));
```

### 3.2 Миграция JSON → PostgreSQL

**Текущее состояние:**
- `backend/data/documents.json` — метаданные
- `backend/documents/{uuid}/form_data.json` — данные формы

**План миграции:**
1. Создать таблицу `documents`
2. Написать скрипт импорта JSON → PostgreSQL
3. Обновить API endpoints
4. Удалить JSON-файлы

### 3.3 Размеры

| Документов | Размер form_data |
|------------|------------------|
| 1,000 | ~5 MB |
| 10,000 | ~50 MB |
| 100,000 | ~500 MB |

---

## 4. Окружения

### 4.1 Структура файлов

```
docker-compose.yml           # Base (общие сервисы)
docker-compose.dev.yml       # Dev overrides
docker-compose.stage.yml     # Stage overrides
docker-compose.prod.yml      # Prod overrides

.env.example                 # Шаблон
.env.dev                     # Локальная разработка (git-ignored)
.env.stage                   # Stage (git-ignored)
.env.prod                    # Production (git-ignored)
```

### 4.2 Конфигурация окружений

| Параметр | Dev | Stage | Prod |
|----------|-----|-------|------|
| DEBUG | true | true | false |
| DATABASE_URL | localhost | stage-db | prod-db |
| DOMAIN | localhost:8000 | stage.oplatanalogov.ru | oplatanalogov.ru |
| BILLING_ENABLED | false | true | true |
| LOG_LEVEL | DEBUG | INFO | WARNING |

### 4.3 Команды

```bash
# Разработка
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stage
docker compose -f docker-compose.yml -f docker-compose.stage.yml up -d

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 5. Document Factory — CLI Generator

### 5.1 Использование

```bash
# Создать новый тип документа
python -m app.documents.cli scaffold torg-12 --category primary

# Что генерируется:
# ✅ documents/categories/primary/torg_12/__init__.py
# ✅ documents/categories/primary/torg_12/document.yaml
# ✅ documents/categories/primary/torg_12/schema.py
# ✅ documents/categories/primary/torg_12/mapping.yaml
# ✅ documents/categories/primary/torg_12/templates/print.html (stub)
# ✅ content/documents/torg_12/_pages.yaml
# ✅ content/documents/torg_12/index.yaml
```

### 5.2 Document Definition DSL

```yaml
# document.yaml
slug: torg-12
name: ТОРГ-12
extends: base_trade              # Наследует: стороны, товары, НДС
category: primary
version: "2026"

fields:
  document_number: { type: string, required: true, auto: counter }
  document_date: { type: date, required: true, default: today }
  transport_info: { type: string }
  driver_name: { type: string }

sections:
  seller: { extends: company }
  buyer: { extends: company }
  items: { extends: product_table, vat: true }
  transport: { custom: true }    # Требует ручной вёрстки
  signers: { extends: signer_pair }

exports:
  html: { template: print.html }
  pdf: { via: weasyprint }
  xlsx: { mapping: mapping.yaml }
  xml: { template: fns.xml, format: ON_TORG12 }

landing_pages:
  - { slug: blank, title: "ТОРГ-12 бланк" }
  - { slug: obrazec, title: "ТОРГ-12 образец заполнения" }
```

### 5.3 Время добавления документа

| Сложность | Пример | Время |
|-----------|--------|-------|
| Простой (extends) | Счёт (= УПД минус НДС) | 4-6 часов |
| Средний | ТОРГ-12, ТТН | 1-2 дня |
| Сложный | Договор, кадровый | 2-3 дня |

**300 документов = ~1.5 года** (vs 10 лет без фабрики)

---

## 6. План внедрения

### Фаза 1: Инфраструктура (1 неделя)

- [ ] Настроить dev/stage/prod окружения
- [ ] Миграция documents JSON → PostgreSQL
- [ ] Alembic миграции для новой схемы

### Фаза 2: Export Engine (1 неделя)

- [ ] Создать Mapping DSL parser
- [ ] Унифицировать PDF export (WeasyPrint)
- [ ] Унифицировать Excel export (openpyxl + mapping)
- [ ] Добавить ФНС XML export skeleton

### Фаза 3: Document Factory (1 неделя)

- [ ] Создать BaseDocumentPlugin
- [ ] Создать DocumentRegistry с auto-discovery
- [ ] Рефакторинг УПД как первый plugin
- [ ] CLI scaffold generator

### Фаза 4: Миграция документов (2 недели)

- [ ] Мигрировать Invoice на plugin-архитектуру
- [ ] Мигрировать Akt на plugin-архитектуру
- [ ] Удалить старый documents.py
- [ ] Добавить 5 новых документов для валидации

### Фаза 5: Стабилизация (1 неделя)

- [ ] Система эталонов (reference samples)
- [ ] Автотесты экспортов
- [ ] Документация для добавления документов

---

## 7. Будущее (out of scope)

| Модуль | Описание | Когда |
|--------|----------|-------|
| КриптоПро | ЭЦП для XML | После 300 документов |
| ЭДО интеграция | Диадок, СБИС, Такском | После КриптоПро |
| API для партнёров | REST/GraphQL | v3 |
| Mobile app | React Native | v3 |

---

## 8. Технические решения

| Вопрос | Решение |
|--------|---------|
| Хранение документов | PostgreSQL JSONB (form_data only) |
| Хранение файлов | Не храним, генерируем на лету |
| S3 | Не нужен |
| PDF/XLS/XML | Генерация = монетизация |
| Шаблоны документов | Jinja2 + shared partials |
| Excel export | openpyxl + YAML mapping (не SpreadsheetML) |
| ФНС XML | Jinja2 templates + XSD validation |
