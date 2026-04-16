# src/models/order.py
"""
Модели данных для работы с заказами
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    """Статусы заказа"""
    QUEUE = "queue"       # В очереди
    PROCESS = "process"   # В работе
    DONE = "done"         # Готово
    CANCELLED = "cancelled"  # Отменено
    
    @property
    def display_name(self) -> str:
        """Отображаемое название статуса"""
        names = {
            OrderStatus.QUEUE: "🟡 В очереди",
            OrderStatus.PROCESS: "🔵 В работе",
            OrderStatus.DONE: "🟢 Готово",
            OrderStatus.CANCELLED: "🔴 Отменено"
        }
        return names[self]
    
    @property
    def color(self) -> str:
        """Цвет для отображения статуса"""
        colors = {
            OrderStatus.QUEUE: "#f39c12",      # Оранжевый
            OrderStatus.PROCESS: "#3498db",    # Синий
            OrderStatus.DONE: "#27ae60",       # Зелёный
            OrderStatus.CANCELLED: "#e74c3c"   # Красный
        }
        return colors[self]
    
    @property
    def next_status(self) -> Optional['OrderStatus']:
        """Следующий статус при переключении"""
        transitions = {
            OrderStatus.QUEUE: OrderStatus.PROCESS,
            OrderStatus.PROCESS: OrderStatus.DONE,
            OrderStatus.DONE: OrderStatus.QUEUE,  # Циклично для демо
            OrderStatus.CANCELLED: None
        }
        return transitions.get(self)
    
    @classmethod
    def from_string(cls, value: str) -> 'OrderStatus':
        """Создаёт статус из строки"""
        mapping = {
            'queue': cls.QUEUE,
            'process': cls.PROCESS,
            'done': cls.DONE,
            'cancelled': cls.CANCELLED
        }
        return mapping.get(value.lower(), cls.QUEUE)


class PaymentMethod(Enum):
    """Способы оплаты"""
    CASH = "cash"           # Наличные
    CARD = "card"           # Карта
    TRANSFER = "transfer"   # Перевод
    SBP = "sbp"             # СБП
    
    @property
    def display_name(self) -> str:
        """Отображаемое название"""
        names = {
            PaymentMethod.CASH: "💵 Наличные",
            PaymentMethod.CARD: "💳 Карта",
            PaymentMethod.TRANSFER: "📱 Перевод",
            PaymentMethod.SBP: "📲 СБП"
        }
        return names[self]
    
    @classmethod
    def from_string(cls, value: str) -> 'PaymentMethod':
        """Создаёт из строки"""
        if not value:
            return cls.CASH
        
        value = value.lower()
        if 'нал' in value or 'cash' in value:
            return cls.CASH
        elif 'карт' in value or 'card' in value:
            return cls.CARD
        elif 'перевод' in value or 'transfer' in value:
            return cls.TRANSFER
        elif 'сбп' in value or 'sbp' in value:
            return cls.SBP
        return cls.CASH


@dataclass
class OrderItem:
    """Элемент заказа (услуга)"""
    service_id: int
    service_name: str
    quantity: int = 1
    base_price: float = 0.0
    final_price: float = 0.0
    
    @property
    def total_price(self) -> float:
        """Итоговая стоимость позиции"""
        return self.final_price * self.quantity
    
    @property
    def discount_percent(self) -> float:
        """Процент скидки"""
        if self.base_price > 0:
            return ((self.base_price - self.final_price) / self.base_price) * 100
        return 0.0
    
    @property
    def has_discount(self) -> bool:
        """Есть ли скидка"""
        return self.final_price < self.base_price


@dataclass
class Order:
    """Модель заказа"""
    id: int
    car_number: str
    created_at: datetime
    status: OrderStatus = OrderStatus.QUEUE
    car_model: Optional[str] = None
    client_phone: Optional[str] = None
    client_id: Optional[int] = None
    car_class_id: Optional[int] = None
    car_class_name: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    comment: Optional[str] = None
    shift_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    # Состав заказа
    items: List[OrderItem] = field(default_factory=list)
    
    @property
    def total_price(self) -> float:
        """Общая сумма заказа"""
        return sum(item.total_price for item in self.items)
    
    @property
    def total_services(self) -> int:
        """Общее количество услуг"""
        return sum(item.quantity for item in self.items)
    
    @property
    def services_display(self) -> str:
        """Список услуг через запятую"""
        if not self.items:
            return "—"
        
        service_names = []
        for item in self.items:
            if item.quantity > 1:
                service_names.append(f"{item.service_name} x{item.quantity}")
            else:
                service_names.append(item.service_name)
        
        return ", ".join(service_names)
    
    @property
    def formatted_date(self) -> str:
        """Форматированная дата создания"""
        if isinstance(self.created_at, str):
            return self.created_at[:16]
        return self.created_at.strftime("%Y-%m-%d %H:%M")
    
    @property
    def formatted_time(self) -> str:
        """Только время"""
        if isinstance(self.created_at, str):
            return self.created_at[11:16] if len(self.created_at) >= 16 else ""
        return self.created_at.strftime("%H:%M")
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя заказа"""
        if self.car_model:
            return f"{self.car_number} ({self.car_model})"
        return self.car_number
    
    @property
    def is_paid(self) -> bool:
        """Оплачен ли заказ"""
        # Можно добавить логику, если будет поле paid
        return self.status == OrderStatus.DONE
    
    @property
    def can_edit(self) -> bool:
        """Можно ли редактировать заказ"""
        return self.status != OrderStatus.CANCELLED
    
    @property
    def can_delete(self) -> bool:
        """Можно ли удалить заказ"""
        return self.status in [OrderStatus.QUEUE, OrderStatus.CANCELLED]
    
    def add_item(self, item: OrderItem):
        """Добавляет услугу в заказ"""
        # Проверяем, нет ли уже такой услуги
        for existing in self.items:
            if existing.service_id == item.service_id:
                existing.quantity += item.quantity
                return
        self.items.append(item)
    
    def remove_item(self, service_id: int):
        """Удаляет услугу из заказа"""
        self.items = [item for item in self.items if item.service_id != service_id]
    
    def change_status(self, new_status: OrderStatus) -> bool:
        """Меняет статус заказа"""
        if new_status == self.status:
            return False
        
        # Здесь можно добавить бизнес-логику (например, нельзя отменить готовый заказ)
        self.status = new_status
        return True
    
    def toggle_status(self) -> OrderStatus:
        """Переключает на следующий статус"""
        next_stat = self.status.next_status
        if next_stat:
            self.status = next_stat
        return self.status
    
    def to_dict(self) -> dict:
        """Конвертирует в словарь"""
        return {
            'id': self.id,
            'car_number': self.car_number,
            'car_model': self.car_model,
            'client_phone': self.client_phone,
            'client_id': self.client_id,
            'status': self.status.value,
            'total_price': self.total_price,
            'payment_method': self.payment_method.value,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [
                {
                    'service_id': item.service_id,
                    'service_name': item.service_name,
                    'quantity': item.quantity,
                    'base_price': item.base_price,
                    'final_price': item.final_price
                }
                for item in self.items
            ]
        }
    
    @classmethod
    def from_db_row(cls, row: dict, items: List[dict] = None) -> 'Order':
        """
        Создаёт объект Order из строки БД
        
        Args:
            row: Словарь с данными заказа
            items: Список словарей с услугами заказа
        """
        # Парсим дату
        created_at = row.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        elif not created_at:
            created_at = datetime.now()
        
        updated_at = row.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except ValueError:
                updated_at = None
        
        # Создаём заказ
        order = cls(
            id=row.get('id', 0),
            car_number=row.get('car_number', ''),
            car_model=row.get('car_model'),
            client_phone=row.get('client_phone'),
            client_id=row.get('client_id'),
            car_class_id=row.get('car_class_id'),
            car_class_name=row.get('car_class_name'),
            created_at=created_at,
            updated_at=updated_at,
            status=OrderStatus.from_string(row.get('status', 'queue')),
            payment_method=PaymentMethod.from_string(row.get('payment_method', '')),
            comment=row.get('comment'),
            shift_id=row.get('shift_id')
        )
        
        # Добавляем услуги
        if items:
            for item in items:
                order_item = OrderItem(
                    service_id=item.get('service_id', 0),
                    service_name=item.get('service_name', ''),
                    quantity=item.get('quantity', 1),
                    base_price=item.get('base_price', 0.0) or 0.0,
                    final_price=item.get('final_price', 0.0) or 0.0
                )
                order.items.append(order_item)
        
        return order


