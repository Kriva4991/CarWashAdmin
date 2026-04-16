# src/models/client.py
"""
Модели данных для работы с клиентами
Используем dataclasses для типобезопасности и удобства
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ClientLoyaltyLevel(Enum):
    """Уровень лояльности клиента (для цветовой индикации)"""
    NEW = "new"          # Новый клиент (1 визит)
    REGULAR = "regular"  # Постоянный (2-4 визита)
    VIP = "vip"          # VIP (5+ визитов)
    
    @property
    def border_color(self) -> str:
        """Цвет рамки карточки"""
        colors = {
            ClientLoyaltyLevel.NEW: "#3498db",      # Синий
            ClientLoyaltyLevel.REGULAR: "#f39c12",  # Оранжевый
            ClientLoyaltyLevel.VIP: "#27ae60"       # Зелёный
        }
        return colors[self]
    
    @property
    def display_name(self) -> str:
        """Отображаемое название уровня"""
        names = {
            ClientLoyaltyLevel.NEW: "Новый",
            ClientLoyaltyLevel.REGULAR: "Постоянный",
            ClientLoyaltyLevel.VIP: "VIP"
        }
        return names[self]


@dataclass
class Client:
    """
    Модель клиента
    Иммутабельная (неизменяемая) - лучше для предсказуемости
    """
    id: int
    car_number: str
    car_model: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Агрегированные данные из заказов
    total_visits: int = 0
    total_spent: float = 0.0
    last_visit: Optional[datetime] = None
    
    @property
    def loyalty_level(self) -> ClientLoyaltyLevel:
        """Определяет уровень лояльности по количеству визитов"""
        if self.total_visits >= 5:
            return ClientLoyaltyLevel.VIP
        elif self.total_visits >= 2:
            return ClientLoyaltyLevel.REGULAR
        return ClientLoyaltyLevel.NEW
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя (госномер + модель)"""
        if self.car_model:
            return f"{self.car_number} ({self.car_model})"
        return self.car_number
    
    @property
    def formatted_phone(self) -> str:
        """Форматированный телефон для отображения"""
        if not self.phone:
            return "—"
        # Простое форматирование (можно улучшить)
        phone = self.phone.strip()
        if len(phone) == 11 and phone.startswith('7'):
            return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        if len(phone) == 11 and phone.startswith('8'):
            return f"8 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        return phone
    
    @property
    def formatted_total_spent(self) -> str:
        """Форматированная сумма потраченных средств"""
        return f"{self.total_spent:,.0f} ₽".replace(",", " ")
    
    @property
    def last_visit_display(self) -> str:
        """Отображение даты последнего визита"""
        if not self.last_visit:
            return "—"
        
        # Если это строка из БД, конвертируем
        if isinstance(self.last_visit, str):
            try:
                dt = datetime.fromisoformat(self.last_visit.replace('Z', '+00:00'))
            except ValueError:
                return self.last_visit[:10]
        else:
            dt = self.last_visit
        
        # Форматируем дату
        today = datetime.now().date()
        visit_date = dt.date()
        
        if visit_date == today:
            return "Сегодня"
        elif (today - visit_date).days == 1:
            return "Вчера"
        elif (today - visit_date).days < 7:
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            return days[visit_date.weekday()]
        else:
            return visit_date.strftime("%d.%m.%Y")
    
    def to_dict(self) -> dict:
        """Конвертирует модель в словарь (для совместимости со старым кодом)"""
        return {
            'id': self.id,
            'car_number': self.car_number,
            'car_model': self.car_model,
            'phone': self.phone,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_visits': self.total_visits,
            'total_spent': self.total_spent,
            'last_visit': self.last_visit.isoformat() if self.last_visit else None
        }
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Client':
        """
        Создаёт объект Client из строки БД (sqlite3.Row)
        
        Пример использования:
            cursor.execute("SELECT * FROM clients WHERE id = ?", (1,))
            row = cursor.fetchone()
            client = Client.from_db_row(dict(row))
        """
        return cls(
            id=row.get('id'),
            car_number=row.get('car_number', ''),
            car_model=row.get('car_model'),
            phone=row.get('phone'),
            comment=row.get('comment'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            total_visits=row.get('total_visits', 0) or 0,
            total_spent=row.get('total_spent', 0.0) or 0.0,
            last_visit=row.get('last_visit')
        )


@dataclass
class ClientOrderHistory:
    """Модель для истории заказов клиента"""
    order_id: int
    created_at: datetime
    car_number: str
    total_price: float
    status: str
    services: List[str] = field(default_factory=list)
    payment_method: Optional[str] = None
    
    @property
    def formatted_date(self) -> str:
        """Форматированная дата заказа"""
        if isinstance(self.created_at, str):
            return self.created_at[:16]
        return self.created_at.strftime("%Y-%m-%d %H:%M")
    
    @property
    def status_display(self) -> str:
        """Отображение статуса с эмодзи"""
        statuses = {
            'queue': '🟡 В очереди',
            'process': '🔵 В работе',
            'done': '🟢 Готово',
            'cancelled': '🔴 Отменено'
        }
        return statuses.get(self.status, self.status)
    
    @property
    def services_display(self) -> str:
        """Список услуг через запятую"""
        return ", ".join(self.services) if self.services else "—"


@dataclass
class ClientSearchResult:
    """Результат поиска клиентов с пагинацией"""
    clients: List[Client]
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
        """Отображаемый диапазон (например: "1-50 из 234")"""
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total_count)
        return f"{start}-{end} из {self.total_count}"