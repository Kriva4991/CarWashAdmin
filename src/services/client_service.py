# src/services/client_service.py
"""
Сервисный слой для работы с клиентами
Содержит бизнес-логику, кэширование и валидацию
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from repositories.client_repo import ClientRepository
from models.client import Client, ClientOrderHistory, ClientSearchResult


class ClientService:
    """
    Сервис для работы с клиентами
    
    Отвечает за:
    - Бизнес-логику (определение уровня лояльности, форматирование)
    - Кэширование данных (уменьшает нагрузку на БД)
    - Валидацию данных перед сохранением
    - Преобразование сырых данных в модели Client
    """
    
    def __init__(self):
        self.repo = ClientRepository()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # Время жизни кэша в секундах (5 минут)
        self.default_page_size = 50
    
    # ============ ПРЕОБРАЗОВАНИЕ ДАННЫХ ============
    
    def _dict_to_client(self, data: Dict[str, Any]) -> Client:
        """
        Преобразует словарь из БД в модель Client
        
        Args:
            data: Словарь с данными из репозитория
            
        Returns:
            Объект Client
        """
        # Преобразуем строковые даты в datetime
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = None
        
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except ValueError:
                updated_at = None
        
        last_visit = data.get('last_visit')
        if last_visit and isinstance(last_visit, str):
            try:
                last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00'))
            except ValueError:
                last_visit = None
        
        return Client(
            id=data['id'],
            car_number=data.get('car_number', ''),
            car_model=data.get('car_model'),
            phone=data.get('phone'),
            comment=data.get('comment'),
            created_at=created_at,
            updated_at=updated_at,
            total_visits=data.get('total_visits', 0) or 0,
            total_spent=data.get('total_spent', 0.0) or 0.0,
            last_visit=last_visit
        )
    
    def _dict_to_order_history(self, data: Dict[str, Any]) -> ClientOrderHistory:
        """
        Преобразует словарь в модель истории заказа
        """
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        
        services_str = data.get('services', '')
        services = [s.strip() for s in services_str.split(',') if s.strip()] if services_str else []
        
        return ClientOrderHistory(
            order_id=data['id'],
            created_at=created_at or datetime.now(),
            car_number=data.get('car_number', ''),
            total_price=data.get('total_price', 0.0) or 0.0,
            status=data.get('status', 'queue'),
            services=services,
            payment_method=data.get('payment_method')
        )
    
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
        """Получает данные из кэша если они валидны"""
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
        """
        Сбрасывает кэш
        
        Args:
            prefix: Если указан, сбрасывает только ключи с этим префиксом
        """
        if prefix:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()
    
    # ============ ОСНОВНЫЕ МЕТОДЫ ============
    
    def get_client(self, client_id: int, use_cache: bool = True) -> Optional[Client]:
        """
        Получает клиента по ID
        
        Args:
            client_id: ID клиента
            use_cache: Использовать ли кэш
            
        Returns:
            Объект Client или None
        """
        cache_key = self._get_cache_key('client', client_id)
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        data = self.repo.get_by_id(client_id)
        if not data:
            return None
        
        client = self._dict_to_client(data)
        
        if use_cache:
            self._set_to_cache(cache_key, client)
        
        return client
    
    def search_clients(
        self,
        query: str = "",
        page: int = 1,
        page_size: int = None
    ) -> ClientSearchResult:
        """
        Поиск клиентов с пагинацией
        
        Args:
            query: Поисковый запрос
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы (по умолчанию default_page_size)
            
        Returns:
            ClientSearchResult с клиентами и информацией о пагинации
        """
        if page_size is None:
            page_size = self.default_page_size
        
        cache_key = self._get_cache_key('search', query, page, page_size)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Выполняем поиск
        result = self.repo.search(query, page, page_size)
        
        # Преобразуем в модели
        clients = [self._dict_to_client(item) for item in result['items']]
        
        search_result = ClientSearchResult(
            clients=clients,
            total_count=result['total'],
            page=page,
            page_size=page_size
        )
        
        self._set_to_cache(cache_key, search_result)
        return search_result
    
    def search_clients_simple(self, query: str = "") -> List[Client]:
        """
        Простой поиск без пагинации (для совместимости со старым кодом)
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список клиентов
        """
        data = self.repo.search_simple(query)
        return [self._dict_to_client(item) for item in data]
    
    def get_client_history(self, client_id: int) -> List[ClientOrderHistory]:
        """
        Получает историю заказов клиента
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список заказов клиента
        """
        cache_key = self._get_cache_key('history', client_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        orders_data = self.repo.get_client_orders(client_id)
        history = [self._dict_to_order_history(order) for order in orders_data]
        
        self._set_to_cache(cache_key, history)
        return history
    
    # ============ ОПЕРАЦИИ С КЛИЕНТАМИ ============
    
    def create_client(
        self,
        car_number: str,
        car_model: Optional[str] = None,
        phone: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Optional[Client]:
        """
        Создаёт нового клиента
        
        Args:
            car_number: Госномер (обязательно)
            car_model: Марка/модель
            phone: Телефон
            comment: Комментарий
            
        Returns:
            Созданный клиент или None при ошибке
        """
        # Валидация
        car_number = car_number.strip().upper()
        if not car_number:
            print("❌ Ошибка: госномер не может быть пустым")
            return None
        
        # Проверяем, нет ли уже такого клиента
        existing = self.repo.get_by_car_number(car_number)
        if existing:
            print(f"⚠️ Клиент с номером {car_number} уже существует (ID: {existing['id']})")
            return self._dict_to_client(existing)
        
        # Создаём
        client_data = {
            'car_number': car_number,
            'car_model': car_model.strip() if car_model else None,
            'phone': phone.strip() if phone else None,
            'comment': comment.strip() if comment else None
        }
        
        client_id = self.repo.create(client_data)
        if not client_id:
            return None
        
        # Сбрасываем кэш поиска
        self.invalidate_cache('search')
        
        # Получаем созданного клиента
        return self.get_client(client_id, use_cache=False)
    
    def update_client(
        self,
        client_id: int,
        car_number: Optional[str] = None,
        car_model: Optional[str] = None,
        phone: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Обновляет данные клиента
        
        Returns:
            True если успешно
        """
        update_data = {}
        
        if car_number is not None:
            update_data['car_number'] = car_number.strip().upper()
        if car_model is not None:
            update_data['car_model'] = car_model.strip() if car_model else None
        if phone is not None:
            update_data['phone'] = phone.strip() if phone else None
        if comment is not None:
            update_data['comment'] = comment.strip() if comment else None
        
        if not update_data:
            return False
        
        success = self.repo.update(client_id, update_data)
        
        if success:
            # Сбрасываем кэш
            self.invalidate_cache(f'client:{client_id}')
            self.invalidate_cache('search')
        
        return success
    
    def update_comment(self, client_id: int, comment: str) -> bool:
        """
        Обновляет комментарий клиента
        
        Args:
            client_id: ID клиента
            comment: Новый комментарий
            
        Returns:
            True если успешно
        """
        success = self.repo.update_comment(client_id, comment.strip())
        
        if success:
            self.invalidate_cache(f'client:{client_id}')
            self.invalidate_cache('search')
        
        return success
    
    def delete_client(self, client_id: int) -> bool:
        """
        Удаляет клиента
        
        Args:
            client_id: ID клиента
            
        Returns:
            True если успешно
        """
        success = self.repo.delete(client_id)
        
        if success:
            self.invalidate_cache(f'client:{client_id}')
            self.invalidate_cache('search')
        
        return success
    
    # ============ ИНТЕГРАЦИЯ С ЗАКАЗАМИ ============
    
    def find_or_create_from_order(
        self,
        car_number: str,
        car_model: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[Client]:
        """
        Находит или создаёт клиента из данных заказа
        
        Args:
            car_number: Госномер
            car_model: Марка/модель
            phone: Телефон
            
        Returns:
            Клиент или None
        """
        if not car_number:
            return None
        
        car_number = car_number.strip().upper()
        
        # Пробуем найти существующего
        existing = self.repo.get_by_car_number(car_number)
        if existing:
            # Обновляем данные если нужно
            update_data = {}
            if car_model and car_model != existing.get('car_model'):
                update_data['car_model'] = car_model
            if phone and phone != existing.get('phone'):
                update_data['phone'] = phone
            
            if update_data:
                self.repo.update(existing['id'], update_data)
                self.invalidate_cache(f"client:{existing['id']}")
                self.invalidate_cache('search')
            
            return self._dict_to_client(existing)
        
        # Создаём нового
        return self.create_client(car_number, car_model, phone)
    
    def sync_clients_from_orders(self) -> int:
        """
        Синхронизирует клиентов из таблицы заказов
        
        Returns:
            Количество созданных клиентов
        """
        count = self.repo.sync_from_orders()
        if count > 0:
            self.invalidate_cache('search')
        return count
    
    # ============ СТАТИСТИКА ============
    
    def get_client_stats(self, client_id: int) -> Dict[str, Any]:
        """
        Получает подробную статистику по клиенту
        
        Returns:
            Словарь со статистикой
        """
        stats = self.repo.get_client_stats(client_id)
        
        # Добавляем вычисляемые поля
        if stats.get('avg_check'):
            stats['avg_check_formatted'] = f"{stats['avg_check']:.0f} ₽"
        if stats.get('total_spent'):
            stats['total_spent_formatted'] = f"{stats['total_spent']:.0f} ₽"
        
        # Определяем уровень лояльности
        total_orders = stats.get('total_orders', 0)
        if total_orders >= 10:
            stats['loyalty_level'] = 'VIP'
            stats['loyalty_color'] = '#27ae60'
        elif total_orders >= 3:
            stats['loyalty_level'] = 'Постоянный'
            stats['loyalty_color'] = '#f39c12'
        else:
            stats['loyalty_level'] = 'Новый'
            stats['loyalty_color'] = '#3498db'
        
        return stats
    
    def get_total_count(self, query: str = "") -> int:
        """Общее количество клиентов"""
        return self.repo.get_total_count(query)
    
    def get_top_clients(self, limit: int = 10) -> List[Client]:
        """Топ клиентов по потраченной сумме"""
        data = self.repo.get_top_clients(limit)
        return [self._dict_to_client(item) for item in data]
    
    def get_recent_clients(self, limit: int = 20) -> List[Client]:
        """Последние клиенты"""
        data = self.repo.get_recent_clients(limit)
        return [self._dict_to_client(item) for item in data]