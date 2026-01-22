#!/bin/bash
#===============================================================================
# МИГРАЦИЯ НА ИЗОЛИРОВАННУЮ АРХИТЕКТУРУ
# 
# Этот скрипт выполняет миграцию с минимальным downtime:
# 1. Создает бэкапы всех данных
# 2. Запускает Traefik в отдельном проекте
# 3. Переносит данные Nexus в отдельный проект
# 4. Переключает n8n на новую конфигурацию
# 5. Переключает Documatica на новую конфигурацию
#
# ВАЖНО: Запускать под root или через sudo
#===============================================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Директории
BACKUP_DIR="/opt/beget/backups/20260120_migration"
TRAEFIK_DIR="/opt/beget/traefik"
NEXUS_DIR="/opt/beget/nexus"
N8N_DIR="/opt/beget/n8n"
DOCUMATICA_DIR="/opt/beget/documatica"

# Логирование
log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"; }
step() { echo -e "\n${BLUE}========== $1 ==========${NC}\n"; }

#===============================================================================
# ШАГ 0: ПРОВЕРКИ
#===============================================================================
check_prerequisites() {
    step "ШАГ 0: Проверка предусловий"
    
    # Проверка root
    if [ "$EUID" -ne 0 ]; then 
        error "Запустите скрипт от root: sudo ./migrate.sh"
        exit 1
    fi
    
    # Проверка бэкапов
    if [ ! -d "$BACKUP_DIR" ]; then
        error "Бэкапы не найдены в $BACKUP_DIR"
        error "Сначала выполните: ./backup-all.sh"
        exit 1
    fi
    
    # Проверка файлов
    local required_files=(
        "$BACKUP_DIR/n8n_db.sql"
        "$BACKUP_DIR/nexus_db.sql"
        "$BACKUP_DIR/nexus_dev_db.sql"
        "$TRAEFIK_DIR/docker-compose.yml"
        "$NEXUS_DIR/docker-compose.yml"
        "$N8N_DIR/docker-compose.new.yml"
        "$DOCUMATICA_DIR/docker-compose.isolated.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            error "Файл не найден: $file"
            exit 1
        fi
    done
    
    log "Все проверки пройдены"
}

#===============================================================================
# ШАГ 1: ЗАПУСК TRAEFIK
#===============================================================================
start_traefik() {
    step "ШАГ 1: Запуск изолированного Traefik"
    
    # Копируем сертификаты из старого Traefik
    if [ -d "$BACKUP_DIR/traefik_data" ]; then
        log "Копирование SSL сертификатов..."
        mkdir -p "$TRAEFIK_DIR/traefik_data"
        cp -r "$BACKUP_DIR/traefik_data/"* "$TRAEFIK_DIR/traefik_data/" 2>/dev/null || true
    fi
    
    # Останавливаем старый Traefik
    log "Останавливаем старый Traefik..."
    docker stop n8n-traefik-1 2>/dev/null || true
    
    # Запускаем новый Traefik
    log "Запускаем новый Traefik..."
    cd "$TRAEFIK_DIR"
    docker compose up -d
    
    # Ждем запуска
    sleep 5
    
    # Проверка
    if docker ps | grep -q "traefik"; then
        log "Traefik запущен успешно"
    else
        error "Traefik не запустился!"
        exit 1
    fi
}

#===============================================================================
# ШАГ 2: МИГРАЦИЯ NEXUS
#===============================================================================
migrate_nexus() {
    step "ШАГ 2: Миграция Nexus в отдельный проект"
    
    # Создаем .env файл
    log "Создание .env файла для Nexus..."
    if [ -f "$BACKUP_DIR/n8n.env" ]; then
        # Извлекаем нужные переменные из старого .env
        grep -E "^(JIRA_|OPENAI_|SECRET_KEY|ADMIN_PASSWORD|GOOGLE_|TELEGRAM_)" "$BACKUP_DIR/n8n.env" > "$NEXUS_DIR/.env" || true
        
        # Добавляем PostgreSQL credentials
        cat >> "$NEXUS_DIR/.env" << 'EOF'
POSTGRES_USER=nexus
POSTGRES_PASSWORD=nexus_L0jfr1ZDwu5KZNO
EOF
    fi
    
    # Копируем migrations
    log "Копирование миграций..."
    if [ -d "$N8N_DIR/migrations" ]; then
        cp -r "$N8N_DIR/migrations" "$NEXUS_DIR/"
    else
        mkdir -p "$NEXUS_DIR/migrations"
    fi
    
    # Останавливаем старый Nexus
    log "Останавливаем старые контейнеры Nexus..."
    docker stop n8n-nexus-1 n8n-nexus-dev-1 2>/dev/null || true
    
    # Запускаем новую PostgreSQL для Nexus
    log "Запускаем PostgreSQL для Nexus..."
    cd "$NEXUS_DIR"
    docker compose up -d postgres
    
    # Ждем пока PostgreSQL будет готова
    log "Ожидание готовности PostgreSQL..."
    sleep 10
    for i in {1..30}; do
        if docker exec nexus-postgres pg_isready -U nexus -d nexus > /dev/null 2>&1; then
            log "PostgreSQL готова"
            break
        fi
        sleep 2
    done
    
    # Восстанавливаем данные
    log "Восстановление данных nexus..."
    
    # Сначала нужно создать структуру, затем данные
    # Меняем владельца в дампе с root на nexus
    sed 's/Owner: root/Owner: nexus/g; s/OWNER TO root/OWNER TO nexus/g' \
        "$BACKUP_DIR/nexus_db.sql" | \
        docker exec -i nexus-postgres psql -U nexus -d nexus
    
    log "Восстановление данных nexus_dev..."
    sed 's/Owner: root/Owner: nexus/g; s/OWNER TO root/OWNER TO nexus/g' \
        "$BACKUP_DIR/nexus_dev_db.sql" | \
        docker exec -i nexus-postgres psql -U nexus -d nexus_dev
    
    # Копируем uploads
    log "Копирование uploads..."
    if [ -d "$N8N_DIR/nexus_storage" ]; then
        mkdir -p "$NEXUS_DIR/uploads"
        cp -r "$N8N_DIR/nexus_storage/"* "$NEXUS_DIR/uploads/" 2>/dev/null || true
    fi
    
    # Запускаем Nexus
    log "Запускаем Nexus..."
    docker compose up -d
    
    # Проверка
    sleep 10
    if docker ps | grep -q "nexus-app"; then
        log "Nexus запущен успешно"
        
        # Проверяем healthcheck
        for i in {1..12}; do
            if docker inspect nexus-app --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
                log "Nexus healthy"
                break
            fi
            sleep 5
        done
    else
        error "Nexus не запустился!"
        docker logs nexus-app 2>&1 | tail -20
    fi
}

#===============================================================================
# ШАГ 3: ПЕРЕКЛЮЧЕНИЕ N8N
#===============================================================================
switch_n8n() {
    step "ШАГ 3: Переключение n8n на новую конфигурацию"
    
    cd "$N8N_DIR"
    
    # Бэкап текущего docker-compose
    log "Бэкап текущей конфигурации..."
    cp docker-compose.yml docker-compose.old.yml
    
    # Останавливаем старые сервисы (кроме postgres - данные нужны)
    log "Останавливаем n8n сервисы..."
    docker compose stop n8n n8n-worker redis qdrant 2>/dev/null || true
    
    # Переименовываем конфигурацию
    log "Применяем новую конфигурацию..."
    mv docker-compose.yml docker-compose.backup.yml
    mv docker-compose.new.yml docker-compose.yml
    
    # Запускаем с новой конфигурацией
    log "Запускаем n8n с новой конфигурацией..."
    docker compose up -d
    
    # Проверка
    sleep 10
    if docker ps | grep -q "n8n-app"; then
        log "n8n запущен успешно"
    else
        error "n8n не запустился! Откатываемся..."
        mv docker-compose.yml docker-compose.new.yml
        mv docker-compose.backup.yml docker-compose.yml
        docker compose up -d
        exit 1
    fi
}

#===============================================================================
# ШАГ 4: ПЕРЕКЛЮЧЕНИЕ DOCUMATICA
#===============================================================================
switch_documatica() {
    step "ШАГ 4: Переключение Documatica на изолированную конфигурацию"
    
    cd "$DOCUMATICA_DIR"
    
    # Бэкап текущего docker-compose
    log "Бэкап текущей конфигурации..."
    cp docker-compose.yml docker-compose.old.yml
    
    # Останавливаем текущие контейнеры
    log "Останавливаем Documatica..."
    docker compose down
    
    # Переименовываем конфигурацию
    log "Применяем изолированную конфигурацию..."
    mv docker-compose.yml docker-compose.legacy.yml
    mv docker-compose.isolated.yml docker-compose.yml
    
    # Запускаем
    log "Запускаем Documatica..."
    docker compose up -d
    
    # Проверка
    sleep 10
    if docker ps | grep -q "documatica-backend"; then
        log "Documatica запущен успешно"
    else
        error "Documatica не запустился! Откатываемся..."
        mv docker-compose.yml docker-compose.isolated.yml
        mv docker-compose.legacy.yml docker-compose.yml
        docker compose up -d
        exit 1
    fi
}

#===============================================================================
# ШАГ 5: ПРОВЕРКА ВСЕЙ СИСТЕМЫ
#===============================================================================
verify_system() {
    step "ШАГ 5: Проверка всей системы"
    
    echo ""
    log "Проверка контейнеров:"
    echo ""
    
    # Traefik
    if docker ps | grep -q "traefik"; then
        echo -e "  ${GREEN}[OK]${NC} Traefik"
    else
        echo -e "  ${RED}[FAIL]${NC} Traefik"
    fi
    
    # n8n
    if docker ps | grep -q "n8n-app"; then
        echo -e "  ${GREEN}[OK]${NC} n8n"
    else
        echo -e "  ${RED}[FAIL]${NC} n8n"
    fi
    
    # Nexus
    if docker ps | grep -q "nexus-app"; then
        echo -e "  ${GREEN}[OK]${NC} Nexus"
    else
        echo -e "  ${RED}[FAIL]${NC} Nexus"
    fi
    
    # Nexus Dev
    if docker ps | grep -q "nexus-dev-app"; then
        echo -e "  ${GREEN}[OK]${NC} Nexus Dev"
    else
        echo -e "  ${RED}[FAIL]${NC} Nexus Dev"
    fi
    
    # Documatica
    if docker ps | grep -q "documatica-backend"; then
        echo -e "  ${GREEN}[OK]${NC} Documatica"
    else
        echo -e "  ${RED}[FAIL]${NC} Documatica"
    fi
    
    echo ""
    log "Проверка доменов (curl):"
    echo ""
    
    # Проверка доменов
    for domain in "dnt-ai.ru" "nexus.dnt-ai.ru" "dev.nexus.dnt-ai.ru" "new.oplatanalogov.ru"; do
        status=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain" --max-time 10 2>/dev/null || echo "000")
        if [ "$status" = "200" ] || [ "$status" = "302" ] || [ "$status" = "301" ]; then
            echo -e "  ${GREEN}[OK]${NC} https://$domain (HTTP $status)"
        else
            echo -e "  ${RED}[FAIL]${NC} https://$domain (HTTP $status)"
        fi
    done
    
    echo ""
    log "Проверка баз данных:"
    echo ""
    
    # n8n DB
    if docker exec n8n-postgres psql -U root -d n8n -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} n8n PostgreSQL"
    else
        echo -e "  ${RED}[FAIL]${NC} n8n PostgreSQL"
    fi
    
    # Nexus DB
    if docker exec nexus-postgres psql -U nexus -d nexus -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} Nexus PostgreSQL"
    else
        echo -e "  ${RED}[FAIL]${NC} Nexus PostgreSQL"
    fi
    
    # Documatica DB
    if docker exec documatica-db psql -U postgres -d documatica -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} Documatica PostgreSQL"
    else
        echo -e "  ${RED}[FAIL]${NC} Documatica PostgreSQL"
    fi
}

