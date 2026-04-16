# src/utils/update_checker.py
"""
Модуль проверки и установки обновлений
"""

import json
import os
import sys
import tempfile
from typing import Optional, Tuple
from datetime import datetime
import urllib.request
import urllib.error

# Версия приложения (менять при каждом релизе)
CURRENT_VERSION = "3.0.0"

# URL для проверки обновлений (GitHub)
UPDATE_URL = "https://raw.githubusercontent.com/Kriva4991/CarWashAdmin/main/version.json"


class UpdateInfo:
    """Информация об обновлении"""
    def __init__(self, data: dict):
        self.version = data.get('version', '')
        self.release_date = data.get('release_date', '')
        self.download_url = data.get('download_url', '')
        self.changelog = data.get('changelog', [])
        self.min_required = data.get('min_required', '')
        self.file_size = data.get('file_size', 0)
    
    @property
    def is_newer(self) -> bool:
        """Проверяет, новее ли версия чем текущая"""
        return self._compare_versions(self.version, CURRENT_VERSION) > 0
    
    @property
    def changelog_text(self) -> str:
        """Возвращает список изменений в виде текста"""
        if isinstance(self.changelog, list):
            return "\n".join(f"• {item}" for item in self.changelog)
        return str(self.changelog)
    
    @property
    def formatted_size(self) -> str:
        """Форматированный размер файла"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Сравнивает версии (1 если v1 > v2, -1 если v1 < v2, 0 если равны)"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            return 0
        except:
            return 0


class UpdateChecker:
    """Класс для проверки обновлений"""
    
    def __init__(self):
        self.current_version = CURRENT_VERSION
        self.update_url = UPDATE_URL
        self.timeout = 10  # секунд
    
    def check_for_updates(self) -> Tuple[bool, Optional[UpdateInfo], str]:
        """
        Проверяет наличие обновлений
        
        Returns:
            (has_update, update_info, error_message)
        """
        try:
            # Создаём запрос
            request = urllib.request.Request(
                self.update_url,
                headers={'User-Agent': 'CarWashAdmin-UpdateChecker/1.0'}
            )
            
            # Выполняем запрос
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            update_info = UpdateInfo(data)
            
            if update_info.is_newer:
                return True, update_info, ""
            else:
                return False, None, ""
                
        except urllib.error.URLError as e:
            return False, None, f"Ошибка сети: {e.reason}"
        except json.JSONDecodeError:
            return False, None, "Неверный формат данных обновления"
        except Exception as e:
            return False, None, f"Ошибка проверки: {str(e)}"
    
    def download_update(self, update_info: UpdateInfo, progress_callback=None) -> Tuple[bool, str]:
        """
        Скачивает обновление
        
        Args:
            update_info: Информация об обновлении
            progress_callback: Функция для обновления прогресса (проценты)
            
        Returns:
            (success, filepath_or_error)
        """
        try:
            # Создаём временный файл
            fd, temp_path = tempfile.mkstemp(suffix='.exe')
            os.close(fd)
            
            request = urllib.request.Request(
                update_info.download_url,
                headers={'User-Agent': 'CarWashAdmin-UpdateChecker/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=60) as response:
                total_size = response.length
                downloaded = 0
                
                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent)
            
            return True, temp_path
            
        except Exception as e:
            return False, str(e)
    
    def install_update(self, filepath: str) -> bool:
        """
        Запускает установщик обновления
        
        Args:
            filepath: Путь к скачанному установщику
            
        Returns:
            True если установщик запущен
        """
        try:
            if sys.platform == 'win32':
                os.startfile(filepath)
            else:
                os.system(f'"{filepath}"')
            return True
        except Exception as e:
            print(f"Ошибка запуска установщика: {e}")
            return False
    
    def get_last_check(self) -> Optional[datetime]:
        """Возвращает дату последней проверки обновлений"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'last_update_check'")
            row = cursor.fetchone()
            conn.close()
            
            if row and row['value']:
                return datetime.fromisoformat(row['value'])
        except:
            pass
        return None
    
    def save_last_check(self):
        """Сохраняет дату последней проверки"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES ('last_update_check', ?)
            """, (datetime.now().isoformat(),))
            conn.commit()
            conn.close()
        except:
            pass