# src/repositories/base.py
"""
Базовый репозиторий с общими методами для работы с БД
Используем паттерн Repository для абстракции доступа к данным
"""

from typing import Optional, Dict, Any, List
from database import get_connection
import sqlite3


class BaseRepository:
    """
    Базовый класс для всех репозиториев
    
    Пример использования:
        class ClientRepository(BaseRepository):
            def get_by_id(self, client_id: int):
                return self.fetch_one(
                    "SELECT * FROM clients WHERE id = ?",
                    (client_id,)
                )
    """
    
    def __init__(self):
        self.table_name = ""  # Должен быть переопределён в дочерних классах
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получает соединение с БД"""
        return get_connection()
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает одну строку
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            Словарь с данными или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"❌ Ошибка SQL в fetch_one: {e}")
            print(f"   Запрос: {query}")
            print(f"   Параметры: {params}")
            return None
        finally:
            conn.close()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает все строки
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            Список словарей с данными
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"❌ Ошибка SQL в fetch_all: {e}")
            print(f"   Запрос: {query}")
            print(f"   Параметры: {params}")
            return []
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> bool:
        """
        Выполняет INSERT/UPDATE/DELETE запрос
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            True если успешно, False если ошибка
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Ошибка SQL в execute: {e}")
            print(f"   Запрос: {query}")
            print(f"   Параметры: {params}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """
        Выполняет множественный INSERT/UPDATE запрос
        
        Args:
            query: SQL запрос
            params_list: Список кортежей с параметрами
            
        Returns:
            True если успешно, False если ошибка
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(query, params_list)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Ошибка SQL в execute_many: {e}")
            print(f"   Запрос: {query}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def execute_and_get_id(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Выполняет INSERT и возвращает ID созданной записи
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            ID созданной записи или None при ошибке
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Ошибка SQL в execute_and_get_id: {e}")
            print(f"   Запрос: {query}")
            print(f"   Параметры: {params}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def count(self, where_clause: str = "", params: tuple = ()) -> int:
        """
        Подсчитывает количество записей в таблице
        
        Args:
            where_clause: Условие WHERE (без слова WHERE)
            params: Параметры для условия
            
        Returns:
            Количество записей
        """
        query = f"SELECT COUNT(*) as cnt FROM {self.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.fetch_one(query, params)
        return result['cnt'] if result else 0
    
    def exists(self, where_clause: str, params: tuple = ()) -> bool:
        """
        Проверяет существование записи
        
        Args:
            where_clause: Условие WHERE (без слова WHERE)
            params: Параметры для условия
            
        Returns:
            True если запись существует
        """
        return self.count(where_clause, params) > 0
    
    def paginate(
        self,
        query: str,
        params: tuple = (),
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Добавляет пагинацию к запросу
        
        Args:
            query: SQL запрос (без LIMIT/OFFSET)
            params: Параметры для запроса
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы
            
        Returns:
            Словарь с данными и метаинформацией
        """
        # Считаем общее количество
        count_query = f"""
            SELECT COUNT(*) as cnt FROM ({query}) as subquery
        """
        total = self.fetch_one(count_query, params)
        total_count = total['cnt'] if total else 0
        
        # Добавляем пагинацию
        offset = (page - 1) * page_size
        paginated_query = f"""
            {query}
            LIMIT {page_size} OFFSET {offset}
        """
        
        items = self.fetch_all(paginated_query, params)
        
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }