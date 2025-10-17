# OZON Telegram Bot & Admin Panel MVP 🤖

> Система для анализа и мониторинга товаров OZON с Telegram-ботом и веб админ-панелью

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Enabled-orange.svg)](https://supabase.com/)

## 📋 Описание

MVP система для мониторинга товаров OZON, состоящая из:
- 🤖 **Telegram-бот** (aiogram) - для конечных пользователей
- ⚡ **Backend API** (FastAPI) - бизнес-логика и интеграция с OZON
- 🎨 **Админ-панель** (React + Vite) - управление и аналитика
- 🗄️ **База данных** (Supabase) - хранение данных с RLS

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+
- Supabase аккаунт
- Telegram Bot Token

### Установка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd ozon-bot-mvp
```

2. **Настройте переменные окружения**
```bash
cp env.example .env
# Отредактируйте .env файл с вашими credentials
```

3. **Backend API**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

4. **Telegram Bot**
```bash
cd bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

5. **Frontend (админ-панель)**
```bash
cd frontend
npm install
npm run dev
```

### Docker Compose (альтернатива)

```bash
docker-compose up -d
```

## 📁 Структура проекта

```
.
├── backend/              # FastAPI Backend API
│   ├── main.py          # Точка входа
│   ├── routers/         # API endpoints
│   ├── services/        # Бизнес-логика
│   ├── models/          # Pydantic модели
│   └── utils/           # Утилиты
│
├── bot/                 # Telegram Bot (aiogram)
│   ├── main.py          # Точка входа бота
│   ├── handlers/        # Обработчики команд
│   ├── keyboards/       # Клавиатуры
│   └── services/        # Сервисы бота
│
├── frontend/            # React Admin Panel
│   ├── src/
│   │   ├── pages/       # Страницы
│   │   ├── components/  # Компоненты
│   │   └── services/    # API клиенты
│   └── package.json
│
├── shared/              # Общие утилиты
├── docs/                # Документация
│   ├── DATABASE.md      # Схема БД
│   ├── supabase-setup.md
│   └── migrations/      # SQL миграции
│
├── .env.example         # Шаблон переменных
├── docker-compose.yml   # Docker конфигурация
└── README.md            # Этот файл
```

## 🔑 Конфигурация

Все настройки хранятся в `.env` файле. См. `env.example` для примера.

Основные переменные:
- `SUPABASE_URL` - URL вашего Supabase проекта
- `SUPABASE_SERVICE_ROLE_KEY` - Service role ключ
- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `BACKEND_API_URL` - URL Backend API

Подробнее: [docs/supabase-setup.md](docs/supabase-setup.md)

## 📚 Документация

- [Настройка Supabase](docs/supabase-setup.md)
- [Схема базы данных](docs/DATABASE.md)
- [Backend API](backend/README.md)
- [Telegram Bot](bot/README.md)
- [Frontend](frontend/README.md)
- [Миграции](docs/migrations/)

## 🤖 Команды Telegram бота

- `/start` - Начало работы и регистрация
- `/add <артикул>` - Добавить артикул для отслеживания
- `/list` - Показать мои артикулы
- `/check <артикул>` - Проверить статус артикула
- `/remove <артикул>` - Удалить артикул
- `/report` - Сгенерировать отчет
- `/history` - История запросов
- `/help` - Справка

## 🛠️ Технологии

### Backend
- **FastAPI** - асинхронный веб-фреймворк
- **Supabase** - БД и аутентификация
- **aiogram** - Telegram Bot framework
- **Pydantic** - валидация данных

### Frontend
- **React 18+** - UI библиотека
- **Vite** - сборщик
- **TypeScript** - типизация
- **React Query** - работа с API
- **Recharts** - графики
- **Supabase JS** - клиент для Supabase

### DevOps
- **Docker** - контейнеризация
- **GitHub Actions** - CI/CD
- **Supabase** - managed PostgreSQL

## 📊 API Documentation

После запуска Backend API, документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Тестирование

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

## 🚢 Деплой

См. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) для инструкций по деплою в production.

Рекомендуемые платформы:
- Backend: Railway / Render / DigitalOcean
- Frontend: Vercel / Netlify
- Database: Supabase (managed)

## 📈 Roadmap

- [x] Настройка Supabase и схемы БД
- [x] Структура монорепозитория
- [ ] Backend API базовая структура
- [ ] Интеграция с OZON API
- [ ] Telegram Bot обработчики
- [ ] Frontend админ-панель
- [ ] Тестирование
- [ ] Документация
- [ ] CI/CD
- [ ] Production деплой

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

MIT License - см. [LICENSE](LICENSE) файл

## 👥 Команда

Разработано командой AIronLab

## 🐛 Баг-репорты и вопросы

Используйте [GitHub Issues](../../issues) для багов и вопросов.

## 📞 Контакты

- Telegram: [@your_contact]
- Email: your@email.com

---

**Made with ❤️ by AIronLab**

