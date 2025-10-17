# Telegram Bot - aiogram

Telegram бот для взаимодействия с пользователями на основе aiogram 3.x.

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd bot
python -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Запуск бота

```bash
python main.py
```

## 📁 Структура

```
bot/
├── main.py              # Точка входа бота
├── config.py            # Конфигурация
├── database.py          # Подключение к Supabase
├── requirements.txt     # Python зависимости
├── handlers/           # Обработчики команд и сообщений
│   ├── __init__.py
│   ├── start.py        # /start команда
│   ├── articles.py     # Работа с артикулами
│   ├── help.py         # /help команда
│   └── errors.py       # Обработка ошибок
├── keyboards/          # Клавиатуры (inline и reply)
│   ├── __init__.py
│   ├── main_menu.py
│   └── inline.py
├── services/           # Сервисы бота
│   ├── __init__.py
│   ├── user_service.py
│   └── article_service.py
├── middlewares/        # Middleware для обработки
│   ├── __init__.py
│   └── auth.py
└── utils/              # Утилиты
    ├── __init__.py
    └── logger.py
```

## 🤖 Команды бота

### Основные команды
- `/start` - Начало работы, регистрация пользователя
- `/help` - Справка по командам
- `/menu` - Главное меню

### Работа с артикулами
- `/add <артикул>` - Добавить артикул для отслеживания
- `/list` - Показать все отслеживаемые артикулы
- `/check <артикул>` - Проверить статус артикула
- `/remove <артикул>` - Удалить артикул из отслеживания

### Информация
- `/history` - История запросов пользователя
- `/report` - Сгенерировать отчет по артикулам
- `/status` - Статус системы

## 🔧 Конфигурация

Переменные окружения (в `.env`):
- `TELEGRAM_BOT_TOKEN` - токен бота от BotFather
- `SUPABASE_URL` - URL Supabase проекта
- `SUPABASE_SERVICE_ROLE_KEY` - service role ключ
- `BACKEND_API_URL` - URL backend API

## 📝 Логирование

Бот использует loguru для логирования:
- Логи сохраняются в `logs/bot.log`
- Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Ротация логов по размеру (10 MB)

## 🎨 Клавиатуры

### Reply клавиатура (главное меню)
```
┌──────────────┬──────────────┐
│ ➕ Добавить  │ 📋 Список    │
├──────────────┼──────────────┤
│ 🔍 Проверить │ 📊 Отчет     │
├──────────────┼──────────────┤
│ 📚 История   │ ℹ️ Помощь    │
└──────────────┴──────────────┘
```

### Inline клавиатуры
- Управление артикулами (удалить, проверить)
- Навигация по спискам (пагинация)
- Подтверждение действий

## 🧪 Тестирование

```bash
# Установить зависимости для тестов
pip install pytest pytest-asyncio

# Запустить тесты
pytest

# С coverage
pytest --cov=. --cov-report=html
```

## 🔐 Безопасность

1. **Валидация пользователей**: проверка `telegram_id` и `is_blocked`
2. **Rate limiting**: ограничение количества запросов
3. **Middleware**: проверка авторизации перед обработкой команд
4. **Логирование**: все действия пользователей логируются

## 📊 Мониторинг

Бот логирует:
- Все команды пользователей
- Ошибки и исключения
- Время выполнения операций
- Статистику использования

Логи можно просматривать в админ-панели.

## 🚀 Деплой

### Supervisor (Linux)
```bash
# /etc/supervisor/conf.d/ozon_bot.conf
[program:ozon_bot]
command=/path/to/venv/bin/python /path/to/bot/main.py
directory=/path/to/bot
user=botuser
autostart=true
autorestart=true
```

### Docker
```bash
docker build -t ozon-bot .
docker run -d --name ozon-bot --env-file .env ozon-bot
```

### systemd (Linux)
```bash
# /etc/systemd/system/ozon-bot.service
[Unit]
Description=OZON Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/bot
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🐛 Отладка

Включите debug режим в `main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Или через переменную окружения:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 📦 Зависимости

Основные:
- `aiogram==3.13.1` - Telegram Bot framework
- `supabase==2.9.0` - клиент для Supabase
- `python-dotenv==1.0.1` - работа с .env
- `loguru==0.7.2` - логирование
- `httpx==0.27.2` - HTTP клиент

## 🔄 Обновление

```bash
git pull
pip install -r requirements.txt --upgrade
# Перезапустить бота
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/bot.log`
2. Проверьте переменные окружения
3. Убедитесь что Backend API запущен
4. Проверьте подключение к Supabase

