# src/repositories/order_repo.py
"""
Репозиторий для работы с заказами
Содержит SQL-запросы к таблицам orders и order_items
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from .base import BaseRepository


class OrderRepository(BaseRepository):
    """Репозиторий для работы с заказами"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "orders"
    
    # ============ БАЗОВЫЕ CRUD ОПЕРАЦИИ ============
    
    def get_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает заказ по ID вместе с услугами
        
        Args:
            order_id: ID заказа
            
        Returns:
            Словарь с данными заказа и списком услуг
        """
        # Получаем основные данные заказа
        query = """
            SELECT 
                o.id,
                o.created_at,
                o.updated_at,
                o.car_number,
                o.car_model,
                o.client_phone,
                o.client_id,
                o.car_class_id,
                cc.name as car_class_name,
                cc.coefficient as car_class_coefficient,
                o.status,
                o.total_price,
                o.payment_method,
                o.comment,
                o.shift_id
            FROM orders o
            LEFT JOIN car_classes cc ON o.car_class_id = cc.id
            WHERE o.id = ?
        """
        order = self.fetch_one(query, (order_id,))
        
        if not order:
            return None
        
        # Получаем услуги заказа
        items_query = """
            SELECT 
                oi.id,
                oi.service_id,
                s.name as service_name,
                oi.quantity,
                oi.base_price,
                oi.final_price
            FROM order_items oi
            JOIN services s ON oi.service_id = s.id
            WHERE oi.order_id = ?
        """
        items = self.fetch_all(items_query, (order_id,))
        order['items'] = items
        
        return order
    
    def get_orders_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает заказы по статусу
        
        Args:
            status: Статус заказа (queue, process, done, cancelled)
            limit: Максимальное количество
            
        Returns:
            Список заказов с услугами
        """
        query = """
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.car_model,
                o.client_phone,
                o.status,
                o.total_price,
                o.payment_method,
                GROUP_CONCAT(s.name, ', ') as services_list
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            WHERE o.status = ?
            GROUP BY o.id
            ORDER BY o.created_at ASC
            LIMIT ?
        """
        return self.fetch_all(query, (status, limit))
    
    def create(self, order_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[int]:
        """
        Создаёт новый заказ с услугами
        
        Args:
            order_data: Данные заказа
                - car_number: str
                - car_model: str (опционально)
                - client_phone: str (опционально)
                - client_id: int (опционально)
                - car_class_id: int (опционально)
                - payment_method: str
                - comment: str (опционально)
                - shift_id: int (опционально)
                - total_price: float
            items: Список услуг
                - service_id: int
                - quantity: int
                - base_price: float
                - final_price: float
                
        Returns:
            ID созданного заказа или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Создаём заказ
            order_query = """
                INSERT INTO orders (
                    car_number, car_model, client_phone, client_id,
                    car_class_id, status, total_price, payment_method,
                    comment, shift_id
                ) VALUES (?, ?, ?, ?, ?, 'queue', ?, ?, ?, ?)
            """
            cursor.execute(order_query, (
                order_data.get('car_number', ''),
                order_data.get('car_model'),
                order_data.get('client_phone'),
                order_data.get('client_id'),
                order_data.get('car_class_id'),
                order_data.get('total_price', 0),
                order_data.get('payment_method', 'cash'),
                order_data.get('comment'),
                order_data.get('shift_id')
            ))
            
            order_id = cursor.lastrowid
            
            # Добавляем услуги
            if items:
                items_query = """
                    INSERT INTO order_items (
                        order_id, service_id, quantity, base_price, final_price
                    ) VALUES (?, ?, ?, ?, ?)
                """
                for item in items:
                    cursor.execute(items_query, (
                        order_id,
                        item.get('service_id'),
                        item.get('quantity', 1),
                        item.get('base_price', 0),
                        item.get('final_price', 0)
                    ))
            
            conn.commit()
            return order_id
            
        except Exception as e:
            print(f"❌ Ошибка создания заказа: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update(self, order_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные заказа
        
        Args:
            order_id: ID заказа
            update_data: Словарь с обновляемыми полями
                - car_number, car_model, client_phone, car_class_id
                - total_price, payment_method, comment, status
                
        Returns:
            True если успешно
        """
        fields = []
        params = []
        
        allowed_fields = [
            'car_number', 'car_model', 'client_phone', 'car_class_id',
            'total_price', 'payment_method', 'comment', 'status'
        ]
        
        for field in allowed_fields:
            if field in update_data:
                fields.append(f"{field} = ?")
                params.append(update_data[field])
        
        if not fields:
            return False
        
        # Добавляем updated_at
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(order_id)
        
        query = f"""
            UPDATE orders 
            SET {', '.join(fields)}
            WHERE id = ?
        """
        
        return self.execute(query, tuple(params))
    
    def update_status(self, order_id: int, status: str) -> bool:
        """
        Обновляет только статус заказа
        
        Args:
            order_id: ID заказа
            status: Новый статус
            
        Returns:
            True если успешно
        """
        query = """
            UPDATE orders 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.execute(query, (status, order_id))
    
    def delete(self, order_id: int) -> bool:
        """
        Удаляет заказ (сначала удаляет order_items из-за FOREIGN KEY)
        
        Args:
            order_id: ID заказа
            
        Returns:
            True если успешно
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Сначала удаляем услуги
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            # Потом удаляем заказ
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления заказа: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============ ПОИСК И ФИЛЬТРАЦИЯ ============
    
    def search(
        self,
        query: str = "",
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at DESC"
    ) -> Dict[str, Any]:
        """
        Поиск заказов с пагинацией
        
        Args:
            query: Поисковый запрос (госномер, телефон, ID)
            status: Фильтр по статусу
            date_from: Дата начала (YYYY-MM-DD)
            date_to: Дата конца (YYYY-MM-DD)
            page: Номер страницы
            page_size: Размер страницы
            order_by: Сортировка
            
        Returns:
            Словарь с результатами и пагинацией
        """
        # Базовый запрос
        base_query = """
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.car_model,
                o.client_phone,
                o.client_id,
                o.status,
                o.total_price,
                o.payment_method,
                o.comment,
                GROUP_CONCAT(s.name, ', ') as services_list
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
        """
        
        conditions = []
        params = []
        
        # Поиск по тексту
        if query:
            search_term = f"%{query}%"
            conditions.append("""
                (o.car_number LIKE ? OR o.client_phone LIKE ? OR CAST(o.id AS TEXT) LIKE ?)
            """)
            params.extend([search_term, search_term, search_term])
        
        # Фильтр по статусу
        if status:
            conditions.append("o.status = ?")
            params.append(status)
        
        # Фильтр по дате
        if date_from:
            conditions.append("DATE(o.created_at) >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("DATE(o.created_at) <= ?")
            params.append(date_to)
        
        # Добавляем WHERE если есть условия
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Группировка
        base_query += " GROUP BY o.id"
        
        # Сортировка
        base_query += f" ORDER BY o.{order_by}"
        
        # Пагинация
        return self.paginate(base_query, tuple(params), page, page_size)
    
    def get_today_orders(self) -> List[Dict[str, Any]]:
        """
        Получает заказы за сегодня
        
        Returns:
            Список заказов
        """
        today = date.today().isoformat()
        query = """
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.car_model,
                o.status,
                o.total_price,
                o.payment_method,
                GROUP_CONCAT(s.name, ', ') as services_list
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            WHERE DATE(o.created_at) = ?
            GROUP BY o.id
            ORDER BY o.created_at ASC
        """
        return self.fetch_all(query, (today,))
    
    def get_recent_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает последние заказы
        
        Args:
            limit: Количество заказов
            
        Returns:
            Список заказов
        """
        query = """
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.car_model,
                o.status,
                o.total_price,
                o.payment_method,
                GROUP_CONCAT(s.name, ', ') as services_list
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))
    
    # ============ СТАТИСТИКА ============
    
    def get_statistics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получает статистику по заказам за период
        
        Args:
            date_from: Дата начала
            date_to: Дата конца
            
        Returns:
            Словарь со статистикой
        """
        conditions = []
        params = []
        
        if date_from:
            conditions.append("DATE(created_at) >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("DATE(created_at) <= ?")
            params.append(date_to)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Основная статистика
        stats_query = f"""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_price), 0) as total_revenue,
                AVG(total_price) as avg_check,
                SUM(CASE WHEN status = 'queue' THEN 1 ELSE 0 END) as queue_count,
                SUM(CASE WHEN status = 'process' THEN 1 ELSE 0 END) as process_count,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count
            FROM orders
            {where_clause}
        """
        stats = self.fetch_one(stats_query, tuple(params))
        
        # Статистика по оплате
        payment_query = f"""
            SELECT 
                payment_method,
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as amount
            FROM orders
            {where_clause}
            GROUP BY payment_method
        """
        payment_stats = self.fetch_all(payment_query, tuple(params))
        
        # Добавляем статистику по оплате в результат
        if stats:
            for p in payment_stats:
                method = p.get('payment_method', '')
                if method == 'cash':
                    stats['cash_count'] = p['count']
                    stats['cash_amount'] = p['amount']
                elif method == 'card':
                    stats['card_count'] = p['count']
                    stats['card_amount'] = p['amount']
                elif method == 'transfer':
                    stats['transfer_count'] = p['count']
                    stats['transfer_amount'] = p['amount']
                elif method == 'sbp':
                    stats['sbp_count'] = p['count']
                    stats['sbp_amount'] = p['amount']
        
        return stats or {}
    
    def get_daily_revenue(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получает выручку по дням
        
        Args:
            days: Количество дней
            
        Returns:
            Список с выручкой по дням
        """
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as orders_count,
                COALESCE(SUM(total_price), 0) as revenue
            FROM orders
            WHERE DATE(created_at) >= DATE('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """
        return self.fetch_all(query, (days,))
    
    # ============ УСЛУГИ В ЗАКАЗЕ ============
    
    def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """
        Получает услуги заказа
        
        Args:
            order_id: ID заказа
            
        Returns:
            Список услуг
        """
        query = """
            SELECT 
                oi.id,
                oi.service_id,
                s.name as service_name,
                oi.quantity,
                oi.base_price,
                oi.final_price
            FROM order_items oi
            JOIN services s ON oi.service_id = s.id
            WHERE oi.order_id = ?
        """
        return self.fetch_all(query, (order_id,))
    
    def update_order_items(self, order_id: int, items: List[Dict[str, Any]]) -> bool:
        """
        Обновляет услуги заказа (удаляет старые и добавляет новые)
        
        Args:
            order_id: ID заказа
            items: Список услуг
            
        Returns:
            True если успешно
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Удаляем старые услуги
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            
            # Добавляем новые
            if items:
                items_query = """
                    INSERT INTO order_items (
                        order_id, service_id, quantity, base_price, final_price
                    ) VALUES (?, ?, ?, ?, ?)
                """
                for item in items:
                    cursor.execute(items_query, (
                        order_id,
                        item.get('service_id'),
                        item.get('quantity', 1),
                        item.get('base_price', 0),
                        item.get('final_price', 0)
                    ))
            
            # Обновляем total_price в заказе
            cursor.execute("""
                UPDATE orders 
                SET total_price = (
                    SELECT COALESCE(SUM(final_price * quantity), 0)
                    FROM order_items
                    WHERE order_id = ?
                )
                WHERE id = ?
            """, (order_id, order_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления услуг заказа: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============ СВЯЗЬ С КЛИЕНТАМИ ============
    
    def link_to_client(self, order_id: int, client_id: int) -> bool:
        """
        Привязывает заказ к клиенту
        
        Args:
            order_id: ID заказа
            client_id: ID клиента
            
        Returns:
            True если успешно
        """
        query = "UPDATE orders SET client_id = ? WHERE id = ?"
        return self.execute(query, (client_id, order_id))
    
    def get_client_orders_count(self, client_id: int) -> int:
        """
        Количество заказов клиента
        
        Args:
            client_id: ID клиента
            
        Returns:
            Количество заказов
        """
        query = "SELECT COUNT(*) as cnt FROM orders WHERE client_id = ?"
        result = self.fetch_one(query, (client_id,))
        return result['cnt'] if result else 0