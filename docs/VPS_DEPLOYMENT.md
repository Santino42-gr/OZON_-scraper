# Инструкция по деплою OZON Scraper на VPS

## Предварительные требования

### На VPS сервере должны быть установлены:
- Ubuntu 20.04+ или Debian 11+
- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)
- Git
- Минимум 2GB RAM
- 20GB свободного места на диске

### Локально у вас должны быть:
- SSH доступ к VPS серверу
- Все актуальные файлы проекта
- Настроенные .env файлы

---

## Шаг 1: Подготовка VPS сервера

### 1.1 Подключение к серверу
```bash
ssh root@your_vps_ip
# или
ssh your_username@your_vps_ip
```

### 1.2 Обновление системы
```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Установка Docker
```bash
# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление Docker GPG ключа
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление Docker репозитория
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Проверка установки
sudo docker --version
```

### 1.4 Установка Docker Compose
```bash
# Скачивание Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Права на выполнение
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker-compose --version
```

### 1.5 Добавление пользователя в группу Docker (опционально)
```bash
sudo usermod -aG docker $USER
# После этого нужно выйти и зайти заново
exit
```

### 1.6 Настройка Firewall
```bash
# Установка UFW
sudo apt install -y ufw

# Разрешение SSH
sudo ufw allow OpenSSH

# Разрешение HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Разрешение Backend API (опционально, если хотите прямой доступ)
sudo ufw allow 8000/tcp

# Включение firewall
sudo ufw enable
sudo ufw status
```

---

## Шаг 2: Подготовка проекта локально

### 2.1 Создание .env файла
Создайте файл `.env` в корне проекта:

```bash
# Создайте на основе этого шаблона
cat > .env << 'EOF'
# Backend & Bot
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
OZON_API_BASE_URL=https://api-seller.ozon.ru

# Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
ADMIN_USER_IDS=123456789,987654321
BACKEND_API_URL=http://backend:8000
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_PATH=/webhook

# Frontend Build Args
VITE_BACKEND_API_URL=https://your-domain.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
```

**ВАЖНО**: Замените все `your-*` значения на реальные!

### 2.2 Проверка структуры проекта
Убедитесь, что у вас есть все необходимые файлы:
```
OZON_scraper/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── ... (остальные файлы)
├── bot/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── ... (остальные файлы)
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   ├── package.json
│   └── ... (остальные файлы)
├── docker-compose.prod.yml
└── .env
```

---

## Шаг 3: Передача проекта на VPS

### Вариант А: Через Git (Рекомендуется)

**3.1 На локальной машине:**
```bash
# Если еще не создали репозиторий
git init
git add .
git commit -m "Production deploy"

# Создайте приватный репозиторий на GitHub/GitLab
# Добавьте remote и запушьте
git remote add origin https://github.com/your-username/ozon-scraper.git
git push -u origin main
```

**ВАЖНО**: Убедитесь, что `.env` файл в `.gitignore`! Никогда не коммитьте секреты!

**3.2 На VPS сервере:**
```bash
# Создание директории для проекта
mkdir -p ~/ozon-scraper
cd ~/ozon-scraper

# Клонирование репозитория
git clone https://github.com/your-username/ozon-scraper.git .

# Если репозиторий приватный, используйте SSH или Personal Access Token
```

**3.3 Создание .env файла на сервере:**
```bash
# Создайте .env файл на VPS (используйте nano или vim)
nano .env
# Вставьте содержимое .env файла и сохраните (Ctrl+O, Enter, Ctrl+X)
```

### Вариант Б: Через rsync/scp

**На локальной машине:**
```bash
# Используйте rsync для передачи файлов
rsync -avz --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
  /path/to/OZON_scraper/ your_username@your_vps_ip:~/ozon-scraper/

# Или используйте scp
scp -r /path/to/OZON_scraper your_username@your_vps_ip:~/ozon-scraper/
```

**Затем на VPS создайте .env файл:**
```bash
cd ~/ozon-scraper
nano .env
# Вставьте содержимое .env файла
```

---

## Шаг 4: Запуск проекта на VPS

### 4.1 Подключение к серверу
```bash
ssh your_username@your_vps_ip
cd ~/ozon-scraper
```

### 4.2 Проверка .env файла
```bash
# Убедитесь, что .env файл существует и содержит правильные значения
cat .env
```

### 4.3 Сборка и запуск контейнеров
```bash
# Сборка образов (может занять 5-10 минут)
docker-compose -f docker-compose.prod.yml build

