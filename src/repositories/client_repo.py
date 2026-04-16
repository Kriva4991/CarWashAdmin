# src/repositories/client_repo.py
"""
Репозиторий для работы с клиентами
Содержит только SQL-запросы, без бизнес-логики
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseRepository


class ClientRepository(BaseRepository):
    """Репозиторий для работы с таблицей clients"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "clients"
    
    # ============ БАЗОВЫЕ CRUD ОПЕРАЦИИ ============
    
    def get_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает клиента по ID
        
        Args:
            client_id: ID клиента
            
        Returns:
            Словарь с данными клиента или None
        """
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.comment,
                c.created_at,
                c.updated_at,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                MAX(o.created_at) as last_visit
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            WHERE c.id = ?
            GROUP BY c.id
        """
        return self.fetch_one(query, (client_id,))
    
    def get_by_car_number(self, car_number: str) -> Optional[Dict[str, Any]]:
        """
        Получает клиента по госномеру
        
        Args:
            car_number: Госномер автомобиля
            
        Returns:
            Словарь с данными клиента или None
        """
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.comment,
                c.created_at,
                c.updated_at,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                MAX(o.created_at) as last_visit
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            WHERE c.car_number = ?
            GROUP BY c.id
        """
        return self.fetch_one(query, (car_number,))
    
    def create(self, client_data: Dict[str, Any]) -> Optional[int]:
        """
        Создаёт нового клиента
        
        Args:
            client_data: Словарь с данными клиента
                - car_number: str (обязательно)
                - car_model: str (опционально)
                - phone: str (опционально)
                - comment: str (опционально)
                
        Returns:
            ID созданного клиента или None при ошибке
        """
        query = """
            INSERT INTO clients (car_number, car_model, phone, comment)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_and_get_id(query, (
            client_data.get('car_number', ''),
            client_data.get('car_model'),
            client_data.get('phone'),
            client_data.get('comment')
        ))
    
    def update(self, client_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные клиента
        
        Args:
            client_id: ID клиента
            update_data: Словарь с обновляемыми полями
                - car_number: str
                - car_model: str
                - phone: str
                - comment: str
                
        Returns:
            True если успешно, False если ошибка
        """
        # Строим динамический UPDATE запрос
        fields = []
        params = []
        
        allowed_fields = ['car_number', 'car_model', 'phone', 'comment']
        for field in allowed_fields:
            if field in update_data:
                fields.append(f"{field} = ?")
                params.append(update_data[field])
        
        if not fields:
            return False
        
        # Добавляем updated_at
        fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Добавляем ID в параметры
        params.append(client_id)
        
        query = f"""
            UPDATE clients 
            SET {', '.join(fields)}
            WHERE id = ?
        """
        
        return self.execute(query, tuple(params))
    
    def update_comment(self, client_id: int, comment: str) -> bool:
        """
        Обновляет только комментарий клиента
        
        Args:
            client_id: ID клиента
            comment: Новый комментарий
            
        Returns:
            True если успешно
        """
        query = """
            UPDATE clients 
            SET comment = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.execute(query, (comment, client_id))
    
    def delete(self, client_id: int) -> bool:
        """
        Удаляет клиента по ID
        
        ВНИМАНИЕ: Использует FOREIGN KEY, может быть ограничено
        если есть связанные заказы (зависит от настроек БД)
        
        Args:
            client_id: ID клиента
            
        Returns:
            True если успешно
        """
        query = "DELETE FROM clients WHERE id = ?"
        return self.execute(query, (client_id,))
    
    # ============ ПОИСК И ФИЛЬТРАЦИЯ ============
    
    def search(
        self,
        query: str = "",
        page: int = 1,
        page_size: int = 50,
        order_by: str = "total_spent DESC"
    ) -> Dict[str, Any]:
        """
        Поиск клиентов с пагинацией
        
        Args:
            query: Поисковый запрос (ищет по госномеру, телефону, марке)
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы
            order_by: Сортировка
            
        Returns:
            Словарь с результатами поиска и пагинацией
        """
        # Базовый запрос
        base_query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.comment,
                c.created_at,
                c.updated_at,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                MAX(o.created_at) as last_visit
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
        """
        
        params = ()
        
        # Добавляем поиск если есть запрос
        if query:
            search_term = f"%{query}%"
            base_query += """
                WHERE c.car_number LIKE ? 
                   OR c.phone LIKE ? 
                   OR c.car_model LIKE ?
            """
            params = (search_term, search_term, search_term)
        
        # Группировка
        base_query += " GROUP BY c.id"
        
        # Сортировка
        base_query += f" ORDER BY {order_by}"
        
        # Используем метод paginate из базового класса
        return self.paginate(base_query, params, page, page_size)
    
    def search_simple(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Простой поиск без пагинации (для совместимости со старым кодом)
        
        Args:
            search_term: Поисковый запрос
            
        Returns:
            Список клиентов
        """
        if not search_term:
            query = """
                SELECT 
                    c.id,
                    c.car_number,
                    c.car_model,
                    c.phone,
                    c.comment,
                    COUNT(o.id) as total_visits,
                    COALESCE(SUM(o.total_price), 0) as total_spent,
                    MAX(o.created_at) as last_visit
                FROM clients c
                LEFT JOIN orders o ON c.id = o.client_id
                GROUP BY c.id
                ORDER BY total_spent DESC
            """
            return self.fetch_all(query)
        
        term = f"%{search_term}%"
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.comment,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                MAX(o.created_at) as last_visit
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            WHERE c.car_number LIKE ? 
               OR c.phone LIKE ? 
               OR c.car_model LIKE ?
            GROUP BY c.id
            ORDER BY total_spent DESC
        """
        return self.fetch_all(query, (term, term, term))
    
    def get_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        """
        Находит клиентов по телефону (может быть несколько)
        
        Args:
            phone: Номер телефона
            
        Returns:
            Список клиентов с таким телефоном
        """
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.comment,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            WHERE c.phone = ?
            GROUP BY c.id
            ORDER BY total_visits DESC
        """
        return self.fetch_all(query, (phone,))
    
    # ============ СТАТИСТИКА ============
    
    def get_total_count(self, search_term: str = "") -> int:
        """
        Общее количество клиентов
        
        Args:
            search_term: Поисковый запрос (опционально)
            
        Returns:
            Количество клиентов
        """
        if not search_term:
            return self.count()
        
        term = f"%{search_term}%"
        where_clause = "car_number LIKE ? OR phone LIKE ? OR car_model LIKE ?"
        return self.count(where_clause, (term, term, term))
    
    def get_top_clients(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Топ клиентов по сумме потраченных средств
        
        Args:
            limit: Количество клиентов
            
        Returns:
            Список клиентов отсортированных по total_spent
        """
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                MAX(o.created_at) as last_visit
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            GROUP BY c.id
            ORDER BY total_spent DESC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))
    
    def get_recent_clients(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Последние клиенты (по дате создания)
        
        Args:
            limit: Количество клиентов
            
        Returns:
            Список последних клиентов
        """
        query = """
            SELECT 
                c.id,
                c.car_number,
                c.car_model,
                c.phone,
                c.created_at,
                COUNT(o.id) as total_visits,
                COALESCE(SUM(o.total_price), 0) as total_spent
            FROM clients c
            LEFT JOIN orders o ON c.id = o.client_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))
    
    # ============ ИСТОРИЯ ЗАКАЗОВ ============
    
    def get_client_orders(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Получает историю заказов клиента
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список заказов клиента с услугами
        """
        query = """
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.total_price,
                o.status,
                o.payment_method,
                GROUP_CONCAT(s.name, ', ') as services
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            WHERE o.client_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        return self.fetch_all(query, (client_id,))
    
    def get_client_stats(self, client_id: int) -> Dict[str, Any]:
        """
        Статистика по клиенту
        
        Args:
            client_id: ID клиента
            
        Returns:
            Словарь со статистикой
        """
        query = """
            SELECT 
                COUNT(DISTINCT o.id) as total_orders,
                COALESCE(SUM(o.total_price), 0) as total_spent,
                AVG(o.total_price) as avg_check,
                MIN(o.created_at) as first_visit,
                MAX(o.created_at) as last_visit,
                COUNT(DISTINCT DATE(o.created_at)) as visit_days
            FROM orders o
            WHERE o.client_id = ?
        """
        return self.fetch_one(query, (client_id,)) or {}
    
    # ============ СИНХРОНИЗАЦИЯ С ЗАКАЗАМИ ============
    
    def find_or_create_by_car_number(
        self,
        car_number: str,
        car_model: Optional[str] = None,
        phone: Optional[str] = None
    ) -> int:
        """
        Находит клиента по госномеру или создаёт нового
        
        Args:
            car_number: Госномер автомобиля
            car_model: Марка/модель (опционально)
            phone: Телефон (опционально)
            
        Returns:
            ID клиента
        """
        # Ищем существующего
        existing = self.get_by_car_number(car_number)
        
        if existing:
            client_id = existing['id']
            
            # Обновляем данные если они изменились
            update_data = {}
            if car_model and car_model != existing.get('car_model'):
                update_data['car_model'] = car_model
            if phone and phone != existing.get('phone'):
                update_data['phone'] = phone
            
            if update_data:
                self.update(client_id, update_data)
            
            return client_id
        
        # Создаём нового
        return self.create({
            'car_number': car_number,
            'car_model': car_model,
            'phone': phone
        })
    
    def sync_from_orders(self) -> int:
        """
        Синхронизирует клиентов из таблицы orders
        Создаёт клиентов для госномеров, которых ещё нет в clients
        
        Returns:
            Количество созданных клиентов
        """
        query = """
            INSERT OR IGNORE INTO clients (car_number, car_model, phone)
            SELECT DISTINCT 
                o.car_number,
                MAX(o.car_model) as car_model,
                MAX(o.client_phone) as phone
            FROM orders o
            WHERE o.car_number IS NOT NULL 
              AND o.car_number != ''
              AND o.car_number NOT IN (SELECT car_number FROM clients)
            GROUP BY o.car_number
        """
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            created_count = cursor.rowcount
            conn.commit()
            return created_count
        except Exception as e:
            print(f"❌ Ошибка синхронизации клиентов: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()