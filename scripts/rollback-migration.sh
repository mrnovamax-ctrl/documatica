#!/bin/bash
#===============================================================================
# ОТКАТ МИГРАЦИИ
# 
# Возвращает систему к исходному состоянию если что-то пошло не так
#===============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"; }

echo ""
echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                    ОТКАТ МИГРАЦИИ                            ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

warn "Это вернет систему к исходному состоянию"
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

log "Останавливаем новые сервисы..."

# Останавливаем новый Traefik
docker stop traefik 2>/dev/null || true
docker rm traefik 2>/dev/null || true

# Останавливаем новый Nexus
cd /opt/beget/nexus && docker compose down 2>/dev/null || true

# Откатываем n8n
cd /opt/beget/n8n
if [ -f docker-compose.backup.yml ]; then
    log "Откатываем конфигурацию n8n..."
    docker compose down 2>/dev/null || true
    mv docker-compose.yml docker-compose.new.yml 2>/dev/null || true
    mv docker-compose.backup.yml docker-compose.yml
    docker compose up -d
fi

# Откатываем Documatica
cd /opt/beget/documatica
if [ -f docker-compose.legacy.yml ]; then
    log "Откатываем конфигурацию Documatica..."
    docker compose down 2>/dev/null || true
    mv docker-compose.yml docker-compose.isolated.yml 2>/dev/null || true
    mv docker-compose.legacy.yml docker-compose.yml
    docker compose up -d
fi

log "Откат завершен"
log "Проверьте работу сервисов: docker ps"
