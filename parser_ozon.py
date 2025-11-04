#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для парсинга товара с Ozon через API parser.market
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Optional, Tuple


class ParserMarketClient:
    """Клиент для работы с API parser.market"""
    
    BASE_URL = "https://parser.market/wp-json/client-api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _parse_response(response_data) -> Dict:
        """
        Преобразует ответ API из формата списка словарей в обычный словарь
        
        API возвращает: [{"key1": "value1"}, {"key2": "value2"}, ...]
        Преобразуем в: {"key1": "value1", "key2": "value2", ...}
        """
        if isinstance(response_data, list):
            result = {}
            for item in response_data:
                if isinstance(item, dict):
                    result.update(item)
            return result
        elif isinstance(response_data, dict):
            return response_data
        else:
            return {}
    
    def get_balance(self) -> Dict:
        """Получить баланс проверок"""
        url = f"{self.BASE_URL}/get-balanse"
        payload = {"apikey": self.api_key}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении баланса: {e}")
            return {}
    
    def send_order(
        self,
        article: str,
        region: str = "Москва",
        market: str = "ozon",
        userlabel: Optional[str] = None,
        use_marketid: bool = True,
        product_link: Optional[str] = None
    ) -> Dict:
        """
        Отправить задание на парсинг товара
        
        Args:
            article: Артикул/SKU товара
            region: Регион для парсинга (по умолчанию "Москва")
            market: Маркетплейс ("ozon", "wbs", "ym" и т.д.)
            userlabel: Метка задания (опционально)
            use_marketid: Если True, использует marketid для Ozon (SKU ID), иначе productid (артикул продавца)
            product_link: Ссылка на карточку товара (опционально, улучшает поиск)
        """
        url = f"{self.BASE_URL}/send-order"
        
        if userlabel is None:
            userlabel = f"ART_{article}"
        
        # Для Ozon marketid - это SKU ID товара на маркетплейсе
        # productid - это артикул продавца
        if market == "ozon" and use_marketid:
            marketid_value = str(article)
            productid_value = ""
        else:
            marketid_value = ""
            productid_value = str(article)
        
        # Формируем linkset если есть ссылка
        linkset = []
        if product_link:
            linkset = [product_link]
        
        payload = {
            "apikey": self.api_key,
            "regionid": region,
            "market": market,
            "userlabel": userlabel,
            "products": [
                {
                    "category": "",
                    "code": 0.0,
                    "productid": productid_value,
                    "brand": "",
                    "name": f"Товар {article}",  # Обязательное поле
                    "linkset": linkset,
                    "marketid": marketid_value,
                    "price": 0.0,
                    "donotsearch": "",
                    "textsearch": ""
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке задания: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            return {}
    
    def get_last_orders(self, limit: int = 50) -> Dict:
        """Получить статус последних заданий"""
        url = f"{self.BASE_URL}/get-last50"
        payload = {
            "apikey": self.api_key,
            "limit": limit
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            # Для get-last50 ответ уже в правильном формате с ключом "data"
            return self._parse_response(data)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении статуса заданий: {e}")
            return {}
    
    def get_order_by_id(self, order_ids: list) -> Dict:
        """Получить статус заданий по ID"""
        url = f"{self.BASE_URL}/get-last50"
        payload = {
            "apikey": self.api_key,
            "orderidlist": order_ids,
            "limit": len(order_ids)
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении статуса заданий: {e}")
            return {}
    
    def wait_for_completion(self, userlabel: str, max_wait: int = 300, check_interval: int = 10) -> Optional[Dict]:
        """
        Ожидать завершения задания
        
        Args:
            userlabel: Метка задания
            max_wait: Максимальное время ожидания в секундах
            check_interval: Интервал проверки в секундах
        
        Returns:
            Информация о задании с результатами или None
        """
        start_time = time.time()
        
        print(f"Ожидание завершения задания '{userlabel}'...")
        
        while time.time() - start_time < max_wait:
            orders = self.get_last_orders(limit=10)
            
            if orders and "data" in orders:
                for order in orders["data"]:
                    # Преобразуем список словарей в обычный словарь
                    order_dict = {}
                    for item in order:
                        if isinstance(item, dict):
                            order_dict.update(item)
                    
                    if order_dict.get("userlabel") == userlabel:
                        status = order_dict.get("status", "")
                        print(f"Статус задания: {status}")
                        
                        if status == "completed":
                            print("Задание завершено!")
                            return order_dict
                        elif status == "error":
                            print("Ошибка при выполнении задания")
                            return order_dict
            
            time.sleep(check_interval)
            print(f"Ожидание... ({int(time.time() - start_time)} сек)")
        
        print(f"Превышено время ожидания ({max_wait} сек)")
        return None


def download_file(url: str, filename: str) -> bool:
    """Скачать файл по URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Файл сохранен: {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании файла: {e}")
        return False


def parse_json_data(json_data: dict) -> Tuple[bool, dict]:
    """
    Парсит JSON данные и извлекает информацию о товаре
    
    Args:
        json_data: JSON данные (словарь)
    
    Returns:
        (found: bool, info: dict) - найден ли товар и полная информация о нем
    """
    try:
        if not json_data.get('data') or len(json_data['data']) == 0:
            return False, {}
        
        item = json_data['data'][0]
        
        # Основная информация о товаре
        offers_count = item.get('Offers_counted', 0)
        name_found = item.get('Name_found', '')
        productid_found = item.get('Productid_found', '')
        brand_found = item.get('Brand_found', '')
        category_found = item.get('Category_found', '')
        rating_found = item.get('Rating_found', 0.0)
        rates_found = item.get('Rates_found', 0)
        
        # Проверяем ServiceData
        service_data = item.get('ServiceData', {})
        is_success = service_data.get('O_IsSuccess', False)
        errors = service_data.get('O_errors', 0)
        
        # Обрабатываем все предложения (offers)
        offers = item.get('offers', [])
        valid_offers = []
        
        for offer in offers:
            if offer.get('Name') or offer.get('Price', 0) > 0:
                offer_data = {
                    'name': offer.get('Name', ''),
                    'price': offer.get('Price', 0),
                    'old_price': offer.get('OldPrice', 0),
                    'promo_price': offer.get('PromoPrice', 0),
                    'ozon_card_price': offer.get('OZON_couponPrice', 0),  # Цена по карте Ozon
                    'shop_name': offer.get('ShopName', ''),
                    'shop_rating': offer.get('ShopRating', 0.0),
                    'marketid': offer.get('Marketid', ''),
                    'sku_id': offer.get('Skuid', ''),
                    'shop_id': offer.get('ShopId', ''),
                    'offer_id': offer.get('OfferId', ''),
                    'stock_count': offer.get('Ozon_stockcount', 0),
                    'available': offer.get('Ozon_available', False),
                    'seller_price': offer.get('Ozon_sellerprice', 0),
                    'delivery_term': offer.get('DeliveryTerm', ''),
                    'delivery_cost': offer.get('DeliveryCost', 0),
                    'pickup_term': offer.get('PickupTerm', ''),
                    'pickup_cost': offer.get('PickupCost', 0),
                    'rating': offer.get('SkuRating', 0.0),
                    'reviews_count': offer.get('SkuRates', 0),
                    'shop_reviews': offer.get('ShopReviews', 0),
                    'url': offer.get('ShopUrl', ''),
                    'shop_url': offer.get('ShopUrl', ''),
                }
                valid_offers.append(offer_data)
        
        # Товар считается найденным, если:
        # 1. Есть успешный результат в ServiceData ИЛИ
        # 2. Найдено предложений > 0 ИЛИ
        # 3. Есть валидные предложения
        found = is_success or offers_count > 0 or len(valid_offers) > 0
        
        # Основное предложение (первое с ценой или первое)
        main_offer = None
        if valid_offers:
            # Ищем предложение с минимальной ценой
            offers_with_price = [o for o in valid_offers if o['price'] > 0]
            if offers_with_price:
                main_offer = min(offers_with_price, key=lambda x: x['price'])
            else:
                main_offer = valid_offers[0]
        
        info = {
            'found': found,
            'offers_count': offers_count,
            'valid_offers_count': len(valid_offers),
            'name': name_found,
            'brand': brand_found,
            'category': category_found,
            'productid': productid_found,
            'rating': rating_found,
            'rates': rates_found,
            'is_success': is_success,
            'errors': errors,
            'main_offer': main_offer,
            'all_offers': valid_offers,
        }
        
        return found, info
        
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_product_found(json_file: str) -> Tuple[bool, dict]:
    """
    Проверяет, найден ли товар в JSON файле (для обратной совместимости)
    
    Returns:
        (found: bool, info: dict) - найден ли товар и информация о нем
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return parse_json_data(data)
    except Exception as e:
        print(f"Ошибка при проверке результата: {e}")
        return False, {}


def parse_article_marketid(
    client: ParserMarketClient,
    article: str,
    region: str = "Москва",
    market: str = "ozon",
    max_wait: int = 600,
    check_interval: int = 15
) -> Optional[Dict]:
    """
    Парсит товар используя только метод marketid (SKU ID Ozon)
    
    Returns:
        Словарь с результатами:
        {
            'found': bool,
            'method': 'marketid',
            'product_info': dict,  # Полная информация о товаре
            'order_info': dict,     # Информация о задании
        }
        или None если товар не найден
    """
    print(f"\n{'='*60}")
    print(f"Поиск товара по артикулу (marketid): {article}")
    print(f"{'='*60}\n")
    
    userlabel = f"OZON_{article}_MID"
    
    result = client.send_order(
        article=article,
        region=region,
        market=market,
        userlabel=userlabel,
        use_marketid=True
    )
    
    if result and result.get("result") == "success":
        print("✓ Задание отправлено")
        completed = client.wait_for_completion(userlabel, max_wait=max_wait, check_interval=check_interval)
        
        if completed and "report_json" in completed:
            json_url = completed["report_json"]
            json_file = f"result_{article}_mid.json"
            if download_file(json_url, json_file):
                # Загружаем JSON для обработки
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                found, info = parse_json_data(json_data)
                
                if found:
                    print(f"\n{'='*60}")
                    print("✓ ТОВАР НАЙДЕН по marketid (SKU ID Ozon)!")
                    print(f"{'='*60}")
                    
                    # Выводим основную информацию
                    if info.get('name'):
                        print(f"Название: {info['name']}")
                    if info.get('brand'):
                        print(f"Бренд: {info['brand']}")
                    if info.get('main_offer'):
                        offer = info['main_offer']
                        print(f"Цена: {offer.get('price', 0)} ₽")
                        if offer.get('ozon_card_price', 0) > 0:
                            print(f"Цена по карте Ozon: {offer.get('ozon_card_price', 0)} ₽")
                        if offer.get('promo_price', 0) > 0:
                            print(f"Промо цена: {offer.get('promo_price', 0)} ₽")
                        if offer.get('old_price', 0) > 0:
                            print(f"Старая цена: {offer.get('old_price', 0)} ₽")
                        print(f"Магазин: {offer.get('shop_name', 'N/A')}")
                        if offer.get('rating', 0) > 0:
                            print(f"Рейтинг: {offer.get('rating', 0)} ({offer.get('reviews_count', 0)} отзывов)")
                    print(f"Найдено предложений: {info.get('valid_offers_count', 0)}")
                    
                    # Скачиваем все форматы
                    if "report_csv" in completed:
                        download_file(completed["report_csv"], f"result_{article}.csv")
                    if "report_xlsx" in completed:
                        download_file(completed["report_xlsx"], f"result_{article}.xlsx")
                    if "report_xml" in completed:
                        download_file(completed["report_xml"], f"result_{article}.xlsm")
                    
                    # Переименовываем JSON в основной файл
                    if os.path.exists(json_file):
                        os.rename(json_file, f"result_{article}.json")
                    
                    # Возвращаем структурированные данные
                    return {
                        'found': True,
                        'method': 'marketid',
                        'product_info': info,
                        'order_info': completed,
                        'json_data': json_data,
                    }
                else:
                    print(f"✗ Товар не найден по marketid")
                    print(f"  Ошибок: {info.get('errors', 0)}")
                    return None
    else:
        print("✗ Ошибка при отправке задания")
        if result:
            print(f"  Ответ API: {result}")
        return None
    
    print(f"\n{'='*60}")
    print("✗ Товар не найден")
    print(f"{'='*60}")
    print("Возможные причины:")
    print("  1. Артикул указан неверно")
    print("  2. Товар отсутствует на Ozon в указанном регионе")
    print("  3. Товар снят с продажи")
    print(f"\nПроверьте файл result_{article}_mid.json для деталей")
    
    return None


def parse_article_auto(
    client: ParserMarketClient,
    article: str,
    region: str = "Москва",
    market: str = "ozon",
    max_wait: int = 600,
    check_interval: int = 15
) -> Optional[Dict]:
    """
    Автоматически парсит товар, пробуя оба варианта (productid и marketid)
    
    Returns:
        Словарь с результатами:
        {
            'found': bool,
            'method': 'productid' | 'marketid' | None,
            'product_info': dict,  # Полная информация о товаре
            'order_info': dict,     # Информация о задании
        }
        или None если товар не найден
    """
    print(f"\n{'='*60}")
    print(f"Автоматический поиск товара по артикулу: {article}")
    print(f"{'='*60}\n")
    
    # Сначала пробуем productid (артикул продавца)
    print("Попытка 1: Поиск по productid (артикул продавца)...")
    userlabel1 = f"OZON_{article}_PID"
    
    result1 = client.send_order(
        article=article,
        region=region,
        market=market,
        userlabel=userlabel1,
        use_marketid=False
    )
    
    if result1 and result1.get("result") == "success":
        print("✓ Задание отправлено")
        completed1 = client.wait_for_completion(userlabel1, max_wait=max_wait, check_interval=check_interval)
        
        if completed1 and "report_json" in completed1:
            json_url = completed1["report_json"]
            json_file = f"result_{article}_pid.json"
            if download_file(json_url, json_file):
                # Загружаем JSON для обработки
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                found, info = parse_json_data(json_data)
                
                if found:
                    print(f"\n{'='*60}")
                    print("✓ ТОВАР НАЙДЕН по productid (артикул продавца)!")
                    print(f"{'='*60}")
                    
                    # Выводим основную информацию
                    if info.get('name'):
                        print(f"Название: {info['name']}")
                    if info.get('brand'):
                        print(f"Бренд: {info['brand']}")
                    if info.get('main_offer'):
                        offer = info['main_offer']
                        print(f"Цена: {offer.get('price', 0)} ₽")
                        if offer.get('ozon_card_price', 0) > 0:
                            print(f"Цена по карте Ozon: {offer.get('ozon_card_price', 0)} ₽")
                        if offer.get('promo_price', 0) > 0:
                            print(f"Промо цена: {offer.get('promo_price', 0)} ₽")
                        if offer.get('old_price', 0) > 0:
                            print(f"Старая цена: {offer.get('old_price', 0)} ₽")
                        print(f"Магазин: {offer.get('shop_name', 'N/A')}")
                        if offer.get('rating', 0) > 0:
                            print(f"Рейтинг: {offer.get('rating', 0)} ({offer.get('reviews_count', 0)} отзывов)")
                    print(f"Найдено предложений: {info.get('valid_offers_count', 0)}")
                    
                    # Скачиваем все форматы
                    if "report_csv" in completed1:
                        download_file(completed1["report_csv"], f"result_{article}.csv")
                    if "report_xlsx" in completed1:
                        download_file(completed1["report_xlsx"], f"result_{article}.xlsx")
                    if "report_xml" in completed1:
                        download_file(completed1["report_xml"], f"result_{article}.xlsm")
                    
                    # Переименовываем JSON в основной файл
                    if os.path.exists(json_file):
                        os.rename(json_file, f"result_{article}.json")
                    
                    # Возвращаем структурированные данные
                    return {
                        'found': True,
                        'method': 'productid',
                        'product_info': info,
                        'order_info': completed1,
                        'json_data': json_data,
                    }
                else:
                    print(f"✗ Товар не найден по productid")
                    print(f"  Ошибок: {info.get('errors', 0)}")
    
    # Если не нашли, пробуем marketid (SKU ID Ozon)
    print(f"\n{'='*60}")
    print("Попытка 2: Поиск по marketid (SKU ID Ozon)...")
    print(f"{'='*60}\n")
    
    userlabel2 = f"OZON_{article}_MID"
    
    result2 = client.send_order(
        article=article,
        region=region,
        market=market,
        userlabel=userlabel2,
        use_marketid=True
    )
    
    if result2 and result2.get("result") == "success":
        print("✓ Задание отправлено")
        completed2 = client.wait_for_completion(userlabel2, max_wait=max_wait, check_interval=check_interval)
        
        if completed2 and "report_json" in completed2:
            json_url = completed2["report_json"]
            json_file = f"result_{article}_mid.json"
            if download_file(json_url, json_file):
                # Загружаем JSON для обработки
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                found, info = parse_json_data(json_data)
                
                if found:
                    print(f"\n{'='*60}")
                    print("✓ ТОВАР НАЙДЕН по marketid (SKU ID Ozon)!")
                    print(f"{'='*60}")
                    
                    # Выводим основную информацию
                    if info.get('name'):
                        print(f"Название: {info['name']}")
                    if info.get('brand'):
                        print(f"Бренд: {info['brand']}")
                    if info.get('main_offer'):
                        offer = info['main_offer']
                        print(f"Цена: {offer.get('price', 0)} ₽")
                        if offer.get('ozon_card_price', 0) > 0:
                            print(f"Цена по карте Ozon: {offer.get('ozon_card_price', 0)} ₽")
                        if offer.get('promo_price', 0) > 0:
                            print(f"Промо цена: {offer.get('promo_price', 0)} ₽")
                        if offer.get('old_price', 0) > 0:
                            print(f"Старая цена: {offer.get('old_price', 0)} ₽")
                        print(f"Магазин: {offer.get('shop_name', 'N/A')}")
                        if offer.get('rating', 0) > 0:
                            print(f"Рейтинг: {offer.get('rating', 0)} ({offer.get('reviews_count', 0)} отзывов)")
                    print(f"Найдено предложений: {info.get('valid_offers_count', 0)}")
                    
                    # Скачиваем все форматы
                    if "report_csv" in completed2:
                        download_file(completed2["report_csv"], f"result_{article}.csv")
                    if "report_xlsx" in completed2:
                        download_file(completed2["report_xlsx"], f"result_{article}.xlsx")
                    if "report_xml" in completed2:
                        download_file(completed2["report_xml"], f"result_{article}.xlsm")
                    
                    # Переименовываем JSON в основной файл
                    if os.path.exists(json_file):
                        os.rename(json_file, f"result_{article}.json")
                    
                    # Возвращаем структурированные данные
                    return {
                        'found': True,
                        'method': 'marketid',
                        'product_info': info,
                        'order_info': completed2,
                        'json_data': json_data,
                    }
                else:
                    print(f"✗ Товар не найден по marketid")
                    print(f"  Ошибок: {info.get('errors', 0)}")
    
    print(f"\n{'='*60}")
    print("✗ Товар не найден ни одним из способов")
    print(f"{'='*60}")
    print("Возможные причины:")
    print("  1. Артикул указан неверно")
    print("  2. Товар отсутствует на Ozon в указанном регионе")
    print("  3. Товар снят с продажи")
    print("\nПроверьте файлы result_*_pid.json и result_*_mid.json для деталей")
    
    return None


def main():
    """Основная функция с автоматическим поиском"""
    API_KEY = "DpJbJzzFtdfIoY8dOQipw18yqgQ="
    ARTICLE = "1066650955"
    REGION = "Москва"
    
    client = ParserMarketClient(API_KEY)
    
    # Проверяем баланс
    print("=" * 60)
    print("Проверка баланса...")
    balance = client.get_balance()
    if balance:
        print(f"Логин: {balance.get('your_login', 'N/A')}")
        print(f"Доступные проверки: {balance.get('checks_total', 0)}")
        print(f"Бесплатные: {balance.get('checks_free', 0)}")
        print(f"Оплаченные: {balance.get('checks_paid', 0)}")
    print("=" * 60)
    
    # Поиск товара по методу marketid (SKU ID Ozon)
    result = parse_article_marketid(
        client=client,
        article=ARTICLE,
        region=REGION,
        market="ozon",
        max_wait=600,
        check_interval=15
    )
    
    if result and result.get('found'):
        print("\n" + "=" * 60)
        print("✓ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 60)
        
        # Обрабатываем результаты
        product_info = result.get('product_info', {})
        method = result.get('method', 'unknown')
        
        print(f"\n📦 Информация о товаре:")
        print(f"   Метод поиска: {method}")
        if product_info.get('name'):
            print(f"   Название: {product_info['name']}")
        if product_info.get('brand'):
            print(f"   Бренд: {product_info['brand']}")
        if product_info.get('category'):
            print(f"   Категория: {product_info['category']}")
        if product_info.get('rating', 0) > 0:
            print(f"   Рейтинг: {product_info['rating']} ({product_info.get('rates', 0)} отзывов)")
        
        # Выводим все предложения
        all_offers = product_info.get('all_offers', [])
        if all_offers:
            print(f"\n💰 Найдено предложений: {len(all_offers)}")
            print(f"\n{'─'*60}")
            for i, offer in enumerate(all_offers, 1):
                print(f"\nПредложение #{i}:")
                if offer.get('name'):
                    print(f"  Название: {offer['name']}")
                print(f"  Цена: {offer.get('price', 0)} ₽")
                if offer.get('ozon_card_price', 0) > 0:
                    print(f"  Цена по карте Ozon: {offer.get('ozon_card_price', 0)} ₽")
                if offer.get('promo_price', 0) > 0:
                    print(f"  Промо цена: {offer.get('promo_price', 0)} ₽")
                if offer.get('old_price', 0) > 0:
                    discount = int((1 - offer['price'] / offer['old_price']) * 100)
                    print(f"  Старая цена: {offer['old_price']} ₽ (скидка {discount}%)")
                print(f"  Магазин: {offer.get('shop_name', 'N/A')}")
                if offer.get('shop_rating', 0) > 0:
                    print(f"  Рейтинг магазина: {offer['shop_rating']}")
                if offer.get('stock_count', 0) > 0:
                    print(f"  Остаток: {offer['stock_count']} шт.")
                if offer.get('available'):
                    print(f"  В наличии: ✓")
                if offer.get('delivery_term'):
                    print(f"  Доставка: {offer['delivery_term']}")
                if offer.get('delivery_cost', 0) > 0:
                    print(f"  Стоимость доставки: {offer['delivery_cost']} ₽")
                if offer.get('rating', 0) > 0:
                    print(f"  Рейтинг товара: {offer['rating']} ({offer.get('reviews_count', 0)} отзывов)")
                if offer.get('sku_id'):
                    print(f"  SKU ID: {offer['sku_id']}")
        
        print(f"\n{'─'*60}")
        print(f"\n💾 Результаты сохранены в файлы:")
        print(f"   - result_{ARTICLE}.json")
        print(f"   - result_{ARTICLE}.csv")
        print(f"   - result_{ARTICLE}.xlsm (если доступен)")
        
        # Возвращаем данные для дальнейшей обработки
        return result
    else:
        print("\n" + "=" * 60)
        print("✗ Не удалось найти товар")
        print("=" * 60)
        return None


if __name__ == "__main__":
    main()

