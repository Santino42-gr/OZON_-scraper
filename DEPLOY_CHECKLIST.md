# ✅ Чек-лист деплоя OZON Scraper

Быстрая шпаргалка для деплоя. Полная инструкция: [docs/DEPLOY_INSTRUCTION.md](docs/DEPLOY_INSTRUCTION.md)

---

## 📋 Что нужно подготовить

- [ ] VPS сервер (Ubuntu 20.04+)
- [ ] SSH доступ (IP + пароль/ключ)
- [ ] Supabase проект (URL + API ключи)
- [ ] Telegram Bot Token (@BotFather)
- [ ] Telegram User ID (@userinfobot)
- [ ] Домен (опционально, для HTTPS)

---

## 🚀 Деплой за 10 шагов

### 1. Подключись к серверу
```bash
ssh root@YOUR_SERVER_IP
```

### 2. Установи Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 3. Установи Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Открой порты
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5. Загрузи проект

**Через Git:**
```bash
mkdir -p ~/ozon-scraper && cd ~/ozon-scraper
git clone <your-repo-url> .
```

**Или через rsync (с локальной машины):**
```bash
rsync -avz --exclude 'node_modules' --exclude '.git' \
  "/Users/sasha/Library/Mobile Documents/com~apple~CloudDocs/AIronLab/Cursor/OZON_ scraper/" \
  root@YOUR_SERVER_IP:~/ozon-scraper/
```

### 6. Создай .env файл
```bash
cd ~/ozon-scraper
nano .env
```

**Минимальная конфигурация:**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

OZON_API_BASE_URL=https://api-seller.ozon.ru

TELEGRAM_BOT_TOKEN=your-bot-token
ADMIN_USER_IDS=your-telegram-id

BACKEND_API_URL=http://backend:8000
VITE_BACKEND_API_URL=http://YOUR_SERVER_IP
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

ENVIRONMENT=production
LOG_LEVEL=INFO
WEBHOOK_ENABLED=false
```

Сохрани: `Ctrl+X` → `Y` → `Enter`

### 7. Сделай скрипт исполняемым
```bash
chmod +x deploy.sh
```

### 8. Запусти деплой
```bash
./deploy.sh
```

### 9. Проверь статус
```bash
docker-compose -f docker-compose.prod.yml ps
```

Все 3 контейнера должны быть **Up**:
- ozon-backend
- ozon-bot
- ozon-frontend

### 10. Открой в браузере
```
http://YOUR_SERVER_IP/
```

---

## 🎯 Быстрая проверка

```bash
# Backend API
curl http://localhost:8000/health
# Должен вернуть: {"status":"ok"}

# Frontend
curl http://localhost/
# Должен вернуть HTML

# Логи
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔧 Полезные команды

### Просмотр логов
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f bot
```

### Управление
```bash
# Статус
docker-compose -f docker-compose.prod.yml ps

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление
git pull origin main && ./deploy.sh
```

### Мониторинг
```bash
# Использование ресурсов
docker stats

# Место на диске
df -h
```

---

## 🐛 Частые проблемы

### Контейнеры не запускаются
```bash
# Проверь .env файл
cat .env

# Проверь логи
docker-compose -f docker-compose.prod.yml logs
```

### Админ-панель не открывается
```bash
# Проверь порты
sudo ufw status
sudo netstat -tulpn | grep :80

# Проверь логи Frontend
docker-compose -f docker-compose.prod.yml logs frontend
```

### Бот не отвечает
```bash
# Проверь токен
cat .env | grep TELEGRAM_BOT_TOKEN

# Проверь логи
docker-compose -f docker-compose.prod.yml logs bot

# Перезапусти
docker-compose -f docker-compose.prod.yml restart bot
```

---

## 🔒 HTTPS (опционально)

### 1. Настрой DNS
В панели домена добавь A-запись:
```
Тип: A
Имя: @
Значение: YOUR_SERVER_IP
```

### 2. Получи SSL сертификат
```bash
sudo apt install certbot -y
docker-compose -f docker-compose.prod.yml down
sudo certbot certonly --standalone -d your-domain.com

mkdir -p ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl
```

### 3. Обнови конфигурацию
См. полную инструкцию: [docs/DEPLOY_INSTRUCTION.md](docs/DEPLOY_INSTRUCTION.md#шаг-21-обнови-nginx-конфигурацию)

### 4. Перезапусти
```bash
./deploy.sh
```

---

## 📱 Итоговые URL

После деплоя доступны:

- **Админ-панель:** `http://YOUR_SERVER_IP/`
- **API Docs:** `http://YOUR_SERVER_IP/api/docs`
- **Health Check:** `http://YOUR_SERVER_IP/api/health`

С HTTPS:
- **Админ-панель:** `https://your-domain.com/`
- **API Docs:** `https://your-domain.com/api/docs`

---

## 📚 Дополнительная документация

- [Полная инструкция по деплою](docs/DEPLOY_INSTRUCTION.md)
- [Доступ к админ-панели](docs/ADMIN_PANEL_ACCESS.md)
- [Технический гайд](docs/VPS_DEPLOYMENT.md)
- [Быстрый справочник](docs/QUICK_DEPLOY.md)

---

## ✅ Финальный чек-лист

После деплоя проверь:

- [ ] Все 3 контейнера работают
- [ ] Админ-панель открывается в браузере
- [ ] API /health возвращает OK
- [ ] API /docs показывает Swagger
- [ ] Telegram бот отвечает на /start
- [ ] Можно залогиниться в админку
- [ ] Логи не показывают критических ошибок

**Готово! 🎉**
