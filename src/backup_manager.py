# src/backup_manager.py
import os
import shutil
from datetime import datetime, timedelta
from database import DB_PATH, get_connection

class BackupManager:
    """Управление резервным копированием БД"""
    
    def __init__(self):
        self.backup_folder = None
        self.backup_enabled = False
        self.backup_day = 5  # Суббота (0=Пн, 6=Вс)
        self.backup_time = "23:00"
        self.last_backup = None
    
    def load_settings(self):
        """Загружает настройки бэкапа из БД"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Папка для бэкапов
        cursor.execute("SELECT value FROM settings WHERE key = 'backup_folder'")
        row = cursor.fetchone()
        self.backup_folder = row['value'] if row else None
        
        # Включено ли
        cursor.execute("SELECT value FROM settings WHERE key = 'backup_enabled'")
        row = cursor.fetchone()
        self.backup_enabled = row['value'] == '1' if row else False
        
        # День недели
        cursor.execute("SELECT value FROM settings WHERE key = 'backup_day'")
        row = cursor.fetchone()
        self.backup_day = int(row['value']) if row else 5
        
        # Время
        cursor.execute("SELECT value FROM settings WHERE key = 'backup_time'")
        row = cursor.fetchone()
        self.backup_time = row['value'] if row else "23:00"
        
        # Последний бэкап
        cursor.execute("SELECT value FROM settings WHERE key = 'last_backup'")
        row = cursor.fetchone()
        self.last_backup = row['value'] if row else None
        
        conn.close()
    
    def save_settings(self):
        """Сохраняет настройки бэкапа в БД"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # 🔍 ОТЛАДКА
        print(f"💾 Сохранение в БД: backup_enabled = {'1' if self.backup_enabled else '0'}")
        
        settings = [
            ('backup_folder', self.backup_folder or ''),
            ('backup_enabled', '1' if self.backup_enabled else '0'),  # ← Проверь эту строку
            ('backup_day', str(self.backup_day)),
            ('backup_time', self.backup_time),
            ('last_backup', self.last_backup or ''),
        ]
        
        for key, value in settings:
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
            print(f"   {key} = {value}")  # ← Отладка
        
        conn.commit()
        conn.close()
    
    def create_backup(self) -> tuple[bool, str]:
        """Создаёт резервную копию БД"""
        try:
            if not self.backup_folder:
                return False, "Не указана папка для бэкапов"
            
            # Создаём папку если нет
            os.makedirs(self.backup_folder, exist_ok=True)
            
            # Имя файла с датой
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'carwash_backup_{timestamp}.db'
            backup_path = os.path.join(self.backup_folder, backup_filename)
            
            # Копируем файл БД
            shutil.copy2(DB_PATH, backup_path)
            
            # Обновляем последний бэкап
            self.last_backup = datetime.now().isoformat()
            self.save_settings()
            
            # Удаляем старые бэкапы (> 30 дней)
            self.cleanup_old_backups()
            
            return True, backup_path
            
        except Exception as e:
            return False, str(e)
    
    def cleanup_old_backups(self, days: int = 30):
        """Удаляет бэкапы старше N дней"""
        if not os.path.exists(self.backup_folder):
            return
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(self.backup_folder):
            if filename.startswith('carwash_backup_') and filename.endswith('.db'):
                filepath = os.path.join(self.backup_folder, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff:
                    os.remove(filepath)
                    print(f"🗑️ Удалён старый бэкап: {filename}")
    
    def should_backup_now(self) -> bool:
        """Проверяет, нужно ли делать бэкап сейчас"""
        if not self.backup_enabled:
            return False
        
        if not self.backup_folder:
            return False
        
        now = datetime.now()
        
        # Проверяем день недели
        if now.weekday() != self.backup_day:
            return False
        
        # Проверяем время (с точностью до минуты)
        try:
            backup_hour, backup_minute = map(int, self.backup_time.split(':'))
            if now.hour == backup_hour and now.minute == backup_minute:
                # Проверяем что ещё не делали бэкап сегодня
                if self.last_backup:
                    last = datetime.fromisoformat(self.last_backup)
                    if last.date() == now.date():
                        return False
                return True
        except:
            pass
        
        return False
    
    def get_last_backup_info(self) -> dict:
        """Возвращает информацию о последнем бэкапе"""
        if not self.last_backup:
            return {'status': 'never', 'message': 'Бэкап ещё не делался'}
        
        try:
            last = datetime.fromisoformat(self.last_backup)
            days_ago = (datetime.now() - last).days
            
            if days_ago == 0:
                return {'status': 'ok', 'message': f'Сегодня в {last.strftime("%H:%M")}'}
            elif days_ago == 1:
                return {'status': 'warning', 'message': 'Вчера'}
            elif days_ago < 7:
                return {'status': 'warning', 'message': f'{days_ago} дн. назад'}
            else:
                return {'status': 'critical', 'message': f'{days_ago} дн. назад (тревога!)'}
        except:
            return {'status': 'error', 'message': 'Ошибка чтения даты'}
    
    def is_configured(self) -> bool:
        """Проверяет, настроен ли бэкап"""
        return self.backup_enabled and bool(self.backup_folder)