# Запуск контейнеров в фоновом режиме
docker-compose -f docker-compose.prod.yml up -d

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Для выхода из просмотра логов нажмите Ctrl+C
```

### 4.4 Проверка статуса контейнеров
```bash
# Просмотр запущенных контейнеров
docker ps

# Вы должны увидеть 3 контейнера:
# - ozon-backend
# - ozon-bot
# - ozon-frontend
```

### 4.5 Проверка работоспособности
```bash
# Проверка Backend
curl http://localhost:8000/health

# Проверка Frontend
curl http://localhost/

# Проверка логов Backend
docker-compose -f docker-compose.prod.yml logs backend

# Проверка логов Bot
docker-compose -f docker-compose.prod.yml logs bot

# Проверка логов Frontend
docker-compose -f docker-compose.prod.yml logs frontend
```

---

## Шаг 5: Настройка домена и SSL (Опционально)

### 5.1 Настройка DNS записей
В панели управления вашего регистратора доменов добавьте A запись:
```
A    @    your_vps_ip
A    www  your_vps_ip
```

### 5.2 Установка Certbot для SSL сертификата
```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Остановка контейнеров на время получения сертификата
cd ~/ozon-scraper
docker-compose -f docker-compose.prod.yml down

# Получение SSL сертификата
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Сертификаты будут сохранены в:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 5.3 Обновление nginx.conf для SSL
Отредактируйте `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /usr/share/nginx/html;
    index index.html;

    # Остальная конфигурация...
}
```

### 5.4 Обновление docker-compose.prod.yml
Обновите секцию volumes для frontend:
```yaml
frontend:
  volumes:
    - /etc/letsencrypt/live/your-domain.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
    - /etc/letsencrypt/live/your-domain.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
```

### 5.5 Пересборка и перезапуск
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d
```

### 5.6 Автообновление SSL сертификата
```bash
# Создание cron задачи для автообновления
sudo crontab -e

# Добавьте эту строку (обновление каждый день в 3:00)
0 3 * * * certbot renew --quiet && docker-compose -f /home/your_username/ozon-scraper/docker-compose.prod.yml restart frontend
```

---

## Шаг 6: Управление проектом

### Полезные команды Docker Compose

```bash
# Запуск контейнеров
docker-compose -f docker-compose.prod.yml up -d

# Остановка контейнеров
docker-compose -f docker-compose.prod.yml down

# Перезапуск контейнеров
docker-compose -f docker-compose.prod.yml restart

# Перезапуск отдельного сервиса
docker-compose -f docker-compose.prod.yml restart backend

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend

# Просмотр статуса контейнеров
docker-compose -f docker-compose.prod.yml ps

# Пересборка после изменений
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Очистка неиспользуемых образов и контейнеров
docker system prune -a
```

### Обновление проекта

```bash
# Подключение к серверу
ssh your_username@your_vps_ip
cd ~/ozon-scraper

# Получение обновлений из Git
git pull origin main

# Пересборка и перезапуск
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Резервное копирование

```bash
# Создание директории для бэкапов
mkdir -p ~/backups

# Экспорт .env файла
cp ~/ozon-scraper/.env ~/backups/.env.backup

# Бэкап базы данных (через Supabase Dashboard или CLI)
# Supabase автоматически делает бэкапы, но можно экспортировать вручную:
# Dashboard -> Database -> Backups
```

---

## Шаг 7: Мониторинг и траблшутинг

### Проверка здоровья системы

```bash
# Проверка использования ресурсов
docker stats

# Проверка места на диске
df -h

# Проверка памяти
free -h

# Проверка логов системы
sudo journalctl -u docker -f
```

### Типичные проблемы и решения

**Проблема 1: Контейнер не запускается**
```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs backend

# Проверьте, не занят ли порт
sudo netstat -tulpn | grep 8000

# Пересоздайте контейнер
docker-compose -f docker-compose.prod.yml up -d --force-recreate backend
```

