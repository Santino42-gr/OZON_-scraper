# OZON Scraper - Deployment Guide

## 📋 Общая информация

**Проект:** OZON Scraper with Comparison Feature
**Версия:** 1.0.0
**Дата:** 2025-10-31

---

## 🏗️ Архитектура

### Компоненты системы:

1. **Backend API** (FastAPI + Python 3.12)
   - REST API для всех операций
   - Асинхронная обработка запросов
   - Автоматический scheduler для обновления данных
   - Swagger/OpenAPI документация

2. **Database** (Supabase PostgreSQL)
   - Хранение артикулов, пользователей, групп сравнения
   - История цен и снэпшотов
   - SQL функции для сложных запросов

3. **Frontend** (Next.js + TypeScript)
   - Admin панель
   - Интерактивные графики
   - Responsive дизайн

4. **Scraping** (Playwright)
   - Получение данных с OZON
   - Rate limiting
   - Кэширование

---

## 📦 Требования

### Минимальные требования:

**Сервер:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- OS: Ubuntu 20.04+ / macOS / Windows Server

**Софт:**
- Python 3.12+
- Node.js 18+
- PostgreSQL 15+ (или Supabase)
- Git

### Рекомендуемые требования (Production):

**Сервер:**
- CPU: 4+ cores
- RAM: 8 GB+
- Disk: 50 GB SSD
- OS: Ubuntu 22.04 LTS

