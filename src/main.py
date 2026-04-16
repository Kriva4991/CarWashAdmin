# src/main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from database import init_db, create_indexes
from license_manager import LicenseManager
from ui.login_dialog import LoginDialog
from ui.main_window import CarWashMainWindow
from ui.theme import get_theme
from database.migrations import migrate_roles_and_permissions
from utils.translator import tr

def main():
    """Точка входа в приложение"""
    print("🚀 Запуск приложения CarWash Admin Pro...")
    
    # Инициализация БД
    init_db()
    create_indexes()

    tr.load_from_db()
   
    migrate_roles_and_permissions()
    
    # Проверка лицензии (без UI)
    license_mgr = LicenseManager()
    license_mgr.load_license()
    is_valid, message = license_mgr.is_valid()
    
    if is_valid:
        print(f"✅ Лицензия: {message}")
    else:
        print(f"⚠️  {message} (демо-режим)")
    
    # Создаём приложение
    app = QApplication(sys.argv)
    app.setApplicationName("CarWash Admin Pro")
    app.setStyle("Fusion")

    # 🔧 ПРИМЕНЯЕМ ТЕМУ (загружаем из БД)
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'theme'")
    row = cursor.fetchone()
    conn.close()
    
    theme = row['value'] if row else 'light'
    app.setStyleSheet(get_theme(theme))
    print(f"🎨 Тема: {theme}")
    
    # Показываем окно входа
    login = LoginDialog()
    if login.exec() != 1:  # Если отменил вход
        sys.exit(0)
    
    current_user = login.current_user
    
    # Создаём главное окно
    window = CarWashMainWindow(current_user=current_user)
    window.show()

    # 🆕 Проверяем обновления при запуске (если включено)
    QTimer.singleShot(1000, lambda: check_updates_on_startup(window))
    
    # 🔧 ПРОВЕРКА ЛИЦЕНЗИИ ПОСЛЕ ЗАПУСКА (с UI)
    QTimer.singleShot(500, lambda: check_license_ui(window, license_mgr))
    
    sys.exit(app.exec())

def check_license_ui(window, license_mgr):
    """Проверяет лицензию и показывает предупреждения/блокировку"""
    is_valid, message = license_mgr.is_valid()
    
    if not is_valid:
        # Лицензия истекла или не активирована
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.critical(
            window, "❌ Лицензия",
            f"{message}\n\n"
            f"Для продолжения работы введите новый лицензионный ключ.\n\n"
            f"📧 ваш@email.com\n"
            f"📱 +7 (XXX) XXX-XX-XX\n\n"
            f"Открыть настройки для активации?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Переключаем на вкладку настроек
            window.tabs.setCurrentIndex(4)
            # Блокируем все вкладки кроме настроек
            for i in range(window.tabs.count()):
                if i != 4:
                    window.tabs.widget(i).setEnabled(False)
        else:
            # Закрываем приложение
            window.close()
    else:
        # Лицензия активна — проверяем сколько дней осталось
        info = license_mgr.get_license_info()
        if info.get('days_left') is not None and 0 < info['days_left'] <= 7:
            # Предупреждение но не блокировка
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                window, "⚠️ Лицензия истекает",
                f"Осталось дней: {info['days_left']}\n\n"
                f"Продлите лицензию чтобы продолжить работу без перерывов.\n"
                f"📧 andreykrivtsov94@gmail.com",
                QMessageBox.StandardButton.Ok
            )

def check_updates_on_startup(window):
    """Проверяет обновления при запуске (если включено в настройках)"""
    from database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'auto_check_updates'")
    row = cursor.fetchone()
    conn.close()
    
    enabled = True
    if row and row['value']:
        enabled = row['value'].lower() == 'true'
    
    if not enabled:
        return
    
    from utils.update_checker import UpdateChecker
    from ui.dialogs.update_dialog import UpdateDialog
    
    checker = UpdateChecker()
    has_update, update_info, error = checker.check_for_updates()
    
    if has_update:
        dialog = UpdateDialog(update_info, window)
        dialog.exec()
        checker.save_last_check()
    elif error:
        # Не показываем ошибку при автопроверке, только логируем
        print(f"⚠️ Ошибка проверки обновлений: {error}")

if __name__ == "__main__":
    main()