#===============================================================================
# ШАГ 6: ОЧИСТКА
#===============================================================================
cleanup() {
    step "ШАГ 6: Очистка старых ресурсов"
    
    log "Удаление неиспользуемых контейнеров и сетей..."
    
    # Удаляем старые контейнеры
    docker rm n8n-traefik-1 n8n-nexus-1 n8n-nexus-dev-1 2>/dev/null || true
    
    # НЕ удаляем старую сеть n8n_n8n-network пока не убедимся что все работает
    warn "Старая сеть n8n_n8n-network сохранена для возможности отката"
    warn "Удалите вручную после проверки: docker network rm n8n_n8n-network"
    
    log "Очистка завершена"
}

#===============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
#===============================================================================
main() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     МИГРАЦИЯ НА ИЗОЛИРОВАННУЮ АРХИТЕКТУРУ                   ║${NC}"
    echo -e "${BLUE}║     n8n + Nexus + Documatica                                 ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    warn "Это приведет к кратковременному downtime (~2-5 минут)"
    echo ""
    read -p "Продолжить? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Отменено"
        exit 0
    fi
    
    check_prerequisites
    start_traefik
    migrate_nexus
    switch_n8n
    switch_documatica
    verify_system
    cleanup
    
    step "МИГРАЦИЯ ЗАВЕРШЕНА"
    
    echo ""
    log "Новая архитектура:"
    echo ""
    echo "  /opt/beget/traefik/    - Централизованный reverse proxy"
    echo "  /opt/beget/n8n/        - n8n (изолированный)"
    echo "  /opt/beget/nexus/      - Nexus (изолированный)"
    echo "  /opt/beget/documatica/ - Documatica (изолированный)"
    echo ""
    log "Все бэкапы сохранены в: $BACKUP_DIR"
    echo ""
}

# Запуск
main "$@"
