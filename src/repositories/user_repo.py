# src/repositories/user_repo.py
"""Репозиторий для работы с пользователями"""

from typing import List, Optional, Dict, Any
from .base import BaseRepository
import bcrypt


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "users"
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по логину"""
        query = "SELECT * FROM users WHERE username = ?"
        return self.fetch_one(query, (username,))
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по ID"""
        query = "SELECT * FROM users WHERE id = ?"
        return self.fetch_one(query, (user_id,))
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей"""
        query = "SELECT * FROM users ORDER BY username"
        return self.fetch_all(query)
    
    def get_user_permissions(self, role: str) -> List[str]:
        """Получает список прав для роли"""
        query = """
            SELECT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role = ?
        """
        rows = self.fetch_all(query, (role,))
        return [row['name'] for row in rows]
    
    def create(self, username: str, password: str, role: str = 'washer') -> Optional[int]:
        """Создаёт нового пользователя"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        query = """
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, 1)
        """
        return self.execute_and_get_id(query, (username, password_hash.decode(), role))
    
    def update(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновляет пользователя"""
        fields = []
        params = []
        
        allowed = ['username', 'role', 'is_active']
        for field in allowed:
            if field in update_data:
                fields.append(f"{field} = ?")
                params.append(update_data[field])
        
        if 'password' in update_data:
            password_hash = bcrypt.hashpw(update_data['password'].encode(), bcrypt.gensalt())
            fields.append("password_hash = ?")
            params.append(password_hash.decode())
        
        if not fields:
            return False
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        return self.execute(query, tuple(params))
    
    def delete(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        query = "DELETE FROM users WHERE id = ?"
        return self.execute(query, (user_id,))
    
    def update_last_login(self, user_id: int) -> bool:
        """Обновляет время последнего входа"""
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        return self.execute(query, (user_id,))
    
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Проверяет логин и пароль"""
        user = self.get_by_username(username)
        if not user:
            return None
        
        password_hash = user['password_hash']
        
        # Проверяем, что хеш существует
        if not password_hash:
            return None
        
        try:
            # Конвертируем в bytes если нужно
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            # Проверяем пароль
            if bcrypt.checkpw(password.encode('utf-8'), password_hash):
                if user.get('is_active', 1):
                    self.update_last_login(user['id'])
                    return user
        except Exception as e:
            print(f"❌ Ошибка проверки пароля: {e}")
            return None
        
        return None


class AuditRepository(BaseRepository):
    """Репозиторий для журнала аудита"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "audit_log"
    
    def log(
        self,
        user_id: Optional[int],
        username: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> bool:
        """Добавляет запись в журнал"""
        query = """
            INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, username, action, entity_type, entity_id, details))
    
    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает последние записи"""
        query = """
            SELECT * FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))