# Frontend Dockerfile - Multi-stage build
FROM node:18-alpine as build

WORKDIR /app

# Копирование package files
COPY package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Production stage
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx (если есть)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Порт
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

