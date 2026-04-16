# src/services/order_service.py
"""
Сервисный слой для работы с заказами
Содержит бизнес-логику, кэширование и валидацию
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from repositories.order_repo import OrderRepository
from services.client_service import ClientService
from models.order import (
    Order, OrderItem, OrderStatus, PaymentMethod,
    OrderSearchResult, OrderStatistics
)


class OrderService:
    """
    Сервис для работы с заказами
    
    Отвечает за:
    - Бизнес-логику (статусы, расчёт сумм)
    - Кэширование данных
    - Валидацию данных перед сохранением
    - Синхронизацию с клиентами
    """
    
    def __init__(self):
        self.repo = OrderRepository()
        self.client_service = ClientService()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 60  # 1 минута для заказов (часто меняются)
        self.default_page_size = 50
    
    # ============ КЭШИРОВАНИЕ ============
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Генерирует ключ для кэша"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверяет, валиден ли кэш"""
        if cache_key not in self._cache:
            return False
        
        cache_data = self._cache[cache_key]
        cache_time = cache_data.get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Получает данные из кэша"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        return None
    
    def _set_to_cache(self, cache_key: str, data: Any):
        """Сохраняет данные в кэш"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def invalidate_cache(self, prefix: str = None):
        """Сбрасывает кэш"""
        if prefix:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()
    
    # ============ ПРЕОБРАЗОВАНИЕ ДАННЫХ ============
    
    def _dict_to_order(self, data: Dict[str, Any]) -> Order:
        """
        Преобразует словарь из БД в модель Order
        """
        items_data = data.get('items', [])
        items = []
        for item in items_data:
            items.append(OrderItem(
                service_id=item.get('service_id', 0),
                service_name=item.get('service_name', ''),
                quantity=item.get('quantity', 1),
                base_price=item.get('base_price', 0.0) or 0.0,
                final_price=item.get('final_price', 0.0) or 0.0
            ))
        
        return Order.from_db_row(data, items)
    
    def _dict_list_to_orders(self, data_list: List[Dict[str, Any]]) -> List[Order]:
        """Преобразует список словарей в список Order"""
        orders = []
        for data in data_list:
            # Для списка может не быть полных items
            items_data = data.get('items', [])
            items = []
            for item in items_data:
                items.append(OrderItem(
                    service_id=item.get('service_id', 0),
                    service_name=item.get('service_name', ''),
                    quantity=item.get('quantity', 1),
                    base_price=item.get('base_price', 0.0) or 0.0,
                    final_price=item.get('final_price', 0.0) or 0.0
                ))
            orders.append(Order.from_db_row(data, items))
        return orders
    
    # ============ ОСНОВНЫЕ МЕТОДЫ ============
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """
        Получает заказ по ID
        
        Args:
            order_id: ID заказа
            
        Returns:
            Объект Order или None
        """
        cache_key = self._get_cache_key('order', order_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        data = self.repo.get_by_id(order_id)
        if not data:
            return None
        
        order = self._dict_to_order(data)
        self._set_to_cache(cache_key, order)
        return order
    
    def get_orders_by_status(self, status: OrderStatus, limit: int = 100) -> List[Order]:
        """
        Получает заказы по статусу
        
        Args:
            status: Статус заказа
            limit: Максимальное количество
            
        Returns:
            Список заказов
        """
        cache_key = self._get_cache_key('orders_status', status.value, limit)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        data = self.repo.get_orders_by_status(status.value, limit)
        orders = self._dict_list_to_orders(data)
        self._set_to_cache(cache_key, orders)
        return orders
    
    def get_today_orders(self) -> List[Order]:
        """Получает заказы за сегодня"""
        cache_key = self._get_cache_key('orders_today', date.today().isoformat())
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        data = self.repo.get_today_orders()
        orders = self._dict_list_to_orders(data)
        self._set_to_cache(cache_key, orders)
        return orders
    
    def search_orders(
        self,
        query: str = "",
        status: Optional[OrderStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = None
    ) -> OrderSearchResult:
        """
        Поиск заказов с пагинацией
        
        Args:
            query: Поисковый запрос
            status: Фильтр по статусу
            date_from: Дата начала
            date_to: Дата конца
            page: Номер страницы
            page_size: Размер страницы
            
        Returns:
            OrderSearchResult с заказами и пагинацией
        """
        if page_size is None:
            page_size = self.default_page_size
        
        # Конвертируем даты
        date_from_str = date_from.isoformat() if date_from else None
        date_to_str = date_to.isoformat() if date_to else None
        status_str = status.value if status else None
        
        # Выполняем поиск
        result = self.repo.search(
            query=query,
            status=status_str,
            date_from=date_from_str,
            date_to=date_to_str,
            page=page,
            page_size=page_size
        )
        
        # Преобразуем в модели
        orders = self._dict_list_to_orders(result['items'])
        
        return OrderSearchResult(
            orders=orders,
            total_count=result['total'],
            page=page,
            page_size=page_size
        )
    
    # ============ СОЗДАНИЕ И ОБНОВЛЕНИЕ ============
    
    def create_order(
        self,
        car_number: str,
        items: List[Dict[str, Any]],
        car_model: Optional[str] = None,
        client_phone: Optional[str] = None,
        car_class_id: Optional[int] = None,
        payment_method: PaymentMethod = PaymentMethod.CASH,
        comment: Optional[str] = None
    ) -> Optional[Order]:
        """
        Создаёт новый заказ
        
        Args:
            car_number: Госномер (обязательно)
            items: Список услуг [{'service_id': 1, 'quantity': 1, 'final_price': 500}, ...]
            car_model: Марка/модель
            client_phone: Телефон клиента
            car_class_id: ID класса авто
            payment_method: Способ оплаты
            comment: Комментарий
            
        Returns:
            Созданный заказ или None
        """
        # Валидация
        car_number = car_number.strip().upper()
        if not car_number:
            print("❌ Ошибка: госномер не может быть пустым")
            return None
        
        if not items:
            print("❌ Ошибка: заказ должен содержать хотя бы одну услугу")
            return None
        
        # Находим или создаём клиента
        client_id = None
        if car_number:
            client = self.client_service.find_or_create_from_order(
                car_number=car_number,
                car_model=car_model,
                phone=client_phone
            )
            if client:
                client_id = client.id
        
        # Считаем общую сумму
        total_price = sum(
            item.get('final_price', 0) * item.get('quantity', 1)
            for item in items
        )
        
        # Подготавливаем данные заказа
        order_data = {
            'car_number': car_number,
            'car_model': car_model,
            'client_phone': client_phone,
            'client_id': client_id,
            'car_class_id': car_class_id,
            'payment_method': payment_method.value,
            'comment': comment,
            'total_price': total_price
        }
        
        # Создаём заказ
        order_id = self.repo.create(order_data, items)
        if not order_id:
            return None
        
        # Сбрасываем кэш
        self.invalidate_cache('orders')
        self.invalidate_cache('stats')
        self.client_service.invalidate_cache('search')
        
        # Получаем созданный заказ
        return self.get_order(order_id)
    
    def update_order(
        self,
        order_id: int,
        car_number: Optional[str] = None,
        car_model: Optional[str] = None,
        client_phone: Optional[str] = None,
        car_class_id: Optional[int] = None,
        payment_method: Optional[PaymentMethod] = None,
        comment: Optional[str] = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Обновляет заказ
        
        Args:
            order_id: ID заказа
            car_number: Новый госномер
            car_model: Новая марка
            client_phone: Новый телефон
            car_class_id: Новый класс авто
            payment_method: Новый способ оплаты
            comment: Новый комментарий
            items: Новый список услуг
            
        Returns:
            True если успешно
        """
        update_data = {}
        
        if car_number is not None:
            update_data['car_number'] = car_number.strip().upper()
        if car_model is not None:
            update_data['car_model'] = car_model.strip() if car_model else None
        if client_phone is not None:
            update_data['client_phone'] = client_phone.strip() if client_phone else None
        if car_class_id is not None:
            update_data['car_class_id'] = car_class_id
        if payment_method is not None:
            update_data['payment_method'] = payment_method.value
        if comment is not None:
            update_data['comment'] = comment.strip() if comment else None
        
        # Обновляем основные данные
        if update_data:
            success = self.repo.update(order_id, update_data)
            if not success:
                return False
        
        # Обновляем услуги
        if items is not None:
            success = self.repo.update_order_items(order_id, items)
            if not success:
                return False
            
            # Пересчитываем total_price
            total_price = sum(
                item.get('final_price', 0) * item.get('quantity', 1)
                for item in items
            )
            self.repo.update(order_id, {'total_price': total_price})
        
        # Сбрасываем кэш
        self.invalidate_cache(f'order:{order_id}')
        self.invalidate_cache('orders')
        self.invalidate_cache('stats')
        
        return True
    
    def delete_order(self, order_id: int) -> bool:
        """
        Удаляет заказ
        
        Args:
            order_id: ID заказа
            
        Returns:
            True если успешно
        """
        success = self.repo.delete(order_id)
        
        if success:
            self.invalidate_cache(f'order:{order_id}')
            self.invalidate_cache('orders')
            self.invalidate_cache('stats')
        
        return success
    
    # ============ УПРАВЛЕНИЕ СТАТУСАМИ ============
    
    def change_status(self, order_id: int, new_status: OrderStatus) -> bool:
        """
        Меняет статус заказа
        
        Args:
            order_id: ID заказа
            new_status: Новый статус
            
        Returns:
            True если успешно
        """
        success = self.repo.update_status(order_id, new_status.value)
        
        if success:
            self.invalidate_cache(f'order:{order_id}')
            self.invalidate_cache('orders_status')
            self.invalidate_cache('orders_today')
        
        return success
    
    def toggle_status(self, order_id: int) -> Optional[OrderStatus]:
        """
        Переключает статус заказа на следующий
        
        Args:
            order_id: ID заказа
            
        Returns:
            Новый статус или None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        next_status = order.status.next_status
        if next_status:
            success = self.change_status(order_id, next_status)
            return next_status if success else None
        
        return None
    
    # ============ СТАТИСТИКА ============
    
    def get_statistics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> OrderStatistics:
        """
        Получает статистику по заказам
        
        Args:
            date_from: Дата начала
            date_to: Дата конца
            
        Returns:
            OrderStatistics с данными
        """
        cache_key = self._get_cache_key('stats', date_from, date_to)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        date_from_str = date_from.isoformat() if date_from else None
        date_to_str = date_to.isoformat() if date_to else None
        
        data = self.repo.get_statistics(date_from_str, date_to_str)
        
        stats = OrderStatistics(
            total_orders=data.get('total_orders', 0) or 0,
            total_revenue=data.get('total_revenue', 0.0) or 0.0,
            avg_check=data.get('avg_check', 0.0) or 0.0,
            queue_count=data.get('queue_count', 0) or 0,
            process_count=data.get('process_count', 0) or 0,
            done_count=data.get('done_count', 0) or 0,
            cancelled_count=data.get('cancelled_count', 0) or 0,
            cash_count=data.get('cash_count', 0) or 0,
            cash_amount=data.get('cash_amount', 0.0) or 0.0,
            card_count=data.get('card_count', 0) or 0,
            card_amount=data.get('card_amount', 0.0) or 0.0,
            transfer_count=data.get('transfer_count', 0) or 0,
            transfer_amount=data.get('transfer_amount', 0.0) or 0.0,
            sbp_count=data.get('sbp_count', 0) or 0,
            sbp_amount=data.get('sbp_amount', 0.0) or 0.0
        )
        
        self._set_to_cache(cache_key, stats)
        return stats
    
    def get_today_statistics(self) -> OrderStatistics:
        """Получает статистику за сегодня"""
        today = date.today()
        return self.get_statistics(today, today)
    
    def get_daily_revenue(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получает выручку по дням
        
        Args:
            days: Количество дней
            
        Returns:
            Список с выручкой по дням
        """
        return self.repo.get_daily_revenue(days)
    
    # ============ БЫСТРЫЕ ДЕЙСТВИЯ ============
    
    def get_orders_grouped_by_status(self) -> Dict[str, List[Order]]:
        """
        Возвращает заказы, сгруппированные по статусам
        
        Returns:
            Словарь {статус: список заказов}
        """
        result = {
            'queue': [],
            'process': [],
            'done': []
        }
        
        # Получаем заказы для каждого статуса
        for status in [OrderStatus.QUEUE, OrderStatus.PROCESS, OrderStatus.DONE]:
            orders = self.get_orders_by_status(status, limit=100)
            result[status.value] = orders
        
        return result
    
    def get_queue_position(self, order_id: int) -> Optional[int]:
        """
        Определяет позицию заказа в очереди
        
        Args:
            order_id: ID заказа
            
        Returns:
            Позиция в очереди (1-based) или None
        """
        order = self.get_order(order_id)
        if not order or order.status != OrderStatus.QUEUE:
            return None
        
        queue_orders = self.get_orders_by_status(OrderStatus.QUEUE)
        for i, o in enumerate(queue_orders):
            if o.id == order_id:
                return i + 1
        
        return None