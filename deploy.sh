#!/bin/bash

# deploy.sh - Автоматический скрипт деплоя OZON Scraper
# Использование: ./deploy.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Заголовок
echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║   OZON Scraper Deployment Script      ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка наличия .env файла
log_info "Checking environment file..."
if [ ! -f .env ]; then
    log_error ".env file not found!"
    log_info "Please create .env file with required variables."
    log_info "See docs/VPS_DEPLOYMENT.md for details."
    exit 1
fi
log_success ".env file found"

# Проверка наличия Docker
log_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed!"
    log_info "Please install Docker first:"
    log_info "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi
log_success "Docker is installed ($(docker --version))"

# Проверка наличия Docker Compose
log_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed!"
    log_info "Please install Docker Compose first:"
    log_info 'sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
    log_info "sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi
log_success "Docker Compose is installed ($(docker-compose --version))"

# Проверка docker-compose.prod.yml
log_info "Checking docker-compose.prod.yml..."
if [ ! -f docker-compose.prod.yml ]; then
    log_error "docker-compose.prod.yml not found!"
    exit 1
fi
log_success "docker-compose.prod.yml found"

# Получение обновлений (если используется Git)
if [ -d .git ]; then
    log_info "Pulling latest changes from Git..."
    if git pull origin main; then
        log_success "Git pull completed"
    else
        log_warning "Git pull failed or no changes. Continuing..."
    fi
else
    log_warning "Not a Git repository. Skipping git pull."
fi

# Остановка контейнеров
log_info "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down
log_success "Containers stopped"

# Сборка образов
log_info "Building Docker images (this may take 5-10 minutes)..."
if docker-compose -f docker-compose.prod.yml build; then
    log_success "Docker images built successfully"
else
    log_error "Docker build failed!"
    exit 1
fi

# Запуск контейнеров
log_info "Starting containers..."
if docker-compose -f docker-compose.prod.yml up -d; then
    log_success "Containers started"
else
    log_error "Failed to start containers!"
    exit 1
fi

# Ожидание запуска контейнеров
log_info "Waiting for containers to initialize (10 seconds)..."
sleep 10

# Проверка статуса контейнеров
log_info "Checking container status..."
echo ""
docker-compose -f docker-compose.prod.yml ps
echo ""

# Проверка здоровья Backend
log_info "Checking Backend health..."
if docker exec ozon-backend python -c "import requests; r = requests.get('http://localhost:8000/health'); exit(0 if r.status_code == 200 else 1)" 2>/dev/null; then
    log_success "Backend is healthy"
else
    log_warning "Backend health check failed. Check logs: docker-compose -f docker-compose.prod.yml logs backend"
fi

# Проверка Frontend
log_info "Checking Frontend..."
if curl -s http://localhost/ > /dev/null 2>&1; then
    log_success "Frontend is responding"
else
    log_warning "Frontend check failed. Check logs: docker-compose -f docker-compose.prod.yml logs frontend"
fi

# Проверка Bot
log_info "Checking Bot logs..."
BOT_LOGS=$(docker-compose -f docker-compose.prod.yml logs --tail=5 bot 2>&1)
if echo "$BOT_LOGS" | grep -q -i "error\|exception"; then
    log_warning "Bot may have errors. Check logs: docker-compose -f docker-compose.prod.yml logs bot"
else
    log_success "Bot appears to be running"
fi

# Очистка старых образов
log_info "Cleaning up old Docker images..."
docker image prune -f > /dev/null 2>&1 || true
log_success "Cleanup completed"

# Итоги
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     🎉 Deployment Completed! 🎉       ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
log_info "Application URLs:"
echo "  - Frontend: http://localhost/ (or your domain)"
echo "  - Backend API: http://localhost:8000/docs"
echo "  - Backend Health: http://localhost:8000/health"
echo ""

log_info "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - View specific service logs: docker-compose -f docker-compose.prod.yml logs -f [backend|bot|frontend]"
echo "  - Check status: docker-compose -f docker-compose.prod.yml ps"
echo "  - Restart service: docker-compose -f docker-compose.prod.yml restart [service]"
echo "  - Stop all: docker-compose -f docker-compose.prod.yml down"
echo ""

log_info "Next steps:"
echo "  1. Check logs to ensure everything is running correctly"
echo "  2. Test the application through your browser"
echo "  3. Test Telegram Bot functionality"
echo "  4. (Optional) Configure SSL certificate for HTTPS"
echo ""

log_success "All done! 🚀"
