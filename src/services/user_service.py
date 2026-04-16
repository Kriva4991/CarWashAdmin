# src/services/user_service.py
"""
Сервис для работы с пользователями и правами доступа
"""

from typing import List, Optional, Dict, Any
from repositories.user_repo import UserRepository, AuditRepository
from models.user import User, UserRole, Permission, AuditLog
from datetime import datetime


class UserService:
    """Сервис для управления пользователями и авторизацией"""
    
    def __init__(self):
        self.repo = UserRepository()
        self.audit_repo = AuditRepository()
        self._current_user: Optional[User] = None
        self._cache: Dict[str, Any] = {}
    
    # ============ ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ ============
    
    @property
    def current_user(self) -> Optional[User]:
        """Возвращает текущего авторизованного пользователя"""
        return self._current_user
    
    def set_current_user(self, user: User):
        """Устанавливает текущего пользователя"""
        self._current_user = user
    
    def logout(self):
        """Выход из системы"""
        if self._current_user:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="logout",
                details="Выход из системы"
            )
        self._current_user = None
        self._cache.clear()
    
    # ============ АВТОРИЗАЦИЯ ============
    
    def login(self, username: str, password: str) -> Optional[User]:
        """
        Авторизация пользователя
        
        Args:
            username: Логин
            password: Пароль
            
        Returns:
            User при успехе, None при ошибке
        """
        user_data = self.repo.verify_password(username, password)
        if not user_data:
            self.audit_repo.log(
                user_id=None,
                username=username,
                action="login_failed",
                details="Неверный логин или пароль"
            )
            return None
        
        # Получаем права пользователя
        permissions = self.repo.get_user_permissions(user_data['role'])
        
        # Создаём модель User
        last_login = user_data.get('last_login')
        if last_login and isinstance(last_login, str):
            try:
                last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
            except ValueError:
                last_login = None
        
        created_at = user_data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = None
        
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            role=UserRole.from_string(user_data['role']),
            is_active=bool(user_data.get('is_active', 1)),
            last_login=last_login,
            created_at=created_at,
            permissions=permissions
        )
        
        self._current_user = user
        
        self.audit_repo.log(
            user_id=user.id,
            username=user.username,
            action="login",
            details=f"Вход в систему (роль: {user.role.value})"
        )
        
        return user
    
    # ============ ПРОВЕРКА ПРАВ ============
    
    def has_permission(self, permission: str) -> bool:
        """Проверяет, есть ли у текущего пользователя право"""
        if not self._current_user:
            return False
        return self._current_user.has_permission(permission)
    
    def require_permission(self, permission: str) -> bool:
        """Требует наличие права (возвращает False если нет)"""
        if not self.has_permission(permission):
            self.audit_repo.log(
                user_id=self._current_user.id if self._current_user else None,
                username=self._current_user.username if self._current_user else 'anonymous',
                action="permission_denied",
                details=f"Отказано в доступе: {permission}"
            )
            return False
        return True
    
    # ============ УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ============
    
    def get_all_users(self) -> List[User]:
        """Получает всех пользователей (только для админа)"""
        if not self.require_permission('manage_users'):
            return []
        
        users_data = self.repo.get_all()
        users = []
        
        for data in users_data:
            permissions = self.repo.get_user_permissions(data['role'])
            users.append(User(
                id=data['id'],
                username=data['username'],
                role=UserRole.from_string(data['role']),
                is_active=bool(data.get('is_active', 1)),
                permissions=permissions
            ))
        
        return users
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID"""
        if not self.require_permission('manage_users'):
            return None
        
        data = self.repo.get_by_id(user_id)
        if not data:
            return None
        
        permissions = self.repo.get_user_permissions(data['role'])
        return User(
            id=data['id'],
            username=data['username'],
            role=UserRole.from_string(data['role']),
            is_active=bool(data.get('is_active', 1)),
            permissions=permissions
        )
    
    def create_user(self, username: str, password: str, role: str) -> Optional[int]:
        """Создаёт нового пользователя"""
        if not self.require_permission('manage_users'):
            return None
        
        # Проверяем, существует ли уже такой пользователь
        existing = self.repo.get_by_username(username)
        if existing:
            return None
        
        user_id = self.repo.create(username, password, role)
        
        if user_id:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="create_user",
                entity_type="user",
                entity_id=user_id,
                details=f"Создан пользователь: {username} (роль: {role})"
            )
            self._cache.clear()
        
        return user_id
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновляет пользователя"""
        if not self.require_permission('manage_users'):
            return False
        
        # Нельзя изменить роль админа, если это последний админ
        if 'role' in update_data and update_data['role'] != 'admin':
            admins = [u for u in self.get_all_users() if u.role == UserRole.ADMIN and u.is_active]
            if len(admins) == 1 and admins[0].id == user_id:
                return False  # Нельзя снять роль с последнего админа
        
        success = self.repo.update(user_id, update_data)
        
        if success:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="update_user",
                entity_type="user",
                entity_id=user_id,
                details=f"Обновлён пользователь ID={user_id}: {update_data}"
            )
            self._cache.clear()
        
        return success
    
    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        if not self.require_permission('manage_users'):
            return False
        
        # Нельзя удалить самого себя
        if self._current_user and self._current_user.id == user_id:
            return False
        
        # Нельзя удалить последнего админа
        admins = [u for u in self.get_all_users() if u.role == UserRole.ADMIN and u.is_active]
        user_to_delete = self.get_user(user_id)
        if user_to_delete and user_to_delete.role == UserRole.ADMIN and len(admins) == 1:
            return False
        
        success = self.repo.delete(user_id)
        
        if success:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="delete_user",
                entity_type="user",
                entity_id=user_id,
                details=f"Удалён пользователь ID={user_id}"
            )
            self._cache.clear()
        
        return success
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Меняет пароль пользователя"""
        if not self.require_permission('manage_users'):
            return False
        
        success = self.repo.update(user_id, {'password': new_password})
        
        if success:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="change_password",
                entity_type="user",
                entity_id=user_id,
                details=f"Изменён пароль пользователя ID={user_id}"
            )
        
        return success
    
    def change_own_password(self, old_password: str, new_password: str) -> bool:
        """Меняет пароль текущего пользователя"""
        if not self._current_user:
            return False
        
        # Проверяем старый пароль
        user_data = self.repo.verify_password(self._current_user.username, old_password)
        if not user_data:
            return False
        
        success = self.repo.update(self._current_user.id, {'password': new_password})
        
        if success:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action="change_own_password",
                details="Изменён собственный пароль"
            )
        
        return success
    
    # ============ АУДИТ ============
    
    def log_action(self, action: str, entity_type: str = None, 
                   entity_id: int = None, details: str = None):
        """Логирует действие текущего пользователя"""
        if self._current_user:
            self.audit_repo.log(
                user_id=self._current_user.id,
                username=self._current_user.username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details
            )
    
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Получает журнал аудита (только для админа)"""
        if not self.require_permission('manage_users'):
            return []
        
        logs = self.audit_repo.get_recent(limit)
        result = []
        
        for log in logs:
            created_at = log.get('created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.now()
            
            result.append(AuditLog(
                id=log['id'],
                user_id=log.get('user_id'),
                username=log['username'],
                action=log['action'],
                entity_type=log.get('entity_type'),
                entity_id=log.get('entity_id'),
                details=log.get('details'),
                created_at=created_at or datetime.now()
            ))
        
        return result
    
    # ============ РОЛИ И ПРАВА ============
    
    def get_available_roles(self) -> List[Dict[str, str]]:
        """Возвращает список доступных ролей"""
        return [
            {'value': 'admin', 'label': '👑 Администратор'},
            {'value': 'manager', 'label': '👔 Менеджер'},
            {'value': 'washer', 'label': '🧽 Мойщик'},
        ]
    
    def get_all_permissions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Возвращает все права, сгруппированные по категориям"""
        query = """
            SELECT id, name, description, category
            FROM permissions
            ORDER BY category, name
        """
        rows = self.repo.fetch_all(query)
        
        grouped = {}
        for row in rows:
            category = row['category'] or 'other'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description']
            })
        
        return grouped


# Глобальный экземпляр сервиса
user_service = UserService()