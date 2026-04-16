# src/services/consumable_service.py
"""
Сервис для работы с расходными материалами
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from repositories.consumable_repo import ConsumableRepository
from models.consumable import Consumable, ConsumableUsage, ConsumableStats
from services.user_service import user_service


class ConsumableService:
    """Сервис для управления расходниками"""
    
    def __init__(self):
        self.repo = ConsumableRepository()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300
    
    # ============ ПРОВЕРКА ПРАВ ============
    
    def _check_permission(self, permission: str) -> bool:
        """Проверяет права доступа"""
        return user_service.has_permission(permission)
    
    # ============ ОСНОВНЫЕ МЕТОДЫ ============
    
    def get_all(self) -> List[Consumable]:
        """Получает все расходники"""
        if not self._check_permission('view_consumables'):
            return []
        
        rows = self.repo.get_all()
        return [Consumable.from_db_row(row) for row in rows]
    
    def get_by_id(self, consumable_id: int) -> Optional[Consumable]:
        """Получает расходник по ID"""
        if not self._check_permission('view_consumables'):
            return None
        
        row = self.repo.get_by_id(consumable_id)
        if row:
            return Consumable.from_db_row(row)
        return None
    
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """Создаёт новый расходник"""
        if not self._check_permission('manage_consumables'):
            return None
        
        consumable_id = self.repo.create(data)
        
        if consumable_id:
            user_service.log_action(
                action="create_consumable",
                entity_type="consumable",
                entity_id=consumable_id,
                details=f"Создан расходник: {data.get('name')}"
            )
            self._cache.clear()
        
        return consumable_id
    
    def update(self, consumable_id: int, data: Dict[str, Any]) -> bool:
        """Обновляет расходник"""
        if not self._check_permission('manage_consumables'):
            return False
        
        success = self.repo.update(consumable_id, data)
        
        if success:
            user_service.log_action(
                action="update_consumable",
                entity_type="consumable",
                entity_id=consumable_id,
                details=f"Обновлён расходник ID={consumable_id}"
            )
            self._cache.clear()
        
        return success
    
    def delete(self, consumable_id: int) -> bool:
        """Удаляет расходник"""
        if not self._check_permission('manage_consumables'):
            return False
        
        consumable = self.get_by_id(consumable_id)
        success = self.repo.delete(consumable_id)
        
        if success and consumable:
            user_service.log_action(
                action="delete_consumable",
                entity_type="consumable",
                entity_id=consumable_id,
                details=f"Удалён расходник: {consumable.name}"
            )
            self._cache.clear()
        
        return success
    
    def add_stock(self, consumable_id: int, quantity: float) -> bool:
        """Пополняет запас"""
        if not self._check_permission('manage_consumables'):
            return False
        
        success = self.repo.add_stock(consumable_id, quantity)
        
        if success:
            consumable = self.get_by_id(consumable_id)
            user_service.log_action(
                action="add_stock",
                entity_type="consumable",
                entity_id=consumable_id,
                details=f"Пополнение: +{quantity} ({consumable.name if consumable else ''})"
            )
            self._cache.clear()
        
        return success
    
    def use_stock(self, consumable_id: int, quantity: float, 
                  order_id: Optional[int] = None, notes: Optional[str] = None) -> bool:
        """Списывает материал"""
        if not self._check_permission('manage_consumables'):
            return False
        
        success = self.repo.use_stock(consumable_id, quantity, order_id, notes)
        
        if success:
            consumable = self.get_by_id(consumable_id)
            user_service.log_action(
                action="use_stock",
                entity_type="consumable",
                entity_id=consumable_id,
                details=f"Списание: -{quantity} ({consumable.name if consumable else ''})"
            )
            self._cache.clear()
        
        return success
    
    def get_usage_history(self, consumable_id: Optional[int] = None, limit: int = 100) -> List[ConsumableUsage]:
        """Получает историю списаний"""
        if not self._check_permission('view_consumables'):
            return []
        
        rows = self.repo.get_usage_history(consumable_id, limit)
        return [ConsumableUsage.from_db_row(row) for row in rows]
    
    def get_low_stock(self) -> List[Consumable]:
        """Получает расходники с низким запасом"""
        if not self._check_permission('view_consumables'):
            return []
        
        rows = self.repo.get_low_stock()
        return [Consumable.from_db_row(row) for row in rows]
    
    def get_low_stock_count(self) -> int:
        """Количество расходников с низким запасом"""
        return len(self.get_low_stock())
    
    def get_stats(self) -> ConsumableStats:
        """Получает статистику"""
        if not self._check_permission('view_consumables'):
            return ConsumableStats()
        
        data = self.repo.get_stats()
        
        return ConsumableStats(
            total_items=data.get('total_items', 0) or 0,
            low_stock_count=(data.get('low_count', 0) or 0),
            empty_count=(data.get('empty_count', 0) or 0),
            total_cost=(data.get('total_cost', 0) or 0)
        )


# Глобальный экземпляр
consumable_service = ConsumableService()