# src/logger.py
import logging
import os
from datetime import datetime

# Путь к папке логов
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG_FILE = os.path.join(LOGS_DIR, f'carwash_{datetime.now().strftime("%Y-%m")}.log')

def setup_logger():
    """Настраивает логирование в файл"""
    # Создаём папку logs если нет
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Настраиваем логгер
    logger = logging.getLogger('CarWashAdmin')
    logger.setLevel(logging.INFO)
    
    # Очищаем старые хендлеры
    logger.handlers = []
    
    # Файловый хендлер
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Формат
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Также пишем в консоль (для отладки)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info("🚀 CarWash Admin Pro запущен")
    logger.info("=" * 60)
    
    return logger

# Глобальный логгер
logger = setup_logger()

def log_error(error: Exception, context: str = ""):
    """Записывает ошибку в лог"""
    logger.error(f"{context} | {type(error).__name__}: {error}")

def log_info(message: str):
    """Записывает информацию"""
    logger.info(message)

def log_backup(success: bool, path: str = ""):
    """Записывает событие бэкапа"""
    if success:
        logger.info(f"💾 Бэкап создан: {path}")
    else:
        logger.error(f"💾 Бэкап не создан: {path}")