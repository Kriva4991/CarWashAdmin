# src/models/consumable.py
"""Модели для учёта расходных материалов"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date


@dataclass
class Consumable:
    """Расходный материал"""
    id: int
    name: str
    unit: str = 'шт'
    current_stock: float = 0.0
    min_stock: float = 0.0
    cost_per_unit: float = 0.0
    last_restock: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_low_stock(self) -> bool:
        """Проверяет, ниже ли запас минимального"""
        return self.current_stock <= self.min_stock
    
    @property
    def stock_status(self) -> str:
        """Статус запаса"""
        if self.current_stock <= 0:
            return 'empty'
        elif self.current_stock <= self.min_stock:
            return 'low'
        return 'normal'
    
    @property
    def stock_status_display(self) -> str:
        """Отображение статуса запаса"""
        statuses = {
            'empty': '🔴 Закончился',
            'low': '🟡 Мало',
            'normal': '🟢 Норма'
        }
        return statuses.get(self.stock_status, '')
    
    @property
    def stock_status_color(self) -> str:
        """Цвет для отображения статуса"""
        colors = {
            'empty': '#e74c3c',
            'low': '#f39c12',
            'normal': '#27ae60'
        }
        return colors.get(self.stock_status, '#95a5a6')
    
    @property
    def formatted_stock(self) -> str:
        """Форматированный остаток"""
        if self.current_stock == int(self.current_stock):
            return f"{int(self.current_stock)} {self.unit}"
        return f"{self.current_stock:.1f} {self.unit}"
    
    @property
    def formatted_cost(self) -> str:
        """Форматированная цена"""
        return f"{self.cost_per_unit:.0f} ₽/{self.unit}"
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Consumable':
        """Создаёт объект из строки БД"""
        last_restock = row.get('last_restock')
        if last_restock and isinstance(last_restock, str):
            try:
                last_restock = date.fromisoformat(last_restock)
            except ValueError:
                last_restock = None
        
        created_at = row.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = None
        
        updated_at = row.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except ValueError:
                updated_at = None
        
        return cls(
            id=row['id'],
            name=row['name'],
            unit=row.get('unit', 'шт'),
            current_stock=row.get('current_stock', 0) or 0,
            min_stock=row.get('min_stock', 0) or 0,
            cost_per_unit=row.get('cost_per_unit', 0) or 0,
            last_restock=last_restock,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def to_dict(self) -> dict:
        """Конвертирует в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'current_stock': self.current_stock,
            'min_stock': self.min_stock,
            'cost_per_unit': self.cost_per_unit,
            'last_restock': self.last_restock.isoformat() if self.last_restock else None,
            'is_low_stock': self.is_low_stock,
            'stock_status': self.stock_status
        }


@dataclass
class ConsumableUsage:
    """Запись о списании расходника"""
    id: int
    consumable_id: int
    quantity: float
    used_at: datetime
    consumable_name: Optional[str] = None
    order_id: Optional[int] = None
    notes: Optional[str] = None
    
    @property
    def formatted_date(self) -> str:
        """Форматированная дата"""
        if isinstance(self.used_at, str):
            return self.used_at[:16]
        return self.used_at.strftime("%Y-%m-%d %H:%M")
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'ConsumableUsage':
        """Создаёт объект из строки БД"""
        used_at = row.get('used_at')
        if used_at and isinstance(used_at, str):
            try:
                used_at = datetime.fromisoformat(used_at.replace('Z', '+00:00'))
            except ValueError:
                used_at = datetime.now()
        
        return cls(
            id=row['id'],
            consumable_id=row['consumable_id'],
            quantity=row['quantity'],
            used_at=used_at or datetime.now(),
            consumable_name=row.get('consumable_name'),
            order_id=row.get('order_id'),
            notes=row.get('notes')
        )


@dataclass
class ConsumableStats:
    """Статистика по расходникам"""
    total_items: int = 0
    low_stock_count: int = 0
    empty_count: int = 0
    total_cost: float = 0.0
    monthly_usage: List[dict] = None