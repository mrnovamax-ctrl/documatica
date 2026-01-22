# Сценарий регистрации гостя при создании УПД

## Реализованный функционал

### UX Flow "Try Before Register"

1. **Гость заходит на сайт** → нажимает "Создать УПД бесплатно"
2. **Заполняет форму** → вводит данные продавца, покупателя, товары (БЕЗ регистрации)
3. **Нажимает "Скачать PDF"** → появляется модальное окно регистрации
4. **Регистрируется** → получает токен и автоматически скачивает PDF
5. **Документ сохраняется** в его личном кабинете автоматически

## Технические детали

### 1. Доступ к форме создания УПД

**Файл:** `/opt/beget/documatica/backend/app/dashboard/upd.py`

```python
@router.get("/create/", response_class=HTMLResponse)
async def upd_create(request: Request):
    # Авторизация НЕ требуется - гости могут заполнять форму
    # Проверка auth только при генерации PDF
    context = get_dashboard_context(request)
    return templates.TemplateResponse("dashboard/upd/create.html", context)
```

### 2. Проверка авторизации при генерации PDF

**Файл:** `/opt/beget/documatica/backend/app/templates/dashboard/upd/create.html`

**Функция:** `generateAndDownloadPDF()` (строка ~2504)

```javascript
async function generateAndDownloadPDF(requestData) {
    // ПРОВЕРКА АВТОРИЗАЦИИ
    const token = localStorage.getItem('documatica_token') || getCookie('access_token');
    
    if (!token) {
        // Гость - сохраняем данные и показываем модалку
        localStorage.setItem('pending_upd_data', JSON.stringify(requestData));
        $('#guestRegistrationModal').modal('show');
        return;
    }
    
    // Авторизованный пользователь - генерируем PDF
    // ... остальная логика
}
```

### 3. Модальное окно регистрации

**ID:** `#guestRegistrationModal`

**Дизайн:** Documatica v12.0 Style
- Левая часть: брендинг + преимущества
- Правая часть: форма регистрации (email, пароль, имя, checkbox terms)
- Кнопка: "Зарегистрироваться" (blue-600)

### 4. Обработчик регистрации

**Функция:** `$('#guest-registration-form').on('submit')`

**Процесс:**
1. Валидация полей (email, пароль ≥6 символов, checkbox)
2. POST `/api/v1/auth/register` с `{email, password, name}`
3. Получение `access_token` и `user`
4. Сохранение в `localStorage` и `cookie`
5. Восстановление данных из `pending_upd_data`
6. Автоматический вызов `generateAndDownloadPDF()`
7. Перезагрузка страницы для обновления UI

## Измененные файлы

1. **backend/app/dashboard/upd.py**
   - Убрана проверка `require_auth()` из `upd_create()`
   - Сохранена проверка для `upd_edit()` и `upd_view()`

2. **backend/app/pages/home.py**
   - Редирект `/upd-create` всегда на `/dashboard/upd/create/`

3. **backend/app/templates/public/home.html**
   - CTA кнопка изменена на `/dashboard/upd/create/`
   - Текст: "Создать УПД бесплатно" + "Без регистрации"

4. **backend/app/templates/dashboard/upd/create.html**
   - Добавлена проверка auth в `generateAndDownloadPDF()`
   - Добавлено модальное окно `#guestRegistrationModal`
   - Добавлена функция `getCookie()`
   - Добавлен обработчик формы регистрации

## Тестирование

### Сценарий 1: Гость создает УПД

1. Откройте http://localhost:8000
2. Нажмите "Создать УПД бесплатно"
3. Заполните форму УПД (продавец, покупатель, товары)
4. Нажмите кнопку "Сохранить и скачать"
5. **Ожидание:** появится модальное окно регистрации
6. Заполните email, пароль, примите terms
7. Нажмите "Зарегистрироваться"
8. **Ожидание:** PDF скачается автоматически, страница перезагрузится
9. **Проверка:** документ появится в /dashboard/documents/

### Сценарий 2: Авторизованный пользователь

1. Войдите в аккаунт
2. Перейдите на /dashboard/upd/create/
3. Заполните форму УПД
4. Нажмите "Сохранить и скачать"
5. **Ожидание:** PDF генерируется сразу, без модалки

### Сценарий 3: Гость закрывает модалку

1. Заполните форму как гость
2. Нажмите "Сохранить и скачать"
3. Закройте модалку (крестик)
4. **Проверка:** данные формы сохранены в `localStorage.pending_upd_data`
5. Можно снова нажать "Сохранить" → модалка откроется с сохраненными данными

## API Endpoints

### POST /api/v1/auth/register

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "Иван Иванов"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Иван Иванов",
    "is_verified": false
  }
}
```

**Response (400):**
```json
{
  "detail": "Пользователь с таким email уже существует"
}
```

### POST /api/v1/documents/upd/generate

**Headers:**
```
Authorization: Bearer <token>
```

**Request:** JSON с данными УПД

**Response:** PDF file (binary)

## Преимущества подхода

1. **Низкий барьер входа** - гость начинает работать без регистрации
2. **Высокая конверсия** - пользователь уже инвестировал время в заполнение
3. **Прозрачность** - четко видно что именно даст регистрация
4. **Автосохранение** - документ не теряется после регистрации
5. **UX без разрывов** - плавный переход от гостя к пользователю

## Возможные улучшения

1. Добавить предзаполнение email из формы (если есть поле email в УПД)
2. Сохранять pending_upd_data с timestamp и очищать старые записи
3. Добавить кнопку "У меня уже есть аккаунт" в модалке → переход на /login
4. После регистрации показывать onboarding tour
5. Email верификация с автоматическим редиректом обратно на УПД
