# src/models/user.py
"""Модели для пользователей и прав доступа"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    
    @property
    def display_name(self) -> str:
        names = {
            UserRole.ADMIN: "👑 Администратор",
            UserRole.MANAGER: "👔 Менеджер",
            UserRole.WASHER: "🧽 Мойщик"
        }
        return names[self]
    
    @classmethod
    def from_string(cls, value: str) -> 'UserRole':
        mapping = {
            'admin': cls.ADMIN,
            'manager': cls.MANAGER,
            'washer': cls.WASHER
        }
        return mapping.get(value.lower(), cls.WASHER)


@dataclass
class Permission:
    """Право доступа"""
    id: int
    name: str
    description: str
    category: str


@dataclass
class User:
    """Пользователь системы"""
    id: int
    username: str
    role: UserRole
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    permissions: List[str] = None
    
    def has_permission(self, permission: str) -> bool:
        """Проверяет наличие права"""
        if self.role == UserRole.ADMIN:
            return True  # Админ имеет все права
        if self.permissions is None:
            return False
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Проверяет наличие хотя бы одного права из списка"""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Проверяет наличие всех прав из списка"""
        return all(self.has_permission(p) for p in permissions)


@dataclass
class AuditLog:
    """Запись в журнале аудита"""
    id: int
    user_id: Optional[int]
    username: str
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Optional[str]
    created_at: datetime