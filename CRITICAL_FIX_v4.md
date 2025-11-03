# 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ v4 - Парсинг страницы товара

## Проблема v3

После исправления URL на `/product/` **всё равно получали ошибку**:
```
⚠️  No search results found for 1066650955
```

## Причина

**Логика парсинга была для страницы ПОИСКА, а не для страницы ТОВАРА!**

### Что было не так (строки 426-430):

```python
# Ищем первый результат поиска (обычно это наш товар)
search_results = soup.find_all('div', {'data-widget': 'searchResultsV2'})
if not search_results:
    logger.warning(f"⚠️  No search results found for {article}")
    return None
```

**Проблема:**
- Искали `searchResultsV2` - это селектор для **страницы поиска** `/search/`
- Но теперь мы на странице `/product/` - там **НЕТ** `searchResultsV2`!
- Поэтому всегда возвращали `None`

## Решение

Полностью переписали метод `_parse_product_from_html` **по образцу Telegram бота**.

---

## Что изменено

### 1. Парсинг заголовка (строки 429-437)

**Было:**
```python
name_elem = soup.find('span', class_=lambda x: x and 'tsBody500Medium' in x)
```

**Стало:**
```python
# Ищем H1 - заголовок товара
name_elem = soup.find('h1')
```

### 2. Парсинг цены через JSON (строки 444-485)

**Добавлено из Telegram бота:**

```python
# Метод 1: Ищем JSON в HTML (window.__INITIAL_STATE__)
json_patterns = [
    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
    r'<script[^>]*data-widget[^>]*>([^<]*)</script>',
]

for pattern in json_patterns:
    matches = re.findall(pattern, html, re.DOTALL)
    for match in matches:
        try:
            if isinstance(match, str) and match.startswith('{'):
                data = json.loads(match)

                # Рекурсивно ищем price в JSON
                def find_price(obj):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in ['price', 'currentPrice', 'finalPrice', 'amount']:
                                # ... возвращаем цену
                    # ... рекурсия по dict и list
```

**Это КРИТИЧНО!** Telegram бот извлекает цену из JSON, встроенного в HTML.

### 3. Парсинг цены через селекторы (строки 487-508)

**Было:**
```python
normal_price_elem = soup.find('span', {'data-widget': 'webPrice'})
# ... сложная логика с multiple селекторами
```

**Стало (как в Telegram боте):**
```python
price_selectors = [
    {'data-widget': 'webPrice'},
    {'data-widget': 'price'},
]

for selector in price_selectors:
    price_elem = soup.find('span', selector)
    if not price_elem:
        price_elem = soup.find('div', selector)

    if price_elem:
        price_text = price_elem.get_text(strip=True)
        # Regex как в Telegram боте
        price_match = re.search(r'(\d[\d\s]*)\s*[₽ррубRUB]', price_text.replace(',', ''))
        # ...
```

### 4. Добавлен import json (строка 24)

```python
import json
```

---

## Файлы изменены

### `backend/services/ozon_scraper.py`

**Строка 24:** Добавлен `import json`

**Строки 412-513:** Полностью переписан метод `_parse_product_from_html`:
- Убрали поиск `searchResultsV2` (это для `/search/`)
- Добавили парсинг `h1` для заголовка
- Добавили JSON parsing (как в Telegram боте)
- Упростили селекторы цены (как в Telegram боте)

---

## Ключевые различия: Наш код vs Telegram бот

| Аспект | Было (наш код) | Стало (как в боте) |
|--------|----------------|-------------------|
| URL | `/search/?text=...` | `/product/...` ✅ |
| Ищем селектор | `searchResultsV2` | `h1` ✅ |
| Парсинг заголовка | `span.tsBody500Medium` | `h1` ✅ |
| Парсинг цены | Только селекторы | JSON + селекторы ✅ |
| JSON parsing | ❌ Не было | ✅ Есть |

---

## Деплой v4

```bash
./redeploy.sh
```

или вручную:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

---

## Тестирование

### 1. Отправить артикул:
```
1066650955
```

### 2. Проверить логи:
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Ожидаемый результат:
```
🌐 Scraping 1066650955 via Playwright: https://www.ozon.ru/product/1066650955/
✅ Page loaded, found selector: h1
✅ Parsed 1066650955: normal_price=XXX, name=...
💰 Цена: XXX ₽
```

---

## История версий

### v1
- ❌ URL: `/search/`
- ❌ Парсинг: для страницы поиска
- ❌ JSON: нет

### v2
- ❌ URL: `/search/`
- ❌ Парсинг: для страницы поиска
- ✅ Anti-detection: усилена

### v3
- ✅ URL: `/product/` **ИСПРАВЛЕН**
- ❌ Парсинг: для страницы поиска (ошибка осталась!)
- ✅ Anti-detection: усилена

### v4 (текущая)
- ✅ URL: `/product/`
- ✅ Парсинг: **для страницы товара** (как в Telegram боте)
- ✅ JSON parsing: добавлен
- ✅ Anti-detection: усилена

---

## Вывод

**Главная ошибка:** Мы изменили URL на `/product/`, но **не изменили логику парсинга**!

Страница `/product/` имеет **совершенно другую структуру**, чем `/search/`:
- Нет `searchResultsV2`
- Заголовок в `h1`, а не в `span`
- Цена часто в JSON `window.__INITIAL_STATE__`

Telegram бот знает эту структуру и правильно парсит.

---

**v4 должна заработать! Все критические ошибки исправлены. 🚀**
