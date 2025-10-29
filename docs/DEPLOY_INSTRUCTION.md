# 🚀 Инструкция по деплою OZON Scraper на VPS

Пошаговая инструкция для деплоя проекта на твой сервер.

---

## 📋 Что тебе понадобится

1. **VPS сервер** с Ubuntu 20.04+ или Debian 11+
2. **SSH доступ** к серверу (IP, логин, пароль/ключ)
3. **Данные от Supabase** (URL, API ключи)
4. **Telegram Bot Token** (от @BotFather)
5. **Твой Telegram User ID** (от @userinfobot)

---

## Часть 1: Подготовка сервера (делается 1 раз)

### Шаг 1: Подключись к серверу

```bash
ssh root@85.193.94.6
```

Или если у тебя другой пользователь:
```bash
ssh username@YOUR_SERVER_IP
```

### Шаг 2: Обнови систему

```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 3: Установи Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавь пользователя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker $USER

# Проверь установку
docker --version
```

**Важно:** После добавления в группу docker, переподключись к серверу (выйди и зайди снова)

### Шаг 4: Установи Docker Compose

```bash
# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Дай права на выполнение
sudo chmod +x /usr/local/bin/docker-compose

# Проверь установку
docker-compose --version
```

### Шаг 5: Открой необходимые порты

```bash
# Установи UFW (если еще не установлен)
sudo apt install ufw -y

# Открой порты
sudo ufw allow OpenSSH       # SSH (важно! чтобы не потерять доступ)
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS

# Включи firewall
sudo ufw enable

# Проверь статус
sudo ufw status
```

Должно показать:
```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## Часть 2: Установка проекта на сервер

### Шаг 6: Создай директорию для проекта

```bash
mkdir -p ~/ozon-scraper
cd ~/ozon-scraper
```

### Шаг 7: Загрузи проект на сервер

**Вариант A: Через Git (рекомендуется)**

```bash
# Если у тебя приватный репозиторий, сначала настрой SSH ключ для GitHub
git clone git@github.com:your-username/ozon-scraper.git .

# Или через HTTPS
git clone https://github.com/your-username/ozon-scraper.git .
```

**Вариант B: Через rsync (с локальной машины)**

На **ЛОКАЛЬНОЙ машине** выполни:

```bash
# Замени YOUR_SERVER_IP на IP твоего сервера
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
  "/Users/sasha/Library/Mobile Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_ scraper/" \
  root@YOUR_SERVER_IP:~/ozon-scraper/
```

**Вариант C: Через scp (с локальной машины)**

На **ЛОКАЛЬНОЙ машине**:

```bash
cd "/Users/sasha/Library/Mobile Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_ scraper/"
tar -czf ozon-scraper.tar.gz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' .
scp ozon-scraper.tar.gz root@YOUR_SERVER_IP:~/
```

На **СЕРВЕРЕ**:

```bash
cd ~/ozon-scraper
tar -xzf ~/ozon-scraper.tar.gz
rm ~/ozon-scraper.tar.gz
```

### Шаг 8: Создай .env файл на сервере

```bash
cd ~/ozon-scraper
nano .env
```

Скопируй и заполни следующие данные (замени значения на свои):

```bash
# ==============================================
# Supabase Configuration
# ==============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
SUPABASE_ANON_KEY=your-supabase-anon-key-here

# ==============================================
# OZON API Configuration
# ==============================================
OZON_API_BASE_URL=https://api-seller.ozon.ru

# ==============================================
# Telegram Bot Configuration
# ==============================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
ADMIN_USER_IDS=123456789,987654321
BACKEND_API_URL=http://backend:8000

# Webhook (оставь false для начала)
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_PATH=/webhook

# ==============================================
# Frontend Configuration
# ==============================================
# Замени на IP твоего сервера или домен
VITE_BACKEND_API_URL=http://YOUR_SERVER_IP
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key-here

# ==============================================
# Application Configuration
# ==============================================
ENVIRONMENT=production
LOG_LEVEL=INFO

# ==============================================
# Additional Settings
# ==============================================
API_TIMEOUT=30
API_RETRY_COUNT=3
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

**Сохрани файл:**
- Нажми `Ctrl + X`
- Нажми `Y`
- Нажми `Enter`

### Шаг 9: Проверь файл .env

```bash
cat .env | grep -E "SUPABASE|TELEGRAM|VITE_BACKEND"
```

Убедись, что все значения заполнены правильно.

---

## Часть 3: Запуск проекта

### Шаг 10: Сделай deploy.sh исполняемым

