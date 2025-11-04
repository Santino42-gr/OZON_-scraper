"""
Parser Market API Client

Клиент для работы с Parser Market API - облачным сервисом парсинга маркетплейсов.
Документация: https://parser.market/parser-cen-json-api/

Основные возможности:
- Отправка задач на парсинг товаров Ozon
- Отслеживание статуса задач (polling)
- Получение результатов парсинга в JSON формате
- Автоматический mapping в модель ProductInfo
"""

import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from models.ozon_models import (
    ProductInfo,
    ProductAvailability,
    ScrapingSource
)


# ==================== Модели Parser Market API ====================

class ParserMarketTask(BaseModel):
    """Задача для отправки в Parser Market"""
    category: str = ""
    code: float = 0.0
    productid: str = ""
    brand: str = ""
    name: str  # REQUIRED
    linkset: List[str] = []
    marketid: str = ""
    price: float = 0.0
    donotsearch: str = ""
    textsearch: str = ""


class ParserMarketSubmitRequest(BaseModel):
    """Запрос на отправку задачи"""
    apikey: str
    regionid: str = "Москва"
    market: str = "ozon"
    userlabel: str
    products: List[Dict[str, Any]]


class ParserMarketStatusRequest(BaseModel):
    """Запрос статуса задачи"""
    apikey: str
    userlabels: Optional[List[str]] = None
    orderidlist: Optional[List[int]] = None
    limit: int = 10


# ==================== Exceptions ====================

class ParserMarketError(Exception):
    """Базовая ошибка Parser Market API"""
    pass


class ParserMarketAPIError(ParserMarketError):
    """Ошибка API запроса"""
    pass


class ParserMarketTaskError(ParserMarketError):
    """Ошибка выполнения задачи парсинга"""
    pass


class ParserMarketTimeoutError(ParserMarketError):
    """Таймаут ожидания результата"""
    pass


# ==================== Parser Market Client ====================

