# Доступ к Админ-Панели OZON Scraper

## Как работает доступ к админ-панели при деплое на VPS

После развертывания проекта на VPS с помощью `docker-compose.prod.yml`, админ-панель (Frontend) будет доступна через интернет.

---

## 🌐 Архитектура доступа

```
Интернет
   ↓
VPS Server (123.45.67.89 или your-domain.com)
   ↓
Nginx (порты 80/443)
   ├── / → React Admin Panel (Frontend)
   └── /api/* → FastAPI Backend (proxy to port 8000)
```

---

## 🔗 Варианты доступа

### 1. Доступ по IP адресу (сразу после деплоя)

После запуска `docker-compose -f docker-compose.prod.yml up -d`:

**HTTP (незащищенный):**
```
http://123.45.67.89/
```

**Пример:**
- Админ-панель: `http://123.45.67.89/`
- API: `http://123.45.67.89/api/health`
- Логин: `http://123.45.67.89/login`

> ⚠️ **Внимание:** HTTP не рекомендуется для production! Настройте домен и SSL.

---

### 2. Доступ по домену (рекомендуется)

#### Шаг 1: Настройте DNS

Добавьте A-запись в DNS вашего домена:

```
Тип: A
Имя: @ (или ozon, или admin)
Значение: 123.45.67.89 (IP вашего VPS)
TTL: 3600
```

**Примеры доменов:**
- `https://ozon-admin.your-domain.com`
- `https://admin.your-domain.com`
- `https://your-domain.com`

#### Шаг 2: Настройте SSL сертификат

Используйте Let's Encrypt для бесплатного SSL:

```bash
# На VPS сервере
sudo apt-get update
sudo apt-get install certbot

# Остановите контейнеры на время получения сертификата
docker-compose -f docker-compose.prod.yml down

# Получите сертификат
sudo certbot certonly --standalone -d your-domain.com

# Скопируйте сертификаты в папку проекта
sudo mkdir -p ./ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/
sudo chown -R $USER:$USER ./ssl
```

#### Шаг 3: Обновите Nginx конфигурацию

См. раздел "Настройка HTTPS" ниже.

---

## 🔐 Настройка HTTPS (опционально, но рекомендуется)

### Обновите `frontend/nginx.conf`

Добавьте блок для SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL сертификаты
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # API proxy
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

    # React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Обновите `.env` файл

```bash
# Frontend Configuration
VITE_BACKEND_API_URL=https://your-domain.com

# Webhook для бота (если используется)
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://your-domain.com/webhook
```

### Пересоберите и перезапустите

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📋 Чек-лист для доступа к админ-панели

### После первого деплоя

- [ ] VPS запущен и доступен по SSH
- [ ] Docker и Docker Compose установлены
- [ ] Порты 80 и 443 открыты в firewall
- [ ] Проект склонирован на VPS
- [ ] Файл `.env` создан и заполнен
- [ ] `docker-compose -f docker-compose.prod.yml up -d` выполнен успешно
- [ ] Все контейнеры запущены: `docker ps`

### Проверка доступа

```bash
# На VPS
docker ps  # Все контейнеры должны быть UP

# Проверка портов
curl http://localhost:80  # Должен вернуть HTML админ-панели
curl http://localhost:8000/api/health  # Должен вернуть {"status":"ok"}

# С локальной машины
curl http://123.45.67.89/  # Должен вернуть HTML
curl http://123.45.67.89/api/health  # Должен вернуть {"status":"ok"}
```

### С SSL сертификатом

- [ ] DNS настроен (A-запись добавлена)
- [ ] SSL сертификат получен через Certbot
- [ ] Сертификаты скопированы в `./ssl/`
- [ ] Nginx конфигурация обновлена
- [ ] `.env` обновлен с HTTPS URL
- [ ] Frontend пересобран
- [ ] HTTPS работает: `https://your-domain.com`

---

## 🔧 Открытие портов на VPS

