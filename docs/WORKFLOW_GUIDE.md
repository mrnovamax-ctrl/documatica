# 🚀 Documatica: Полное руководство Dev → Production

> **Актуально на:** 7 февраля 2026

---

## 📍 Где что находится

```
📂 /opt/beget/
├── documatica/          ✅ PRODUCTION
│   ├── .git/           (main ветка)
│   ├── backend/        (код приложения)
│   └── docker-compose.yml
│
└── documatica-dev/     🧪 DEVELOPMENT  
    ├── .git/          (main ветка)
    ├── backend/       (код приложения)
    └── docker-compose.yml (не в Git!)
```

**Важно:** Оба окружения используют одинаковый код из Git, но разные БД и настройки.

---

## 🌐 URL и доступы

| Окружение | Домен | Локальный доступ | База данных |
|-----------|-------|------------------|-------------|
| **Production** | https://oplatanalogov.ru | http://localhost:8000 | documatica (порт 5432) |
| **Development** | https://dev.oplatanalogov.ru | http://localhost:8003 | documatica_dev (порт 5435) |

---

## 🎯 Простой workflow (3 шага)

### Шаг 1️⃣: Работаем на DEV

```bash
# Переходим в dev окружение
cd /opt/beget/documatica-dev

# Обновляем код
git pull origin main

# Вносим изменения (редактируем файлы)
nano backend/app/pages/home.py

# Перезапускаем dev сервер
docker-compose restart backend

# ✅ Проверяем результат на https://dev.oplatanalogov.ru
```

### Шаг 2️⃣: Сохраняем в Git

```bash
# Смотрим что изменилось
git status

# Добавляем файлы
git add backend/app/pages/home.py

# Коммитим с понятным описанием
git commit -m "feat: добавил фильтр по категориям на главной"

# Отправляем в репозиторий
git push origin main
```

### Шаг 3️⃣: Публикуем на PRODUCTION

```bash
# Переходим в production
cd /opt/beget/documatica

# Запускаем deploy скрипт
./deploy-prod.sh

# ✅ Готово! Проверяем на https://oplatanalogov.ru
```

Вот и всё! 🎉

---

## 📚 Практические примеры

### Пример 1: Правим текст на странице

```bash
# 1️⃣ DEV
cd /opt/beget/documatica-dev
nano backend/app/templates/public/home.html
# Меняем текст "Старый заголовок" → "Новый заголовок"

docker-compose restart backend
# Проверяем на dev.oplatanalogov.ru ✅

# 2️⃣ GIT
git add backend/app/templates/public/home.html
git commit -m "fix: обновил заголовок на главной"
git push origin main

# 3️⃣ PROD
cd /opt/beget/documatica
./deploy-prod.sh
# Проверяем на oplatanalogov.ru ✅
```

### Пример 2: Добавляем новую страницу

```bash
# 1️⃣ DEV - Создаём файлы
cd /opt/beget/documatica-dev

# Создаём роутер
cat > backend/app/pages/services.py << 'PYEOF'
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates

router = APIRouter()

@router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="public/services.html",
        context={"title": "Наши услуги"}
    )
PYEOF

# Создаём шаблон
cat > backend/app/templates/public/services.html << 'HTMLEOF'
{% extends "base_public.html" %}
{% block title %}Наши услуги{% endblock %}
{% block content %}
<section class="py-24">
  <div class="container">
    <h1 class="docu-h2 mb-8">Наши услуги</h1>
    <p class="docu-body">Текст страницы...</p>
  </div>
</section>
{% endblock %}
HTMLEOF

# Регистрируем роутер
nano backend/app/main.py
# Добавляем: from app.pages import services
# Добавляем: app.include_router(services.router)

# Тестируем
docker-compose restart backend
# Открываем https://dev.oplatanalogov.ru/services ✅

# 2️⃣ GIT
git add backend/app/pages/services.py \
        backend/app/templates/public/services.html \
        backend/app/main.py
git commit -m "feat: добавил страницу услуг"
git push origin main

# 3️⃣ PROD
cd /opt/beget/documatica
./deploy-prod.sh
```

### Пример 3: Работа с базой данных

```bash
# 1️⃣ DEV - Добавляем новую модель
cd /opt/beget/documatica-dev

# Редактируем модели
nano backend/app/models.py
# Добавляем новую модель, например:
# class Review(Base):
#     __tablename__ = "reviews"
#     ...

# Создаём миграцию
docker exec documatica-dev-backend sh -c \
  'cd /app && alembic revision --autogenerate -m "Add reviews table"'

# Применяем миграцию на DEV БД
docker exec documatica-dev-backend sh -c \
  'cd /app && DATABASE_URL="postgresql://postgres:postgres@db:5432/documatica_dev" alembic upgrade head'

# Проверяем что таблица создалась
docker exec -it documatica-dev-db psql -U postgres documatica_dev -c "\dt reviews"

# Тестируем новый функционал на dev.oplatanalogov.ru ✅

# 2️⃣ GIT
git add backend/app/models.py backend/alembic/versions/*.py
git commit -m "feat: добавил таблицу отзывов"
git push origin main

# 3️⃣ PROD - deploy-prod.sh автоматически применит миграции!
cd /opt/beget/documatica
./deploy-prod.sh
```

---

## 🆘 Частые вопросы

### Q: Нужно ли создавать отдельную ветку для фичи?

**A:** Не обязательно для маленьких изменений. Можно работать прямо в main:

```bash
# Простой подход (для небольших изменений)
cd /opt/beget/documatica-dev
git pull origin main
# Вносим изменения
git add .
git commit -m "..."
git push origin main
cd /opt/beget/documatica
./deploy-prod.sh
```

### Q: Как откатить изменения если сломал production?

```bash
cd /opt/beget/documatica

# 1. Смотрим последние коммиты
git log --oneline -5

# 2. Откатываемся на предыдущий
git reset --hard HEAD~1  # или конкретный хэш

# 3. Перезапускаем
docker-compose restart backend

# 4. Если нужно откатить миграцию БД
docker exec documatica-backend sh -c \
  'cd /app && DATABASE_URL="postgresql://postgres:postgres@db:5432/documatica" alembic downgrade -1'
```

### Q: Как посмотреть логи если что-то не работает?

```bash
# Production
docker logs documatica-backend --tail 100 -f

# Development
docker logs documatica-dev-backend --tail 100 -f

# БД логи
docker logs documatica-db
docker logs documatica-dev-db
```

### Q: Нужно ли перезапускать весь docker-compose?

**A:** Обычно достаточно перезапустить только backend:

```bash
# Быстро (только backend)
docker-compose restart backend

# Если нужен rebuild (изменили requirements.txt)
docker-compose up -d --build backend

# Полный перезапуск (редко нужен)
docker-compose down
docker-compose up -d
```

### Q: Где находятся данные пользователей?

```bash
# Production БД
docker exec -it documatica-db psql -U postgres documatica

# Список таблиц
\dt

# Посмотреть пользователей
SELECT id, email, created_at FROM users;
```

### Q: Как обновить только CSS/JS без перезапуска?

**A:** Статические файлы обновляются автоматически. Просто:
1. Измени файл в `/backend/app/static/`
2. Обнови страницу в браузере (Ctrl+F5 для сброса кэша)

Если изменения не видны - добавь cache busting:
```html
<!-- Было -->
<link rel="stylesheet" href="/static/css/home.css?v=2.5">

<!-- Стало -->
<link rel="stylesheet" href="/static/css/home.css?v=2.6">
```

---

## 🔐 Важные отличия Dev vs Prod

| Параметр | Development | Production |
|----------|-------------|------------|
| URL | https://dev.oplatanalogov.ru | https://oplatanalogov.ru |
| База данных | documatica_dev | documatica |
| Debug режим | ✅ Включён | ❌ Выключен |
| Платежи | 🧪 Mock/Test | 💰 Реальные |
| Email теги | [DEV] в теме | Без тегов |
| Ошибки | Показываются полностью | Скрываются |

---

## ⚡ Быстрые команды

```bash
# === DEVELOPMENT ===

# Полный деплой dev
cd /opt/beget/documatica-dev && ./deploy-dev.sh

# Перезапуск backend
cd /opt/beget/documatica-dev && docker-compose restart backend

# Логи в реальном времени
docker logs documatica-dev-backend -f

# Подключиться к БД
docker exec -it documatica-dev-db psql -U postgres documatica_dev


# === PRODUCTION ===

# Полный деплой prod
cd /opt/beget/documatica && ./deploy-prod.sh

# Только обновить код без перезапуска
cd /opt/beget/documatica && git pull origin main

# Логи
docker logs documatica-backend --tail 100

# Бэкап БД
docker exec documatica-db pg_dump -U postgres documatica > backup_$(date +%Y%m%d).sql

# Откат на 1 коммит назад
cd /opt/beget/documatica && git reset --hard HEAD~1 && docker-compose restart backend
```

---

## 📝 Checklist перед PROD деплоем

Перед запуском `./deploy-prod.sh`:

- [ ] ✅ Протестировано на https://dev.oplatanalogov.ru
- [ ] ✅ Все изменения закоммичены и запушены в main
- [ ] ✅ Миграции БД работают на dev
- [ ] ✅ Нет хардкода паролей/токенов
- [ ] ✅ Убраны console.log / print отладки
- [ ] ✅ Обновлён cache busting для CSS/JS (если нужно)

---

## 🎓 Типичный рабочий день

**Утро:**
```bash
cd /opt/beget/documatica-dev
git pull origin main
```

**В течение дня (каждая фича):**
```bash
# Правим код
nano backend/app/...

# Тестируем на dev
docker-compose restart backend

# Коммитим
git add .
git commit -m "feat: ..."
git push origin main
```

**Вечер (если всё ок на dev):**
```bash
cd /opt/beget/documatica
./deploy-prod.sh
```

---

## 🔥 Emergency: Что делать если всё сломалось

### Production вернул 500 ошибку после деплоя

```bash
# 1. Смотрим логи
docker logs documatica-backend --tail 50

# 2. Быстрый откат
cd /opt/beget/documatica
git reset --hard HEAD~1
docker-compose restart backend

# 3. Проверяем
curl -I https://oplatanalogov.ru
```

### База данных сломана после миграции

```bash
# 1. Смотрим доступные бэкапы
ls -lh /opt/beget/documatica/backups/

# 2. Восстанавливаем последний
docker exec documatica-db psql -U postgres documatica < backups/db_backup_LATEST.sql

# 3. Откатываем миграцию
docker exec documatica-backend sh -c \
  'cd /app && DATABASE_URL="postgresql://postgres:postgres@db:5432/documatica" alembic downgrade -1'
```

---

## 📞 Контакты и полезные ссылки

- **Production**: https://oplatanalogov.ru
- **Development**: https://dev.oplatanalogov.ru  
- **Git репозиторий**: /opt/beget/documatica/.git
- **Документация**: /opt/beget/documatica/docs/

**Дополнительная документация:**
- [Архитектура проекта](architecture-v2.md)
- [CSS Manifest](../CSS_MANIFEST.md)
- [API документация](http://localhost:8000/docs)

---

**Последнее обновление:** 7 февраля 2026  
**Статус:** ✅ Актуально
