# Documatica Backend

## Быстрый запуск (локально)

### 1. Создать виртуальное окружение

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Запустить сервер

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Открыть документацию API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Запуск через Docker

```bash
cd ..
docker-compose up -d
```

## API Endpoints

### POST /api/v1/documents/upd/generate

Генерация УПД в PDF формате.

**Пример запроса:**

```json
{
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
```

### POST /api/v1/documents/upd/preview

Предпросмотр УПД в HTML формате (для отладки).

### GET /api/v1/documents/templates

Список доступных шаблонов документов.

## Примечания по WeasyPrint (Windows)

Для работы WeasyPrint на Windows нужно:

1. Установить GTK3: https://github.com/nicobytes/weasyprint-docker

Или использовать Docker, где всё уже настроено.