### Ubuntu/Debian (UFW)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH (важно!)
sudo ufw enable
sudo ufw status
```

### CentOS/RHEL (Firewalld)

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

---

## 🎯 Примеры URL после деплоя

### Доступ по IP (HTTP)

| Сервис | URL | Описание |
|--------|-----|----------|
| Админ-панель | `http://123.45.67.89/` | Главная страница |
| Логин | `http://123.45.67.89/login` | Страница входа |
| API Health | `http://123.45.67.89/api/health` | Проверка Backend |
| API Docs | `http://123.45.67.89/api/docs` | Swagger документация |

### Доступ по домену (HTTPS)

| Сервис | URL | Описание |
|--------|-----|----------|
| Админ-панель | `https://ozon-admin.com/` | Главная страница |
| Логин | `https://ozon-admin.com/login` | Страница входа |
| API Health | `https://ozon-admin.com/api/health` | Проверка Backend |
| API Docs | `https://ozon-admin.com/api/docs` | Swagger документация |

---

## 🐛 Troubleshooting

### Админ-панель не открывается

**1. Проверьте контейнеры:**
```bash
docker ps
# Должны быть запущены: ozon-frontend, ozon-backend, ozon-bot
```

**2. Проверьте логи:**
```bash
docker logs ozon-frontend
docker logs ozon-backend
```

**3. Проверьте порты:**
```bash
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
# Должны быть заняты docker-proxy
```

**4. Проверьте firewall:**
```bash
sudo ufw status
# Порты 80 и 443 должны быть ALLOW
```

### Админ-панель открывается, но API не работает

**1. Проверьте Backend:**
```bash
curl http://localhost:8000/api/health
# Должен вернуть: {"status":"ok"}
```

**2. Проверьте Nginx proxy:**
```bash
docker exec ozon-frontend cat /etc/nginx/conf.d/default.conf
# Проверьте proxy_pass http://backend:8000
```

**3. Проверьте переменные окружения Frontend:**
```bash
# В .env файле:
VITE_BACKEND_API_URL должен быть правильным
```

### SSL сертификат не работает

**1. Проверьте DNS:**
```bash
nslookup your-domain.com
# Должен вернуть IP вашего VPS
```

**2. Проверьте сертификаты:**
```bash
ls -la ./ssl/
# Должны быть: fullchain.pem, privkey.pem
```

**3. Проверьте Nginx конфигурацию:**
```bash
docker exec ozon-frontend nginx -t
# Должно быть: syntax is ok, test is successful
```

### Админ-панель показывает 404 на роутах

Это нормально, если не настроен fallback для SPA. Nginx должен отдавать `index.html` для всех роутов:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 📱 Доступ с мобильных устройств

После настройки домена и HTTPS, админ-панель будет доступна с любых устройств:

- 📱 **Смартфон:** откройте браузер → `https://your-domain.com`
- 💻 **Планшет:** откройте браузер → `https://your-domain.com`
- 🖥️ **Компьютер:** откройте браузер → `https://your-domain.com`

---

## 🔒 Безопасность

### Рекомендации

1. ✅ **Используйте HTTPS** для production
2. ✅ **Настройте firewall** (только порты 22, 80, 443)
3. ✅ **Используйте сильные пароли** в Supabase
4. ✅ **Ограничьте доступ к SSH** (только ваш IP)
5. ✅ **Включите Rate Limiting** в Backend
6. ✅ **Настройте мониторинг** (логи, алерты)

### Настройка SSH ограничения (опционально)

```bash
# Разрешить SSH только с вашего IP
sudo ufw delete allow 22/tcp
sudo ufw allow from YOUR_IP to any port 22
```

---

## 📊 Мониторинг доступа

### Просмотр логов Nginx

```bash
# Access logs (кто заходил)
docker exec ozon-frontend tail -f /var/log/nginx/access.log

# Error logs (ошибки)
docker exec ozon-frontend tail -f /var/log/nginx/error.log
```

### Просмотр логов Backend

```bash
docker logs -f ozon-backend
```

---

## 📞 Поддержка

Если админ-панель недоступна после деплоя:

1. Проверьте все пункты в чек-листе выше
2. Посмотрите логи контейнеров
3. Убедитесь, что порты открыты
4. Проверьте `.env` файл на корректность

Для детального деплоя смотрите:
- `docs/VPS_DEPLOYMENT.md` - полная инструкция по деплою
- `docs/QUICK_DEPLOY.md` - быстрый старт
