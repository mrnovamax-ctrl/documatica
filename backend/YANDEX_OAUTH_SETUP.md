# Настройка Яндекс OAuth для Documatica

## Шаг 1: Создание приложения в Яндекс OAuth

1. Перейдите на https://oauth.yandex.ru/client/new
2. Заполните форму:
   - **Название**: Documatica (или любое другое)
   - **Платформы**: Выберите "Веб-сервисы"
   - **Callback URL**: `https://oplatanalogov.ru/auth/yandex/callback`
   - **Доступ к данным**:
     - ✅ Доступ к email адресу
     - ✅ Доступ к аватару
     - ✅ Доступ к имени пользователя

3. Нажмите "Создать приложение"

## Шаг 2: Получение Client ID и Client Secret

После создания приложения вы увидите:
- **ID приложения** (Client ID) - скопируйте его
- **Пароль приложения** (Client Secret) - скопируйте его

## Шаг 3: Настройка .env файла

Откройте файл `/opt/beget/documatica/backend/.env` и замените:

```env
YANDEX_CLIENT_ID=your_client_id_here
YANDEX_CLIENT_SECRET=your_client_secret_here
```

На ваши реальные значения из Яндекс OAuth.

## Шаг 4: Перезапуск сервера

После изменения .env перезапустите сервер:

```bash
cd /opt/beget/documatica/backend
pkill -f "uvicorn app.main:app"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
```

## Шаг 5: Тестирование

1. Откройте https://oplatanalogov.ru/login/
2. Нажмите кнопку "Войти через Яндекс"
3. Вы должны быть перенаправлены на страницу авторизации Яндекс
4. После подтверждения вы вернётесь на сайт как авторизованный пользователь

## Исправленная проблема

### Была ошибка:
```
invalid_scope
```

### Причина:
В коде запрашивались несуществующие scopes `"login:email login:info"`.

### Решение:
Убрали параметр `scope` из запроса. Для Яндекс OAuth:
- Базовый доступ к email и данным пользователя предоставляется автоматически
- Дополнительные разрешения настраиваются в панели управления приложением

## Проверка настроек в Яндекс OAuth

Убедитесь, что в настройках вашего приложения на https://oauth.yandex.ru указаны:

1. **Callback URL**: `https://oplatanalogov.ru/auth/yandex/callback`
   - ❌ НЕТ: `http://localhost:8000/...`
   - ❌ НЕТ: URL с другим доменом
   - ✅ ДА: `https://oplatanalogov.ru/auth/yandex/callback`

2. **Платформы**: Веб-сервисы

3. **Доступы** (должны быть включены):
   - Email адрес
   - Имя пользователя
   - Аватар (опционально)

## Отладка

Если всё ещё возникают проблемы:

1. Проверьте логи сервера:
   ```bash
   tail -f /tmp/uvicorn.log
   ```

2. Проверьте, что переменные окружения загружены:
   ```bash
   cd /opt/beget/documatica/backend
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('YANDEX_CLIENT_ID:', os.getenv('YANDEX_CLIENT_ID'))"
   ```

3. Проверьте URL редиректа в коде ([oauth.py](app/api/oauth.py)):
   ```python
   YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "https://oplatanalogov.ru/auth/yandex/callback")
   ```

## Важные замечания

- **HTTPS обязателен** - Яндекс OAuth работает только через HTTPS в production
- **Точное совпадение URL** - Callback URL в настройках приложения должен **точно** совпадать с `YANDEX_REDIRECT_URI` в .env
- **Без trailing slash** - URL должен быть без `/` в конце
