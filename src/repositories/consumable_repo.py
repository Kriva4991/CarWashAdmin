# src/repositories/consumable_repo.py
"""Репозиторий для работы с расходными материалами"""

from typing import List, Optional, Dict, Any
from datetime import date
from .base import BaseRepository


class ConsumableRepository(BaseRepository):
    """Репозиторий для работы с расходниками"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "consumables"
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Получает все расходники"""
        query = """
            SELECT * FROM consumables
            ORDER BY 
                CASE 
                    WHEN current_stock <= 0 THEN 1
                    WHEN current_stock <= min_stock THEN 2
                    ELSE 3
                END,
                name
        """
        return self.fetch_all(query)
    
    def get_by_id(self, consumable_id: int) -> Optional[Dict[str, Any]]:
        """Получает расходник по ID"""
        query = "SELECT * FROM consumables WHERE id = ?"
        return self.fetch_one(query, (consumable_id,))
    
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """Создаёт новый расходник"""
        query = """
            INSERT INTO consumables (name, unit, current_stock, min_stock, cost_per_unit)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_and_get_id(query, (
            data.get('name', ''),
            data.get('unit', 'шт'),
            data.get('current_stock', 0),
            data.get('min_stock', 0),
            data.get('cost_per_unit', 0)
        ))
    
    def update(self, consumable_id: int, data: Dict[str, Any]) -> bool:
        """Обновляет расходник"""
        fields = []
        params = []
        
        allowed = ['name', 'unit', 'current_stock', 'min_stock', 'cost_per_unit', 'last_restock']
        for field in allowed:
            if field in data:
                fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not fields:
            return False
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(consumable_id)
        
        query = f"UPDATE consumables SET {', '.join(fields)} WHERE id = ?"
        return self.execute(query, tuple(params))
    
    def delete(self, consumable_id: int) -> bool:
        """Удаляет расходник"""
        query = "DELETE FROM consumables WHERE id = ?"
        return self.execute(query, (consumable_id,))
    
    def add_stock(self, consumable_id: int, quantity: float) -> bool:
        """Пополняет запас"""
        query = """
            UPDATE consumables 
            SET current_stock = current_stock + ?,
                last_restock = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.execute(query, (quantity, date.today().isoformat(), consumable_id))
    
    def use_stock(self, consumable_id: int, quantity: float, 
                  order_id: Optional[int] = None, notes: Optional[str] = None) -> bool:
        """Списывает материал"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем, достаточно ли остатка
            cursor.execute("SELECT current_stock FROM consumables WHERE id = ?", (consumable_id,))
            row = cursor.fetchone()
            if not row or row['current_stock'] < quantity:
                return False
            
            # Списываем
            cursor.execute("""
                UPDATE consumables 
                SET current_stock = current_stock - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (quantity, consumable_id))
            
            # Записываем использование
            cursor.execute("""
                INSERT INTO consumable_usage (consumable_id, order_id, quantity, notes)
                VALUES (?, ?, ?, ?)
            """, (consumable_id, order_id, quantity, notes))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка списания: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_usage_history(self, consumable_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает историю списаний"""
        query = """
            SELECT 
                cu.id,
                cu.consumable_id,
                c.name as consumable_name,
                cu.quantity,
                cu.used_at,
                cu.order_id,
                cu.notes
            FROM consumable_usage cu
            JOIN consumables c ON cu.consumable_id = c.id
        """
        params = []
        
        if consumable_id:
            query += " WHERE cu.consumable_id = ?"
            params.append(consumable_id)
        
        query += " ORDER BY cu.used_at DESC LIMIT ?"
        params.append(limit)
        
        return self.fetch_all(query, tuple(params))
    
    def get_low_stock(self) -> List[Dict[str, Any]]:
        """Получает расходники с низким запасом"""
        query = """
            SELECT * FROM consumables
            WHERE current_stock <= min_stock
            ORDER BY current_stock ASC
        """
        return self.fetch_all(query)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику"""
        query = """
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN current_stock <= 0 THEN 1 ELSE 0 END) as empty_count,
                SUM(CASE WHEN current_stock <= min_stock AND current_stock > 0 THEN 1 ELSE 0 END) as low_count,
                SUM(current_stock * cost_per_unit) as total_cost
            FROM consumables
        """
        return self.fetch_one(query) or {}