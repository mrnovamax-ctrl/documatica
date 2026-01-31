# Documatica - Dev/Prod Окружения

## Структура

```
/opt/beget/documatica/         ← PRODUCTION (порт 8000)
/opt/beget/documatica-dev/     ← DEVELOPMENT (порт 8003)
```

## Доступы

| Окружение | Backend URL | Database Port | Container Prefix |
|-----------|-------------|---------------|------------------|
| **Production** | http://localhost:8000 | 5432 | `documatica-` |
| **Development** | http://localhost:8003 | 5435 | `documatica-dev-` |

## Деплой

### Production (ПРОД)
```bash
cd /opt/beget/documatica
./deploy-prod.sh
```

**Что делает:**
- Создаёт бэкап базы данных
- Обновляет код из Git (ветка `main`)
- Перезапускает backend
- Проверяет работу сервиса

### Development (ТЕСТ)
```bash
cd /opt/beget/documatica-dev
./deploy-dev.sh
```

**Что делает:**
- Обновляет код из Git (ветка `develop` или `main`)
- Пересобирает и перезапускает контейнеры
- Проверяет работу dev-сервиса

## Рабочий процесс (Workflow)

### 1. Разработка фичи

```bash
# 1. Переключись на dev-окружение
cd /opt/beget/documatica-dev

# 2. Создай ветку для фичи
git checkout -b feature/new-save-logic

# 3. Меняй код в /opt/beget/documatica-dev/backend/

# 4. Перезапускай dev-окружение
./deploy-dev.sh

# 5. Тестируй на http://localhost:8003
```

### 2. Тестирование

```bash
# Включи feature flag в dev
cd /opt/beget/documatica-dev
nano docker-compose.yml  # Измени FEATURE_NEW_SAVE_LOGIC=true

# Перезапусти
docker-compose restart backend

# Тестируй функционал
```

### 3. Деплой на прод

```bash
# 1. Закоммить и запушить изменения
cd /opt/beget/documatica-dev
git add .
git commit -m "feat: новая логика сохранения"
git push origin feature/new-save-logic

# 2. Сделать merge в main (через PR или локально)
git checkout main
git merge feature/new-save-logic
git push origin main

# 3. Обновить прод
cd /opt/beget/documatica
./deploy-prod.sh
```

## Управление контейнерами

### Production
```bash
cd /opt/beget/documatica

# Посмотреть логи
docker logs -f documatica-backend

# Перезапустить backend
docker-compose restart backend

# Полный перезапуск
docker-compose down
docker-compose up -d

# Подключиться к БД
docker exec -it documatica-db psql -U postgres -d documatica
```

### Development
```bash
cd /opt/beget/documatica-dev

# Посмотреть логи
docker logs -f documatica-dev-backend

# Перезапустить backend
docker-compose restart backend

# Полный перезапуск с rebuild
docker-compose down
docker-compose up -d --build

# Подключиться к БД
docker exec -it documatica-dev-db psql -U postgres -d documatica_dev
```

## Feature Flags

Feature flags управляются через переменные окружения в `docker-compose.yml`:

```yaml
environment:
  - FEATURE_NEW_SAVE_LOGIC=false  # По умолчанию выключен
```

**Включение на dev:**
```bash
cd /opt/beget/documatica-dev
# Изменить FEATURE_NEW_SAVE_LOGIC=true в docker-compose.yml
docker-compose restart backend
```

**Включение на prod:**
```bash
cd /opt/beget/documatica
# Изменить FEATURE_NEW_SAVE_LOGIC=true в docker-compose.yml
docker-compose restart backend
```

## Откат изменений

### Откатить код (Git)
```bash
cd /opt/beget/documatica
git log --oneline  # Найди SHA коммита
git revert <SHA>
git push origin main
./deploy-prod.sh
```

### Восстановить БД из бэкапа
```bash
cd /opt/beget/documatica/backups
ls -lh  # Найди нужный бэкап

# Восстановить
docker exec -i documatica-db psql -U postgres -d documatica < db_backup_20260130_150000.sql
```

## Мониторинг

```bash
# Статус контейнеров
docker ps

# Использование ресурсов
docker stats documatica-backend documatica-dev-backend

# Проверка работы
curl http://localhost:8000/health  # prod
curl http://localhost:8003/health  # dev
```

## Безопасность

- **НИКОГДА** не коммитить `.env` файлы
- **ВСЕГДА** делать бэкап БД перед production деплоем
- **ТЕСТИРОВАТЬ** на dev перед деплоем на прод
- Feature flags по умолчанию **выключены** (false)

## Troubleshooting

### Backend не запускается
```bash
# Посмотреть логи
docker logs documatica-backend

# Проверить синтаксис Python
cd /opt/beget/documatica/backend
python -m py_compile app/main.py
```

### База данных не отвечает
```bash
# Проверить статус
docker exec documatica-db pg_isready -U postgres

# Перезапустить БД
docker-compose restart db
```

### Порт занят
```bash
# Найти что занимает порт
netstat -tlnp | grep :8000

# Освободить (если нужно)
docker stop <container_name>
```

---

**Создано:** 30 января 2026  
**Автор:** GitHub Copilot
