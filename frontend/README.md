# Frontend - React Admin Panel

Веб админ-панель для управления OZON Bot на основе React + Vite + TypeScript.

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd frontend
npm install
```

### Запуск в режиме разработки

```bash
npm run dev
```

Откроется по адресу: http://localhost:5173

### Сборка для production

```bash
npm run build
npm run preview  # Предпросмотр production сборки
```

## 📁 Структура

```
frontend/
├── public/              # Статические файлы
├── src/
│   ├── main.tsx        # Точка входа
│   ├── App.tsx         # Главный компонент
│   ├── pages/          # Страницы приложения
│   │   ├── Dashboard.tsx
│   │   ├── Users.tsx
│   │   ├── Articles.tsx
│   │   ├── Logs.tsx
│   │   └── Login.tsx
│   ├── components/     # Переиспользуемые компоненты
│   │   ├── Layout/
│   │   ├── Header/
│   │   ├── Sidebar/
│   │   └── Table/
│   ├── services/       # API клиенты
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── supabase.ts
│   ├── hooks/          # Custom hooks
│   │   └── useAuth.ts
│   ├── types/          # TypeScript типы
│   │   └── index.ts
│   ├── utils/          # Утилиты
│   │   └── helpers.ts
│   └── styles/         # Глобальные стили
│       └── index.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.example
```

## 🎨 Страницы

### Dashboard (`/`)
- Статистика системы
- Графики и аналитика
- Активность пользователей

### Users (`/users`)
- Список всех пользователей
- Поиск и фильтрация
- Блокировка/разблокировка

### Articles (`/articles`)
- Все отслеживаемые артикулы
- Статус проверок
- Проблемные артикулы

### Logs (`/logs`)
- Системные логи
- Фильтрация по уровню и дате
- Экспорт логов

### Login (`/login`)
- Вход через Supabase Auth
- Email + Password

## 🔧 Технологии

- **React 18** - UI библиотека
- **TypeScript** - типизация
- **Vite** - быстрый сборщик
- **React Router** - роутинг
- **React Query (TanStack Query)** - управление состоянием API
- **Supabase JS** - клиент для Supabase Auth & DB
- **Recharts** - графики и диаграммы
- **Tailwind CSS** - стилизация (или Ant Design/MUI)

## 📦 Основные зависимости

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "@tanstack/react-query": "^5.56.2",
    "@supabase/supabase-js": "^2.45.4",
    "recharts": "^2.12.7",
    "axios": "^1.7.7"
  },
  "devDependencies": {
    "@types/react": "^18.3.9",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.2",
    "typescript": "^5.6.2",
    "vite": "^5.4.8"
  }
}
```

## 🔐 Аутентификация

Используется Supabase Auth:

```typescript
// Вход
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'admin@example.com',
  password: 'password'
})

// Проверка сессии
const { data: { session } } = await supabase.auth.getSession()

// Выход
await supabase.auth.signOut()
```

## 🎯 API Интеграция

### Supabase Client

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

### Backend API Client

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

## 🧪 Тестирование

```bash
# Unit тесты (Vitest)
npm run test

# E2E тесты (Playwright)
npm run test:e2e

# Coverage
npm run test:coverage
```

## 🎨 Стилизация

### Tailwind CSS
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Ant Design (альтернатива)
```bash
npm install antd
```

## 🔄 Переменные окружения

Создайте `.env` файл:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_BACKEND_API_URL=http://localhost:8000
```

## 🚀 Деплой

### Vercel
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
netlify deploy --prod --dir=dist
```

### Nginx
```bash
npm run build
# Скопируйте dist/ в /var/www/html
```

## 📊 Компоненты Dashboard

### Статистика
- Общее количество пользователей
- Активных артикулов
- Запросов сегодня
- Ошибок за последний час

### Графики
- Активность пользователей (по дням)
- Количество запросов (по часам)
- Популярные артикулы
- Статистика ошибок

## 🛠️ Разработка

### Добавление новой страницы

1. Создайте компонент в `src/pages/`
2. Добавьте роут в `App.tsx`
3. Добавьте пункт в сайдбар

### Добавление API endpoint

1. Создайте функцию в `src/services/api.ts`
2. Используйте React Query для кеширования
3. Добавьте типы в `src/types/index.ts`

## 🔒 Безопасность

- ✅ Защита роутов (требуется авторизация)
- ✅ RLS политики в Supabase
- ✅ CORS настроен на Backend
- ✅ Валидация всех inputs
- ✅ Защита от XSS

## 📱 Адаптивность

Панель полностью адаптивна:
- Desktop: полный функционал
- Tablet: оптимизированная навигация
- Mobile: мобильное меню

## 🐛 Отладка

```bash
# Режим разработки с source maps
npm run dev

# Проверка типов
npm run type-check

# Lint
npm run lint
```

## 📈 Оптимизация

- Code splitting по роутам
- Lazy loading компонентов
- Оптимизация изображений
- Минификация и gzip
- CDN для статики

## 🔄 Обновление

```bash
git pull
npm install
npm run build
```

