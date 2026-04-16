# src/utils/translator.py
"""
Система интернационализации (i18n)
"""

import json
import os
from typing import Dict, Any


class Translator:
    """Класс для управления переводами"""
    
    _instance = None
    _translations: Dict[str, Dict[str, Any]] = {}
    _current_language: str = 'ru'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_translations()
        return cls._instance
    
    def _load_translations(self):
        """Загружает файлы переводов"""
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')
        
        for lang in ['ru', 'en']:
            filepath = os.path.join(locales_dir, f'{lang}.json')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)
            except FileNotFoundError:
                print(f"⚠️ Файл перевода не найден: {filepath}")
                self._translations[lang] = {}
    
    def set_language(self, language: str):
        """Устанавливает текущий язык"""
        if language in self._translations:
            self._current_language = language
            # Сохраняем в БД
            self._save_to_db(language)
    
    def get_language(self) -> str:
        """Возвращает текущий язык"""
        return self._current_language
    
    def get_available_languages(self) -> list:
        """Возвращает список доступных языков"""
        return [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en', 'name': 'English'}
        ]
    
    def _save_to_db(self, language: str):
        """Сохраняет выбранный язык в БД"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES ('language', ?)
            """, (language,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Не удалось сохранить язык: {e}")
    
    def load_from_db(self):
        """Загружает язык из БД"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'language'")
            row = cursor.fetchone()
            conn.close()
            
            if row and row['value'] in self._translations:
                self._current_language = row['value']
        except Exception as e:
            print(f"⚠️ Не удалось загрузить язык: {e}")
    
    def translate(self, key: str, default: str = None, **kwargs) -> str:
        """
        Переводит ключ в текущий язык
        
        Args:
            key: Ключ перевода (например, 'orders.title')
            default: Значение по умолчанию, если перевод не найден
            **kwargs: Параметры для подстановки в строку
        
        Returns:
            Переведённая строка
        """
        keys = key.split('.')
        value = self._translations.get(self._current_language, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                value = {}
                break
        
        if not value or isinstance(value, dict):
            result = default or key
        else:
            result = str(value)
        
        # Подставляем параметры
        if kwargs:
            try:
                result = result.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return result
    
    def __call__(self, key: str, default: str = None, **kwargs) -> str:
        """Сокращение для translate()"""
        return self.translate(key, default, **kwargs)


# Глобальный экземпляр
tr = Translator()