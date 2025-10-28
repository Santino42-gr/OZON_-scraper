# Quick Deploy Guide - OZON Scraper

Быстрая инструкция для опытных пользователей. Для подробной инструкции смотрите [VPS_DEPLOYMENT.md](./VPS_DEPLOYMENT.md)

## TL;DR

```bash
# 1. На VPS: Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. Клонирование проекта на VPS
mkdir -p ~/ozon-scraper && cd ~/ozon-scraper
git clone <your-repo-url> .

# 3. Создание .env файла
cat > .env << 'EOF'
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
OZON_API_BASE_URL=https://api-seller.ozon.ru
TELEGRAM_BOT_TOKEN=your-token
ADMIN_USER_IDS=123456789
BACKEND_API_URL=http://backend:8000
VITE_BACKEND_API_URL=https://your-domain.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
ENVIRONMENT=production
LOG_LEVEL=INFO
WEBHOOK_ENABLED=false
EOF

# 4. Запуск
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Проверка
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Обновление проекта

```bash
cd ~/ozon-scraper
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## SSL (Let's Encrypt)

```bash
sudo apt install -y certbot
docker-compose -f docker-compose.prod.yml down
sudo certbot certonly --standalone -d your-domain.com
```

Обновите `frontend/nginx.conf` для SSL и `docker-compose.prod.yml` для монтирования сертификатов.

## Полезные команды

```bash
# Логи
docker-compose -f docker-compose.prod.yml logs -f [service]

# Перезапуск
docker-compose -f docker-compose.prod.yml restart [service]

# Остановка
docker-compose -f docker-compose.prod.yml down

# Очистка
docker system prune -a

# Статус
docker-compose -f docker-compose.prod.yml ps

# Ресурсы
docker stats
```

## Проверка работоспособности

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost/

# Логи бота
docker-compose -f docker-compose.prod.yml logs bot | tail -50
```

## 🌐 Доступ к Админ-Панели

После успешного деплоя админ-панель доступна через браузер:

### По IP адресу (HTTP)
```
http://YOUR_VPS_IP/
```

**Пример:** `http://123.45.67.89/`

### По домену (HTTPS, после настройки SSL)
```
https://your-domain.com/
```

### Основные URL:
- **Админ-панель:** `http://YOUR_IP/` или `https://your-domain.com/`
- **Логин:** `http://YOUR_IP/login`
- **API Health:** `http://YOUR_IP/api/health`
- **API Docs:** `http://YOUR_IP/api/docs`

> 📖 Подробная инструкция: [ADMIN_PANEL_ACCESS.md](./ADMIN_PANEL_ACCESS.md)

## Архитектура

```
┌─────────────┐
│   Frontend  │ :80, :443
│   (Nginx)   │
└──────┬──────┘
       │ proxy /api/ → :8000
       ↓
┌─────────────┐      ┌──────────────┐
│   Backend   │ :8000│  Telegram    │
│  (FastAPI)  │←─────┤     Bot      │
└──────┬──────┘      └──────────────┘
       │
       ↓
┌─────────────┐
│  Supabase   │
│ (PostgreSQL)│
└─────────────┘
```

## Минимальные требования

- 2GB RAM
- 20GB Disk
- Ubuntu 20.04+
- Docker 20.10+
- Docker Compose 2.0+

## Порты

- 80 - Frontend HTTP
- 443 - Frontend HTTPS (если SSL настроен)
- 8000 - Backend API (закрыт снаружи, доступен только внутри Docker сети)

## Важно

- ❌ Никогда не коммитьте `.env` в Git!
- ✅ Используйте сильные пароли для всех сервисов
- ✅ Настройте SSH ключи вместо паролей
- ✅ Регулярно обновляйте систему: `sudo apt update && sudo apt upgrade -y`
- ✅ Настройте автоматическое обновление SSL: добавьте cron задачу для `certbot renew`

Для получения полной информации см. [VPS_DEPLOYMENT.md](./VPS_DEPLOYMENT.md)