**Дополнительно:**
- Nginx (reverse proxy)
- SSL сертификат (Let's Encrypt)
- Monitoring (Sentry, Grafana)

---

## 🚀 Установка и настройка

### Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd OZON_scraper
```

### Шаг 2: Backend Setup

#### 2.1 Установка зависимостей

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Установить браузеры для Playwright
playwright install
```

#### 2.2 Настройка переменных окружения

Создать файл `backend/.env`:

```bash
cp .env.example .env
```

Заполнить все необходимые переменные:

```env
# Environment
ENVIRONMENT=production

# API Configuration
BACKEND_API_URL=https://api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ozon-scraper/backend.log

# Rate Limiting
OZON_RATE_LIMIT=30
OZON_TIMEOUT=10
```

#### 2.3 Инициализация базы данных

```bash
# Применить все миграции
# (Предполагается что миграции уже в Supabase)

# Проверить подключение
python3 -c "
from database import check_database_connection
import asyncio
result = asyncio.run(check_database_connection())
print('✅ Database connected!' if result else '❌ Database connection failed!')
"
```

#### 2.4 Запуск тестов

```bash
# Unit тесты
python3 test_comparison_service.py

# Integration тесты (требуется запущенный backend)
python3 test_comparison_api.py
```

### Шаг 3: Frontend Setup

```bash
cd frontend

# Установить зависимости
npm install
# или
yarn install

# Создать .env.local
cp .env.example .env.local
```

Заполнить `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

#### 3.1 Build для production

```bash
npm run build
# или
yarn build
```

#### 3.2 Тестирование production build

```bash
npm start
# Откройте http://localhost:3000
```

---

## 🐳 Docker Deployment

### Опция 1: Docker Compose (Рекомендуется для development/staging)

#### 1. Создать docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    volumes:
      - ./backend/logs:/app/logs
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

#### 2. Запустить

```bash
docker-compose up -d
```

#### 3. Проверить логи

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Опция 2: Отдельные Docker контейнеры

#### Backend:

```bash
cd backend
docker build -t ozon-scraper-backend .
docker run -d \
  --name ozon-backend \
  -p 8000:8000 \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_KEY=$SUPABASE_KEY \
  --restart unless-stopped \
  ozon-scraper-backend
```

#### Frontend:

```bash
cd frontend
docker build -t ozon-scraper-frontend .
docker run -d \
  --name ozon-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  --link ozon-backend:backend \
  --restart unless-stopped \
  ozon-scraper-frontend
```

---

## ☁️ Cloud Deployment

### Вариант 1: Vercel (Frontend) + Railway/Render (Backend)

#### Frontend на Vercel:

1. Подключить GitHub репозиторий к Vercel
2. Настроить Build & Development Settings:
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. Добавить Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_SUPABASE_URL=...
   NEXT_PUBLIC_SUPABASE_ANON_KEY=...
   ```

4. Deploy!

#### Backend на Railway:

1. Создать новый проект на Railway
2. Подключить GitHub репозиторий
3. Настроить:
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. Добавить Environment Variables (из .env)

5. Deploy!

### Вариант 2: AWS EC2

#### 1. Создать EC2 Instance

- Ubuntu 22.04 LTS
- t3.medium (или больше)
- Security Groups: 22, 80, 443, 8000, 3000

#### 2. Подключиться по SSH

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. Установить необходимый софт

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip -y

# Установить Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Установить Nginx
sudo apt install nginx -y

# Установить Certbot для SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### 4. Клонировать и настроить проект

```bash
git clone <repo-url>
cd OZON_scraper

# Backend
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
cp .env.example .env
# Отредактировать .env

# Frontend
cd ../frontend
npm install
npm run build
```

#### 5. Настроить systemd services

**Backend service** (`/etc/systemd/system/ozon-backend.service`):

```ini
[Unit]
Description=OZON Scraper Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/OZON_scraper/backend
Environment="PATH=/home/ubuntu/OZON_scraper/backend/venv/bin"
ExecStart=/home/ubuntu/OZON_scraper/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend service** (`/etc/systemd/system/ozon-frontend.service`):

```ini
[Unit]
Description=OZON Scraper Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/OZON_scraper/frontend
ExecStart=/usr/bin/npm start
Restart=always
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

#### 6. Запустить services

```bash
sudo systemctl daemon-reload
sudo systemctl enable ozon-backend
sudo systemctl enable ozon-frontend
sudo systemctl start ozon-backend
sudo systemctl start ozon-frontend

# Проверить статус
sudo systemctl status ozon-backend
sudo systemctl status ozon-frontend
```

#### 7. Настроить Nginx

```bash
sudo nano /etc/nginx/sites-available/ozon-scraper
```

```nginx
# Backend
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ozon-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. Настроить SSL

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

---

## 🔧 Настройка Scheduler (Cron Jobs)

Scheduler автоматически запускается при старте backend. Настройки в `backend/services/scheduler.py`:

```python
# Обновление снэпшотов сравнений - каждый день в 03:00
scheduler.add_job(
    update_comparison_snapshots,
    trigger=CronTrigger(hour=3, minute=0),
    ...
)

# Обновление истории цен - каждый день в 04:00
scheduler.add_job(
    update_price_history,
    trigger=CronTrigger(hour=4, minute=0),
    ...
)
```

### Изменить расписание:

Отредактировать `backend/services/scheduler.py` и перезапустить backend:

```bash
sudo systemctl restart ozon-backend
```

### Запустить задачи вручную:

```bash
cd backend
source venv/bin/activate

# Тест снэпшотов
python3 services/scheduler.py test-snapshots

# Тест истории цен
python3 services/scheduler.py test-price
```

---

## 📊 Monitoring & Logging

### Логи

**Backend логи:**
```bash
# Systemd logs
sudo journalctl -u ozon-backend -f

# Application logs
tail -f backend/logs/backend.log
```

**Frontend логи:**
```bash
sudo journalctl -u ozon-frontend -f
```

### Monitoring (Рекомендуется)

#### 1. Sentry для error tracking

```bash
pip install sentry-sdk
```

```python
# backend/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

#### 2. Prometheus + Grafana

Установить Prometheus exporter:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## 🔒 Security Checklist

### Backend:

- [ ] Все environment variables в .env (не в коде)
- [ ] CORS настроен правильно (только нужные домены)
- [ ] Rate limiting включен
- [ ] SQL injection защита (используем parameterized queries)
- [ ] Authentication для admin endpoints
- [ ] HTTPS включен (SSL сертификат)
- [ ] Secrets не в git (проверить .gitignore)

### Frontend:

- [ ] API keys только для публичных операций
- [ ] XSS защита (Next.js по умолчанию)
- [ ] CSRF токены для форм
- [ ] Content Security Policy настроена
- [ ] HTTPS everywhere

### Database:

- [ ] Row Level Security (RLS) включен в Supabase
- [ ] Регулярные бэкапы настроены
- [ ] Минимальные права для service role
- [ ] SSL соединение с БД

---

## 🔄 CI/CD Pipeline (Опционально)

### GitHub Actions Example

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python3 test_comparison_service.py

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        # or SSH to EC2 and pull + restart

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        # Vercel auto-deploys on push
```

---

## 🆘 Troubleshooting

### Backend не запускается

**Проблема:** Port 8000 already in use
```bash
# Найти процесс
lsof -ti:8000

# Убить процесс
kill -9 $(lsof -ti:8000)
```

**Проблема:** Database connection failed
```bash
# Проверить .env файл
cat backend/.env | grep SUPABASE

# Проверить доступность Supabase
curl https://your-project.supabase.co
```

**Проблема:** Playwright browser not found
```bash
playwright install
```

### Frontend не запускается

**Проблема:** Module not found
```bash
rm -rf node_modules package-lock.json
npm install
```

**Проблема:** API не доступен
```bash
# Проверить NEXT_PUBLIC_API_URL в .env.local
# Проверить CORS в backend
```

### Scheduler не работает

**Проблема:** Задачи не выполняются
```bash
# Проверить логи
tail -f backend/logs/backend.log | grep scheduler

# Запустить вручную для теста
python3 services/scheduler.py test-snapshots
```

---

## 📞 Support

**Документация:**
- API Docs: http://localhost:8000/docs (после запуска backend)
- ReDoc: http://localhost:8000/redoc

**Логи:**
- Backend: `backend/logs/backend.log`
- Systemd: `sudo journalctl -u ozon-backend`

**Тесты:**
- Unit: `python3 backend/test_comparison_service.py`
- Integration: `python3 backend/test_comparison_api.py`
- Manual: См. `MANUAL_TEST_PLAN.md`

---

## ✅ Production Checklist

Перед deploy в production:

- [ ] Все тесты пройдены (unit + integration)
- [ ] .env файлы настроены корректно
- [ ] Database миграции применены
- [ ] SSL сертификаты установлены
- [ ] Monitoring настроен (Sentry, logs)
- [ ] Бэкапы базы данных настроены
- [ ] Rate limiting настроен
- [ ] CORS настроен правильно
- [ ] Scheduler работает корректно
- [ ] Health checks работают (/health, /api/v1/comparison/health)
- [ ] Документация обновлена
- [ ] README актуален
- [ ] Rollback план подготовлен

---

**Версия:** 1.0.0
**Дата:** 2025-10-31
**Автор:** AI Agent

**Удачного деплоя! 🚀**