**Проблема 2: Backend не подключается к базе данных**
```bash
# Проверьте .env файл
cat .env | grep SUPABASE

# Проверьте подключение изнутри контейнера
docker exec -it ozon-backend bash
curl $SUPABASE_URL
```

**Проблема 3: Frontend показывает ошибку подключения к API**
```bash
# Проверьте, что Backend запущен
docker ps | grep backend

# Проверьте логи Frontend
docker-compose -f docker-compose.prod.yml logs frontend

# Проверьте nginx конфигурацию
docker exec -it ozon-frontend cat /etc/nginx/conf.d/default.conf
```

**Проблема 4: Закончилось место на диске**
```bash
# Очистка неиспользуемых образов
docker image prune -a

# Очистка всех неиспользуемых ресурсов
docker system prune -a --volumes

# Проверка размеров образов
docker images

# Удаление конкретного образа
docker rmi <image_id>
```

**Проблема 5: Telegram Bot не отвечает**
```bash
# Проверьте логи бота
docker-compose -f docker-compose.prod.yml logs bot

# Проверьте, что Backend доступен для бота
docker exec -it ozon-bot ping backend

# Перезапустите бота
docker-compose -f docker-compose.prod.yml restart bot
```

---

## Шаг 8: Безопасность

### Рекомендации по безопасности

1. **Не храните секреты в Git**
   ```bash
   # Убедитесь, что .env в .gitignore
   echo ".env" >> .gitignore
   ```

2. **Используйте сильные пароли**
   - Для Supabase
   - Для администраторов Telegram Bot
   - Для SSH доступа

3. **Регулярно обновляйте систему**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Используйте SSH ключи вместо паролей**
   ```bash
   # На локальной машине
   ssh-copy-id your_username@your_vps_ip

   # Отключите парольную аутентификацию на VPS
   sudo nano /etc/ssh/sshd_config
   # Установите: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

5. **Настройте fail2ban**
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

6. **Ограничьте доступ к Backend API**
   - Используйте только через nginx proxy
   - Не открывайте порт 8000 напрямую в firewall (если не нужно)

---

## Шаг 9: Создание простого скрипта деплоя

Создайте файл `deploy.sh` в корне проекта:

```bash
#!/bin/bash

# deploy.sh - Скрипт для автоматического деплоя

set -e

echo "🚀 Starting deployment..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Остановка контейнеров
echo "⏹️  Stopping containers..."
docker-compose -f docker-compose.prod.yml down

# Получение обновлений (если используется Git)
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main
fi

# Сборка образов
echo "🔨 Building images..."
docker-compose -f docker-compose.prod.yml build

# Запуск контейнеров
echo "▶️  Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
echo "✅ Checking status..."
sleep 5
docker-compose -f docker-compose.prod.yml ps

echo "🎉 Deployment complete!"
echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
```

Сделайте скрипт исполняемым:
```bash
chmod +x deploy.sh
```

Использование:
```bash
./deploy.sh
```

---

## Контрольный чеклист деплоя

- [ ] VPS сервер подготовлен (Docker, Docker Compose установлены)
- [ ] Firewall настроен (порты 80, 443, SSH открыты)
- [ ] Проект загружен на сервер (через Git или rsync)
- [ ] .env файл создан и заполнен правильными значениями
- [ ] Контейнеры собраны и запущены
- [ ] Backend API отвечает на /health endpoint
- [ ] Frontend доступен через браузер
- [ ] Telegram Bot отвечает на команды
- [ ] (Опционально) Домен настроен
- [ ] (Опционально) SSL сертификат установлен
- [ ] Логи проверены на отсутствие критических ошибок

---

## Дополнительные ресурсы

- Docker Documentation: https://docs.docker.com/
- Docker Compose Documentation: https://docs.docker.com/compose/
- Nginx Documentation: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- Supabase Documentation: https://supabase.com/docs

---

## Поддержка

Если возникли проблемы:
1. Проверьте логи контейнеров
2. Убедитесь, что все переменные окружения заполнены правильно
3. Проверьте, что Supabase база данных доступна
4. Убедитесь, что все порты открыты в firewall

Для получения помощи создайте issue в репозитории проекта.