```bash
cd ~/ozon-scraper
chmod +x deploy.sh
```

### Шаг 11: Запусти деплой

```bash
./deploy.sh
```

Скрипт автоматически:
1. Проверит наличие Docker и Docker Compose
2. Проверит .env файл
3. Остановит старые контейнеры (если есть)
4. Соберёт Docker образы (займёт 5-10 минут)
5. Запустит контейнеры
6. Проверит их работоспособность

**Примерный вывод:**

```
╔════════════════════════════════════════╗
║   OZON Scraper Deployment Script      ║
╚════════════════════════════════════════╝

ℹ️  Checking environment file...
✅ .env file found
ℹ️  Checking Docker installation...
✅ Docker is installed (Docker version 24.0.7)
ℹ️  Building Docker images (this may take 5-10 minutes)...
✅ Docker images built successfully
ℹ️  Starting containers...
✅ Containers started

╔════════════════════════════════════════╗
║     🎉 Deployment Completed! 🎉       ║
╚════════════════════════════════════════╝
```

### Шаг 12: Проверь статус контейнеров

```bash
docker-compose -f docker-compose.prod.yml ps
```

Должно показать 3 контейнера (все со статусом **Up**):

```
NAME              STATUS         PORTS
ozon-backend      Up             0.0.0.0:8000->8000/tcp
ozon-bot          Up
ozon-frontend     Up             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Шаг 13: Проверь логи

```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Только Backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Только Bot
docker-compose -f docker-compose.prod.yml logs -f bot

# Только Frontend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

Для выхода нажми `Ctrl + C`

---

## Часть 4: Проверка работы

### Шаг 14: Проверь Backend API

На сервере:

```bash
curl http://localhost:8000/health
```

Должно вернуть: `{"status":"ok"}`

```bash
curl http://localhost:8000/api/docs
```

Должен вернуть HTML страницу Swagger документации

### Шаг 15: Проверь Frontend

На сервере:

```bash
curl http://localhost/
```

Должен вернуть HTML страницу админ-панели

### Шаг 16: Открой админ-панель в браузере

На **СВОЕЙ машине** открой браузер и перейди по адресу:

```
http://YOUR_SERVER_IP/
```

Например: `http://123.45.67.89/`

Ты должен увидеть админ-панель OZON Scraper!

### Шаг 17: Проверь API

```
http://YOUR_SERVER_IP/api/docs
```

Должна открыться Swagger документация API

### Шаг 18: Проверь Telegram бота

1. Открой Telegram
2. Найди своего бота (по имени, которое давал @BotFather)
3. Напиши `/start`
4. Бот должен ответить

Проверь логи бота:

```bash
docker-compose -f docker-compose.prod.yml logs bot | tail -20
```

---

## Часть 5: Настройка домена и SSL (опционально)

Если хочешь использовать домен вместо IP и добавить HTTPS.

### Шаг 19: Настрой DNS

В панели управления доменом (Cloudflare, GoDaddy, etc.) добавь A-запись:

```
Тип: A
Имя: @ (или admin, или ozon)
Значение: YOUR_SERVER_IP
TTL: Auto или 3600
```

Подожди 5-15 минут пока DNS обновится. Проверь:

```bash
nslookup your-domain.com
```

### Шаг 20: Получи SSL сертификат (Let's Encrypt)

На сервере:

```bash
# Установи Certbot
sudo apt install certbot -y

# Останови контейнеры на время получения сертификата
cd ~/ozon-scraper
docker-compose -f docker-compose.prod.yml down

# Получи сертификат (замени your-domain.com на свой домен)
sudo certbot certonly --standalone -d your-domain.com

# Создай папку для сертификатов
mkdir -p ssl

# Скопируй сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl
```

### Шаг 21: Обнови Nginx конфигурацию

Открой `frontend/nginx.conf`:

```bash
nano frontend/nginx.conf
```

Замени содержимое на:

```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Сохрани (`Ctrl+X`, `Y`, `Enter`)

### Шаг 22: Обнови .env файл

```bash
nano .env
```

Обнови строку:

```bash
VITE_BACKEND_API_URL=https://your-domain.com
```

Сохрани (`Ctrl+X`, `Y`, `Enter`)

### Шаг 23: Перезапусти проект

```bash
./deploy.sh
```

### Шаг 24: Проверь HTTPS

Открой в браузере:

```
https://your-domain.com/
```

Должен показать замочек (защищённое соединение) ✅

---

## 🔧 Полезные команды

### Просмотр логов

```bash
# Все логи (live)
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f bot
docker-compose -f docker-compose.prod.yml logs -f frontend

