#!/bin/bash
# Deploy-скрипт для PRODUCTION окружения

set -e

PROJECT_DIR="/opt/beget/documatica"
BRANCH="main"

echo "==================================="
echo "🚀 PRODUCTION DEPLOY"
echo "==================================="

cd $PROJECT_DIR

# 1. Бэкап базы данных
echo "📦 Создаю бэкап базы данных..."
BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backups
docker exec documatica-db pg_dump -U postgres documatica > $BACKUP_FILE
echo "✅ Бэкап сохранён: $BACKUP_FILE"

# 2. Обновление кода
echo "🔄 Обновляю код из Git..."
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
echo "✅ Код обновлён"

# 3. Перезапуск контейнеров
echo "🔄 Перезапускаю backend..."
docker-compose restart backend
echo "✅ Backend перезапущен"

# 4. Проверка здоровья
echo "🏥 Проверяю работу сервиса..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "✅ Сервис работает (HTTP $HTTP_CODE)"
else
    echo "⚠️  Предупреждение: HTTP $HTTP_CODE"
fi

# 5. Показать последний коммит
echo ""
echo "📝 Последний коммит:"
git log -1 --oneline
echo ""
echo "==================================="
echo "✅ PRODUCTION DEPLOY ЗАВЕРШЁН"
echo "==================================="