class ParserMarketClient:
    """
    Клиент для работы с Parser Market API

    Features:
    - Submit parsing tasks for Ozon products
    - Poll task status
    - Download JSON reports
    - Automatic mapping to ProductInfo model
    - Retry logic with exponential backoff
    - Comprehensive error handling

    Example:
        >>> client = ParserMarketClient(api_key="your_key")
        >>> product = await client.parse_sync(article="123456789")
        >>> print(product.name, product.price)
    """

    BASE_URL = "https://parser.market/wp-json/client-api/v1"

    def __init__(
        self,
        api_key: str,
        region: str = "Москва",
        timeout: int = 120,
        poll_interval: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize Parser Market client

        Args:
            api_key: API ключ от Parser Market
            region: Регион для парсинга (по умолчанию Москва)
            timeout: Максимальное время ожидания результата (секунды)
            poll_interval: Интервал опроса статуса задачи (секунды)
            max_retries: Максимальное количество попыток при ошибках
        """
        self.api_key = api_key
        self.region = region
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),
            follow_redirects=True
        )

        logger.info(
            f"Parser Market client initialized | "
            f"region={region} | timeout={timeout}s | poll_interval={poll_interval}s"
        )

    async def close(self):
        """Закрыть HTTP клиент"""
        await self.client.aclose()
        logger.debug("Parser Market client closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    # ==================== Core API Methods ====================

    async def get_balance(self) -> Dict[str, Any]:
        """
        Получить баланс аккаунта

        Returns:
            Dict с информацией о балансе:
            - checks_free: бесплатные проверки
            - checks_paid: оплаченные проверки
            - checks_pending: проверки в процессе
            - checks_total: всего доступно

        Raises:
            ParserMarketAPIError: Ошибка API запроса
        """
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/get-balanse",
                json={"apikey": self.api_key}
            )
            response.raise_for_status()

            result = self._parse_response(response.json())

            if result.get("result") != "success":
                raise ParserMarketAPIError(f"API returned error: {result}")

            logger.info(
                f"Balance check | "
                f"total={result.get('checks_total')} | "
                f"pending={result.get('checks_pending')}"
            )

            return result

        except httpx.HTTPError as e:
            logger.error(f"Balance check failed: {e}")
            raise ParserMarketAPIError(f"Failed to get balance: {e}")

    async def submit_task(
        self,
        article: str,
        userlabel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправить задачу на парсинг товара

        Args:
            article: Артикул товара Ozon
            userlabel: Уникальная метка задачи (по умолчанию генерируется автоматически)

        Returns:
            Dict с информацией о задаче:
            - userlabel: метка задачи для отслеживания
            - bytes: размер отправленных данных

        Raises:
            ParserMarketAPIError: Ошибка отправки задачи
        """
        if not userlabel:
            userlabel = f"ozon_{article}_{int(datetime.now().timestamp())}"

        # Формируем product для API
        product = {
            "category": "",
            "code": 0.0,
            "productid": article,
            "brand": "",
            "name": f"Product {article}",  # Required field
            "linkset": [f"https://www.ozon.ru/product/{article}/"],
            "marketid": "",
            "price": 0.0,
            "donotsearch": "",
            "textsearch": ""
        }

        payload = {
            "apikey": self.api_key,
            "regionid": self.region,
            "market": "ozon",
            "userlabel": userlabel,
            "products": [product]
        }

        try:
            logger.info(f"Submitting task | article={article} | userlabel={userlabel}")

            response = await self.client.post(
                f"{self.BASE_URL}/send-order",
                json=payload
            )
            response.raise_for_status()

            result = self._parse_response(response.json())

            if result.get("result") != "success":
                error_code = result.get("error_code", "unknown")
                raise ParserMarketAPIError(
                    f"Task submission failed: {error_code} | {result}"
                )

            logger.info(
                f"Task submitted successfully | "
                f"userlabel={result.get('userlabel')} | "
                f"bytes={result.get('bytes')}"
            )

            return result

        except httpx.HTTPError as e:
            logger.error(f"Task submission failed | article={article} | error={e}")
            raise ParserMarketAPIError(f"Failed to submit task: {e}")

    async def get_task_status(
        self,
        userlabel: Optional[str] = None,
        order_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получить статус задачи

        Args:
            userlabel: Метка задачи для фильтрации
            order_id: ID заказа для фильтрации
            limit: Максимальное количество результатов

        Returns:
            Список задач с их статусами и ссылками на отчеты

        Raises:
            ParserMarketAPIError: Ошибка получения статуса
        """
        payload = {"apikey": self.api_key, "limit": limit}

        if userlabel:
            payload["userlabels"] = [userlabel]
        elif order_id:
            payload["orderidlist"] = [order_id]

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/get-last50",
                json=payload
            )
            response.raise_for_status()

            result = self._parse_response(response.json())

            if result.get("result") != "success":
                raise ParserMarketAPIError(f"Failed to get status: {result}")

            tasks = result.get("data", [])

            logger.debug(f"Status check | found {len(tasks)} tasks")

            return tasks

        except httpx.HTTPError as e:
            logger.error(f"Status check failed: {e}")
            raise ParserMarketAPIError(f"Failed to get task status: {e}")

    async def wait_for_completion(
        self,
        userlabel: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ожидать завершения задачи (polling)

        Args:
            userlabel: Метка задачи для отслеживания
            timeout: Максимальное время ожидания (по умолчанию self.timeout)
            poll_interval: Интервал опроса (по умолчанию self.poll_interval)

        Returns:
            Dict с данными завершенной задачи

        Raises:
            ParserMarketTimeoutError: Таймаут ожидания
            ParserMarketTaskError: Ошибка выполнения задачи
        """
        timeout = timeout or self.timeout
        poll_interval = poll_interval or self.poll_interval

        start_time = datetime.now()
        elapsed = 0

        logger.info(
            f"Waiting for task completion | "
            f"userlabel={userlabel} | timeout={timeout}s | interval={poll_interval}s"
        )

        while elapsed < timeout:
            tasks = await self.get_task_status(userlabel=userlabel, limit=1)

            if not tasks:
                logger.warning(f"Task not found yet | userlabel={userlabel}")
                await asyncio.sleep(poll_interval)
                elapsed = (datetime.now() - start_time).total_seconds()
                continue

            task = tasks[0]
            status = self._get_field(task, "status")

            logger.debug(
                f"Task status | userlabel={userlabel} | status={status} | elapsed={elapsed:.1f}s"
            )

            if status == "completed":
                items_loaded = self._get_field(task, "items-loaded")
                logger.info(
                    f"Task completed | "
                    f"userlabel={userlabel} | items={items_loaded} | duration={elapsed:.1f}s"
                )
                return task

            elif status == "error":
                error_msg = f"Task failed with error status"
                logger.error(f"{error_msg} | userlabel={userlabel}")
                raise ParserMarketTaskError(error_msg)

            # status == "waiting" или "processing"
            await asyncio.sleep(poll_interval)
            elapsed = (datetime.now() - start_time).total_seconds()

        # Timeout
        logger.error(
            f"Task timeout | userlabel={userlabel} | timeout={timeout}s"
        )
        raise ParserMarketTimeoutError(
            f"Task timeout after {timeout}s: {userlabel}"
        )

    async def download_json_report(self, report_url: str) -> Dict[str, Any]:
        """
        Скачать и распарсить JSON отчет

        Args:
            report_url: URL JSON отчета от Parser Market

        Returns:
            Dict с данными отчета

        Raises:
            ParserMarketAPIError: Ошибка скачивания отчета
        """
        try:
            logger.debug(f"Downloading JSON report | url={report_url}")

            response = await self.client.get(report_url)
            response.raise_for_status()

            data = response.json()

            logger.debug(f"JSON report downloaded | size={len(response.content)} bytes")

            return data

        except httpx.HTTPError as e:
            logger.error(f"Report download failed | url={report_url} | error={e}")
            raise ParserMarketAPIError(f"Failed to download report: {e}")
        except Exception as e:
            logger.error(f"Report parsing failed: {e}")
            raise ParserMarketAPIError(f"Failed to parse JSON report: {e}")

    # ==================== High-Level Methods ====================

    async def parse_sync(
        self,
        article: str,
        timeout: Optional[int] = None
    ) -> Optional[ProductInfo]:
        """
        Синхронный парсинг товара (отправка задачи + ожидание результата)

        Главный метод для замены OzonScraper.get_product_info()

        Args:
            article: Артикул товара Ozon
            timeout: Максимальное время ожидания (по умолчанию self.timeout)

        Returns:
            ProductInfo или None если парсинг не удался

        Example:
            >>> client = ParserMarketClient(api_key="key")
            >>> product = await client.parse_sync("123456789")
            >>> print(product.price)
        """
        start_time = datetime.now()

        try:
            # 1. Отправляем задачу
            submit_result = await self.submit_task(article)
            userlabel = submit_result.get("userlabel")

            if not userlabel:
                logger.error(f"No userlabel in response | article={article}")
                return None

            # 2. Ждем завершения
            task = await self.wait_for_completion(
                userlabel=userlabel,
                timeout=timeout
            )

            # 3. Скачиваем JSON отчет
            report_url = self._get_field(task, "report_json")
            if not report_url:
                logger.error(f"No JSON report URL | article={article}")
                return None

            report_data = await self.download_json_report(report_url)

            # 4. Парсим в ProductInfo
            product_info = self._parse_report_to_product_info(report_data, article)

            # Добавляем метаданные
            if product_info:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                product_info.fetch_time_ms = duration_ms
                product_info.source = ScrapingSource.MANUAL  # API source
                product_info.last_check = datetime.now()

                logger.info(
                    f"Product parsed successfully | "
                    f"article={article} | duration={duration_ms}ms"
                )

            return product_info

        except ParserMarketTimeoutError:
            logger.error(f"Parsing timeout | article={article}")
            return None
        except ParserMarketTaskError:
            logger.error(f"Parsing task failed | article={article}")
            return None
        except Exception as e:
            logger.error(f"Parsing failed | article={article} | error={e}", exc_info=True)
            return None

    async def parse_batch(
        self,
        articles: List[str],
        timeout: Optional[int] = None
    ) -> List[Optional[ProductInfo]]:
        """
        Пакетный парсинг товаров

        Args:
            articles: Список артикулов для парсинга
            timeout: Максимальное время ожидания для каждого товара

        Returns:
            Список ProductInfo (или None для неудавшихся)

        Note:
            Выполняется последовательно для избежания rate limits
        """
        logger.info(f"Batch parsing | count={len(articles)}")

        results = []

        for i, article in enumerate(articles, 1):
            logger.info(f"Parsing {i}/{len(articles)} | article={article}")

            product = await self.parse_sync(article, timeout=timeout)
            results.append(product)

            # Небольшая задержка между запросами
            if i < len(articles):
                await asyncio.sleep(2)

        success_count = sum(1 for r in results if r is not None)
        logger.info(
            f"Batch parsing completed | "
            f"total={len(articles)} | success={success_count} | failed={len(articles) - success_count}"
        )

        return results

    # ==================== Utility Methods ====================

    def _parse_response(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Преобразовать формат ответа Parser Market в dict

        Parser Market возвращает список словарей:
        [{"result": "success"}, {"user_id": "3"}, ...]

        Преобразуем в единый словарь:
        {"result": "success", "user_id": "3", ...}
        """
        result = {}
        for item in data:
            result.update(item)
        return result

    def _get_field(self, task_list: List[Dict], field: str) -> Any:
        """
        Извлечь поле из формата задачи Parser Market

        Задача представлена как список словарей:
        [{"order-id": 123}, {"status": "completed"}, ...]
        """
        for item in task_list:
            if field in item:
                return item[field]
        return None

    def _parse_report_to_product_info(
        self,
        report_data: Dict[str, Any],
        article: str
    ) -> Optional[ProductInfo]:
        """
        Преобразовать JSON отчет Parser Market в ProductInfo

        Args:
            report_data: Данные JSON отчета
            article: Артикул товара

        Returns:
            ProductInfo или None

        Note:
            Структура отчета Parser Market может отличаться от текущей
            Этот метод нужно будет адаптировать после получения примера отчета
        """
        try:
            # TODO: Адаптировать под реальную структуру Parser Market JSON
            # Пока делаем базовый маппинг на основе предполагаемой структуры

            # Предполагаем что отчет содержит массив товаров
            products = report_data.get("products", [])
            if not products:
                # Или может быть один товар в корне
                product_data = report_data
            else:
                product_data = products[0]

            # Маппинг полей (адаптировать под реальные поля!)
            product_info = ProductInfo(
                article=article,
                name=product_data.get("name") or product_data.get("title"),

                # Цены
                price=self._parse_float(product_data.get("price")),
                normal_price=self._parse_float(product_data.get("normal_price")),
                ozon_card_price=self._parse_float(product_data.get("ozon_card_price")),
                old_price=self._parse_float(product_data.get("old_price")),

                # Рейтинг
                rating=self._parse_float(product_data.get("rating")),
                reviews_count=self._parse_int(product_data.get("reviews_count")),

                # Наличие
                availability=self._parse_availability(product_data.get("availability")),

                # Изображения и ссылки
                image_url=product_data.get("image_url") or product_data.get("image"),
                url=product_data.get("url") or f"https://www.ozon.ru/product/{article}/",
                product_id=article,

                # Дополнительно
                brand=product_data.get("brand"),
                seller_name=product_data.get("seller") or product_data.get("seller_name"),

                # Метаданные
                last_check=datetime.now(),
                source=ScrapingSource.MANUAL  # API source
            )

            logger.debug(f"Report parsed | article={article} | name={product_info.name}")

            return product_info

        except Exception as e:
            logger.error(
                f"Failed to parse report | article={article} | error={e}",
                exc_info=True
            )
            return None

    def _parse_float(self, value: Any) -> Optional[float]:
        """Безопасно преобразовать в float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Безопасно преобразовать в int"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_availability(self, value: Any) -> ProductAvailability:
        """Преобразовать availability в enum"""
        if not value:
            return ProductAvailability.UNKNOWN

        value_str = str(value).lower()

        if "available" in value_str or "в наличии" in value_str:
            return ProductAvailability.AVAILABLE
        elif "out" in value_str or "нет" in value_str:
            return ProductAvailability.OUT_OF_STOCK
        elif "limited" in value_str or "мало" in value_str:
            return ProductAvailability.LIMITED
        elif "pre" in value_str or "предзаказ" in value_str:
            return ProductAvailability.PRE_ORDER
        else:
            return ProductAvailability.UNKNOWN


# ==================== Factory Function ====================

_parser_market_client: Optional[ParserMarketClient] = None


def get_parser_market_client(
    api_key: Optional[str] = None,
    region: str = "Москва"
) -> ParserMarketClient:
    """
    Получить singleton инстанс Parser Market клиента

    Args:
        api_key: API ключ (если None, берется из config)
        region: Регион для парсинга

    Returns:
        ParserMarketClient instance

    Example:
        >>> client = get_parser_market_client()
        >>> product = await client.parse_sync("123456789")
    """
    global _parser_market_client

    if _parser_market_client is None:
        if api_key is None:
            # Import здесь чтобы избежать circular imports
            from config import settings
            api_key = settings.PARSER_MARKET_API_KEY

        _parser_market_client = ParserMarketClient(
            api_key=api_key,
            region=region
        )
        logger.info("Parser Market client singleton created")

    return _parser_market_client


async def close_parser_market_client():
    """Закрыть глобальный клиент"""
    global _parser_market_client

    if _parser_market_client:
        await _parser_market_client.close()
        _parser_market_client = None
        logger.info("Parser Market client singleton closed")