# Последние 50 строк
docker-compose -f docker-compose.prod.yml logs --tail=50 backend
```

### Управление контейнерами

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Перезапустить всё
docker-compose -f docker-compose.prod.yml restart

# Перезапустить конкретный сервис
docker-compose -f docker-compose.prod.yml restart backend

# Остановить всё
docker-compose -f docker-compose.prod.yml down

# Запустить всё
docker-compose -f docker-compose.prod.yml up -d

# Пересобрать и запустить
docker-compose -f docker-compose.prod.yml up -d --build
```

### Мониторинг ресурсов

```bash
# Использование CPU, RAM
docker stats

# Место на диске
df -h

# Логи системы
journalctl -xe
```

### Очистка

```bash
# Удалить неиспользуемые образы
docker image prune -a

# Удалить всё неиспользуемое
docker system prune -a

# Освободить место (осторожно!)
docker system prune -a --volumes
```

---

## 🔄 Обновление проекта

Когда нужно обновить код на сервере:

### Вариант A: Через Git

```bash
cd ~/ozon-scraper
git pull origin main
./deploy.sh
```

### Вариант B: Через rsync

На **ЛОКАЛЬНОЙ машине**:

```bash
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
  "/Users/sasha/Library/Mobile Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_ scraper/" \
  root@YOUR_SERVER_IP:~/ozon-scraper/
```

На **СЕРВЕРЕ**:

```bash
cd ~/ozon-scraper
./deploy.sh
```

---

## 🐛 Troubleshooting

### Контейнеры не запускаются

```bash
# Проверь логи
docker-compose -f docker-compose.prod.yml logs

# Проверь .env файл
cat .env

# Проверь статус
docker-compose -f docker-compose.prod.yml ps
```

### Админ-панель не открывается

```bash
# Проверь порты
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Проверь firewall
sudo ufw status

# Проверь логи Nginx
docker-compose -f docker-compose.prod.yml logs frontend
```

### Backend не работает

```bash
# Проверь health endpoint
curl http://localhost:8000/health

# Проверь логи
docker-compose -f docker-compose.prod.yml logs backend

# Перезапусти Backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Бот не отвечает

```bash
# Проверь логи
docker-compose -f docker-compose.prod.yml logs bot

# Проверь токен в .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Перезапусти бота
docker-compose -f docker-compose.prod.yml restart bot
```

### Нет места на диске

```bash
# Проверь место
df -h

# Очисти Docker
docker system prune -a

# Удали старые логи
sudo journalctl --vacuum-time=7d
```

---

## 📱 Тестирование после деплоя

### ✅ Чек-лист

- [ ] Админ-панель открывается: `http://YOUR_SERVER_IP/`
- [ ] API документация доступна: `http://YOUR_SERVER_IP/api/docs`
- [ ] Backend health работает: `http://YOUR_SERVER_IP/api/health`
- [ ] Telegram бот отвечает на `/start`
- [ ] Можно залогиниться в админ-панель
- [ ] Можно просмотреть статистику
- [ ] Можно просмотреть логи
- [ ] Все контейнеры работают: `docker-compose -f docker-compose.prod.yml ps`

---

## 🔒 Безопасность

### Рекомендации после деплоя

1. **Смени пароль root**
```bash
passwd root
```

2. **Создай отдельного пользователя** (не используй root)
```bash
adduser ozon
usermod -aG sudo ozon
usermod -aG docker ozon
```

3. **Настрой SSH ключи** (отключи пароль)

4. **Ограничь SSH только твоим IP**
```bash
sudo ufw allow from YOUR_IP to any port 22
```

5. **Настрой автоматическое обновление SSL**
```bash
sudo crontab -e
# Добавь строку:
0 3 * * * certbot renew --quiet && docker-compose -f /root/ozon-scraper/docker-compose.prod.yml restart frontend
```

6. **Включи автоматические обновления системы**
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📞 Поддержка

Если что-то пошло не так:

1. Проверь логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверь статус: `docker-compose -f docker-compose.prod.yml ps`
3. Перечитай инструкцию
4. Посмотри [VPS_DEPLOYMENT.md](./VPS_DEPLOYMENT.md) для деталей

---

## 🎉 Готово!

Теперь твой OZON Scraper работает в production!

**Основные URL:**
- Админ-панель: `http://YOUR_SERVER_IP/` (или `https://your-domain.com/`)
- API: `http://YOUR_SERVER_IP/api/docs`
- Health Check: `http://YOUR_SERVER_IP/api/health`