@dataclass
class OrderSearchResult:
    """Результат поиска заказов с пагинацией"""
    orders: List[Order]
    total_count: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Общее количество страниц"""
        return (self.total_count + self.page_size - 1) // self.page_size
    
    @property
    def has_previous(self) -> bool:
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def display_range(self) -> str:
        """Отображаемый диапазон"""
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total_count)
        return f"{start}-{end} из {self.total_count}"
    
    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """Фильтрует заказы по статусу"""
        return [o for o in self.orders if o.status == status]


@dataclass
class OrderStatistics:
    """Статистика по заказам"""
    total_orders: int = 0
    total_revenue: float = 0.0
    avg_check: float = 0.0
    
    # По статусам
    queue_count: int = 0
    process_count: int = 0
    done_count: int = 0
    cancelled_count: int = 0
    
    # По оплате
    cash_count: int = 0
    cash_amount: float = 0.0
    card_count: int = 0
    card_amount: float = 0.0
    transfer_count: int = 0
    transfer_amount: float = 0.0
    sbp_count: int = 0
    sbp_amount: float = 0.0
    
    @property
    def completion_rate(self) -> float:
        """Процент выполненных заказов"""
        if self.total_orders == 0:
            return 0.0
        return (self.done_count / self.total_orders) * 100
    
    @property
    def formatted_revenue(self) -> str:
        """Форматированная выручка"""
        return f"{self.total_revenue:,.0f} ₽".replace(",", " ")
    
    @property
    def formatted_avg_check(self) -> str:
        """Форматированный средний чек"""
        return f"{self.avg_check:,.0f} ₽".replace(",", " ")