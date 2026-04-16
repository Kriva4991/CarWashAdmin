# src/license_manager.py
import os
import json
import random
import string
import hashlib
from datetime import datetime, timedelta
from database import get_connection

class LicenseManager:
    """Управление лицензиями с проверкой контрольной суммы"""
    
    # 🔐 СЕКРЕТ ДЛЯ ГЕНЕРАЦИИ (не меняй!)
    SECRET = "CarWashAdminPro2026SecretKey"
    
    def __init__(self):
        self.license_key = None
        self.license_type = None
        self.activated_at = None
        self.is_activated = False
    
    def _calculate_checksum(self, key_part: str) -> str:
        """Вычисляет контрольную сумму для части ключа"""
        data = f"{key_part}-{self.SECRET}"
        return hashlib.md5(data.encode()).hexdigest()[:4].upper()
    
    def generate_key(self, license_type: str = 'trial') -> str:
        """
        Генерирует лицензионный ключ с контрольной суммой
        
        Формат: CW-TYPE-XXXX-XXXX-CCCC
        где CCCC - контрольная сумма
        """
        # Генерируем случайную часть
        random_part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        random_part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Тип лицензии
        if license_type == 'lifetime':
            type_code = 'LIFE'
        else:
            type_code = '30'
        
        # Основная часть ключа
        key_base = f"CW-{type_code}-{random_part1}-{random_part2}"
        
        # Контрольная сумма
        checksum = self._calculate_checksum(key_base)
        
        return f"{key_base}-{checksum}"
    
    def _validate_key_format(self, license_key: str) -> tuple[bool, str, str]:
        """
        Проверяет формат и контрольную сумму ключа
        
        Returns:
            (is_valid, type_code, message)
        """
        if not license_key:
            return False, None, "Ключ пуст"
        
        parts = license_key.split('-')
        if len(parts) != 5:
            return False, None, "Неверный формат (должно быть 5 частей через дефис)"
        
        prefix, type_code, part1, part2, checksum = parts
        
        # Проверка префикса
        if prefix != 'CW':
            return False, None, "Неверный префикс (должен быть CW)"
        
        # Проверка типа
        if type_code not in ['LIFE', '30']:
            return False, None, f"Неизвестный тип: {type_code}"
        
        # 🔍 ПРОВЕРКА КОНТРОЛЬНОЙ СУММЫ
        key_base = f"{prefix}-{type_code}-{part1}-{part2}"
        expected_checksum = self._calculate_checksum(key_base)
        
        if checksum != expected_checksum:
            return False, None, "Неверная контрольная сумма (ключ невалиден)"
        
        return True, type_code, "OK"
    
    def load_license(self):
        """Загружает лицензию из БД"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = 'license_key'")
        row = cursor.fetchone()
        self.license_key = row['value'] if row else None
        
        cursor.execute("SELECT value FROM settings WHERE key = 'license_type'")
        row = cursor.fetchone()
        self.license_type = row['value'] if row else None
        
        cursor.execute("SELECT value FROM settings WHERE key = 'license_activated_at'")
        row = cursor.fetchone()
        self.activated_at = row['value'] if row else None
        
        cursor.execute("SELECT value FROM settings WHERE key = 'license_activated'")
        row = cursor.fetchone()
        self.is_activated = row['value'] == '1' if row else False
        
        conn.close()
    
    def save_license(self):
        """Сохраняет лицензию в БД"""
        conn = get_connection()
        cursor = conn.cursor()
        
        settings = [
            ('license_key', self.license_key or ''),
            ('license_type', self.license_type or ''),
            ('license_activated_at', self.activated_at or ''),
            ('license_activated', '1' if self.is_activated else '0'),
        ]
        
        for key, value in settings:
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
        
        conn.commit()
        conn.close()
    
    def activate(self, license_key: str) -> tuple[bool, str]:
        """Активирует лицензию по ключу"""
        # Проверяем формат и контрольную сумму
        is_valid, type_code, message = self._validate_key_format(license_key)
        
        if not is_valid:
            return False, f"Неверный ключ: {message}"
        
        # Определяем тип лицензии
        if type_code == 'LIFE':
            self.license_type = 'lifetime'
        else:
            self.license_type = 'trial'
        
        # Активируем
        self.license_key = license_key
        self.is_activated = True
        self.activated_at = datetime.now().isoformat()
        
        self.save_license()
        
        return True, f"Лицензия активирована! ({'Бессрочная' if self.license_type == 'lifetime' else '30 дней'})"
    
    def deactivate(self):
        """Деактивирует лицензию"""
        self.license_key = None
        self.license_type = None
        self.activated_at = None
        self.is_activated = False
        self.save_license()
    
    def is_valid(self) -> tuple[bool, str]:
        """Проверяет валидность лицензии"""
        if not self.is_activated or not self.license_key:
            return False, "Лицензия не активирована"
        
        if self.license_type == 'lifetime':
            return True, "Бессрочная лицензия"
        
        if self.license_type == 'trial':
            if not self.activated_at:
                return False, "Дата активации не найдена"
            
            try:
                activated = datetime.fromisoformat(self.activated_at)
                days_left = 30 - (datetime.now() - activated).days
                
                if days_left <= 0:
                    return False, f"Срок действия истёк"
                elif days_left <= 7:
                    return True, f"Осталось дней: {days_left} ⚠️"
                else:
                    return True, f"Осталось дней: {days_left}"
            except:
                return False, "Ошибка проверки срока"
        
        return False, "Неизвестный тип лицензии"
    
    def get_license_info(self) -> dict:
        """Возвращает информацию о лицензии"""
        is_valid, message = self.is_valid()
        
        if not is_valid and "не активирована" in message:
            return {
                'status': 'not_activated',
                'message': 'Лицензия не активирована',
                'days_left': None
            }
        
        if self.license_type == 'lifetime':
            return {
                'status': 'lifetime',
                'message': f'✅ Бессрочная лицензия\nКлюч: {self.license_key}',
                'key': self.license_key,
                'days_left': None
            }
        
        if self.license_type == 'trial':
            if self.activated_at:
                activated = datetime.fromisoformat(self.activated_at)
                days_left = 30 - (datetime.now() - activated).days
                expired = days_left <= 0
                
                return {
                    'status': 'expired' if expired else 'trial',
                    'message': f"{'❌ Срок истёк' if expired else '⏳ Пробный период'}\n"
                              f"Ключ: {self.license_key}\n"
                              f"Активирована: {activated.strftime('%Y-%m-%d')}\n"
                              f"{'Истекла: ' + str(activated + timedelta(days=30)).split()[0] if expired else f'Осталось дней: {days_left}'}",
                    'key': self.license_key,
                    'days_left': days_left
                }
        
        return {
            'status': 'unknown',
            'message': message,
            'days_left': None
        }