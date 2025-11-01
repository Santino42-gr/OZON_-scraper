# Быстрый чек-лист деплоя обновлений

## Для обновления уже развернутого проекта на VPS

---

## Шаг 1: Подготовка локально

### 1.1 Проверка изменений
```bash
# Убедитесь, что все изменения закоммичены
git status

# Если есть незакоммиченные изменения, закоммитьте их
git add .
git commit -m "Описание изменений"
```

### 1.2 Пуш изменений в репозиторий
```bash
# Отправьте изменения в удаленный репозиторий
git push origin main
# или
git push origin master
```

---

## Шаг 2: Подключение к VPS

```bash
# Подключитесь к вашему VPS серверу
ssh your_username@your_vps_ip

API-key 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

# Перейдите в директорию проекта
cd ~/ozon-scraper
```

---

## Шаг 3: Получение обновлений

```bash
# Получите последние изменения из репозитория
git pull origin main
```

---

## Шаг 4: Проверка .env файла

```bash
# Убедитесь, что .env файл существует и актуален
ls -la .env

# Если нужно, проверьте содержимое (не изменяйте без необходимости)
cat .env | grep -E "SUPABASE|TELEGRAM|API"
```

**ВАЖНО**: Если в обновлениях есть новые переменные окружения, добавьте их в `.env` файл перед запуском!

---

## Шаг 5: Остановка контейнеров

```bash
# Остановите текущие контейнеры
docker-compose -f docker-compose.prod.yml down
```

---

## Шаг 6: Пересборка и запуск

```bash
# Пересборка образов (если были изменения в коде)
docker-compose -f docker-compose.prod.yml build

# Запуск контейнеров в фоновом режиме
docker-compose -f docker-compose.prod.yml up -d
```

---

## Шаг 7: Проверка статуса

```bash
# Проверьте, что все контейнеры запущены
docker-compose -f docker-compose.prod.yml ps

# Должны быть запущены все 3 контейнера:
# - ozon-backend
# - ozon-bot
# - ozon-frontend
```

---

## Шаг 8: Проверка работоспособности

```bash
# Проверка Backend
curl http://localhost:8000/health

# Проверка Frontend
curl -I http://localhost/

# Просмотр логов на наличие ошибок
docker-compose -f docker-compose.prod.yml logs --tail=50
```

---

## Шаг 9: Мониторинг (опционально)

```bash
# Просмотр логов в реальном времени (Ctrl+C для выхода)
docker-compose -f docker-compose.prod.yml logs -f

# Или логов конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f bot
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## Быстрый деплой одной командой

Если у вас есть скрипт `deploy.sh`:

```bash
# На VPS сервере
cd ~/ozon-scraper
./deploy.sh
```

Или вручную:

```bash
cd ~/ozon-scraper && \
git pull origin main && \
docker-compose -f docker-compose.prod.yml down && \
docker-compose -f docker-compose.prod.yml build && \
docker-compose -f docker-compose.prod.yml up -d && \
docker-compose -f docker-compose.prod.yml ps
```

---

## Чек-лист быстрого деплоя

- [ ] Локально: изменения закоммичены и запушены в Git
- [ ] Подключение к VPS: успешное SSH подключение
- [ ] Обновление кода: `git pull` выполнен успешно
- [ ] Проверка .env: файл существует и содержит все необходимые переменные
- [ ] Остановка: старые контейнеры остановлены
- [ ] Сборка: новые образы собраны без ошибок
- [ ] Запуск: контейнеры запущены и работают
- [ ] Статус: все 3 контейнера в статусе "Up"
- [ ] Health check: Backend отвечает на `/health`
- [ ] Логи: отсутствуют критические ошибки

---

## Частые проблемы и решения

### Проблема: Контейнер не запускается после обновления

```bash
# Проверьте логи конкретного контейнера
docker-compose -f docker-compose.prod.yml logs backend

# Пересоздайте контейнер
docker-compose -f docker-compose.prod.yml up -d --force-recreate backend
```

### Проблема: Ошибки при сборке образа

```bash
# Очистите старые образы и пересоберите
docker-compose -f docker-compose.prod.yml build --no-cache backend

# Затем запустите
docker-compose -f docker-compose.prod.yml up -d
```

### Проблема: Конфликты в Git

```bash
# Сохраните изменения локально
git stash

# Получите обновления
git pull origin main

# Примените сохраненные изменения
git stash pop
```

### Проблема: Изменения не применяются

```bash
# Полная пересборка без кеша
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

---

## Откат к предыдущей версии

Если что-то пошло не так:

```bash
# Перейдите на предыдущий коммит
git log --oneline  # Найдите нужный коммит
git checkout <commit-hash>

# Пересоберите и перезапустите
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

Или вернитесь на предыдущую ветку:

```bash
git checkout main
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## Оптимизация: быстрый деплой без пересборки

Если изменился только код (не зависимости), можно использовать cached слои:

```bash
# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление кода
git pull origin main

# Запуск (использует существующие образы)
docker-compose -f docker-compose.prod.yml up -d

# Если нужна пересборка только измененных сервисов
docker-compose -f docker-compose.prod.yml build backend  # если изменился только backend
docker-compose -f docker-compose.prod.yml up -d
```

**Примечание**: Используйте полную пересборку, если:
- Изменились зависимости (requirements.txt, package.json)
- Изменились Dockerfile'ы
- Изменились переменные окружения, влияющие на сборку

---

## Время выполнения

- Обновление кода: ~10-30 секунд
- Пересборка образов: ~3-10 минут (в зависимости от изменений)
- Запуск контейнеров: ~10-30 секунд
- Проверка работоспособности: ~1-2 минуты

**Общее время**: ~5-15 минут в зависимости от объема изменений

---

## Полезные команды

```bash
# Просмотр изменений перед деплоем
git diff HEAD~1

# Просмотр истории коммитов
git log --oneline -10

# Проверка использования ресурсов
docker stats

# Очистка неиспользуемых образов (после успешного деплоя)
docker image prune -a
```

---

## Дополнительная информация

Для полной инструкции по первоначальному деплою см. [VPS_DEPLOYMENT.md](./VPS_DEPLOYMENT.md)
