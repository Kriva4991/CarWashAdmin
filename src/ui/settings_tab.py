# src/ui/settings_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox, QScrollArea,
    QMessageBox, QFileDialog, QComboBox, QTextEdit, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from database import get_connection
import bcrypt
import os
from ui.dialogs.user_management_dialog import UserManagementDialog
from services.user_service import user_service
from utils.translator import tr
from utils.update_checker import UpdateChecker
from ui.dialogs.update_dialog import UpdateDialog

class SettingsTab(QWidget):
    def __init__(self, parent=None, current_user="admin"):
        super().__init__(parent)
        self.current_user = current_user
        self.user = user_service.current_user
        self.setup_ui()
        self.load_settings()
        self.load_backup_settings()
        self.load_license_settings()
        self.load_update_settings()
    
    def setup_ui(self):
        # Создаем прокрутку для больших экранов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Основной виджет
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = QLabel(tr("settings.title"))
        header.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            padding: 15px;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
        """)
        main_layout.addWidget(header)

        # === ГРУППА: РЕЗЕРВНОЕ КОПИРОВАНИЕ ===
        backup_group = self.create_group(tr("settings.backup"))
        backup_layout = QVBoxLayout()
        
        # Включить автобэкап
        self.backup_enabled_check = QCheckBox(tr("settings.backup_enable"))
        self.backup_enabled_check.setStyleSheet("font-size: 14px; padding: 5px;")
        backup_layout.addWidget(self.backup_enabled_check)
        
        # Папка для бэкапов
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel(tr("settings.backup_folder") + ":"))
        self.backup_folder_edit = QLineEdit()
        self.backup_folder_edit.setPlaceholderText("C:\\Backups\\Carwash")
        self.backup_folder_edit.setStyleSheet(self.get_input_style())
        folder_layout.addWidget(self.backup_folder_edit)
        
        btn_browse = QPushButton(tr("settings.browse"))
        btn_browse.setFixedWidth(100)
        btn_browse.clicked.connect(self.browse_backup_folder)
        btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        folder_layout.addWidget(btn_browse)
        backup_layout.addLayout(folder_layout)
        
        # День и время
        schedule_layout = QHBoxLayout()
        schedule_layout.addWidget(QLabel(tr("settings.day") + ":"))
        
        self.backup_day_combo = QComboBox()
        self.backup_day_combo.addItems([
            "Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"
        ])
        self.backup_day_combo.setCurrentIndex(5)  # Суббота
        self.backup_day_combo.setFixedWidth(80)
        schedule_layout.addWidget(self.backup_day_combo)
        
        schedule_layout.addWidget(QLabel(tr("settings.time") + ":"))
        self.backup_time_edit = QLineEdit()
        self.backup_time_edit.setPlaceholderText("23:00")
        self.backup_time_edit.setFixedWidth(80)
        schedule_layout.addWidget(self.backup_time_edit)
        schedule_layout.addStretch()
        backup_layout.addLayout(schedule_layout)
        
        # Информация о последнем бэкапе
        self.last_backup_label = QLabel(tr("settings.last_backup") + ": " + tr("common.unknown", default="неизвестно"))
        self.last_backup_label.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 10px 0;")
        backup_layout.addWidget(self.last_backup_label)
        
        # Кнопки
        backup_btn_layout = QHBoxLayout()
        backup_btn_layout.addStretch()
        
        self.btn_backup_now = QPushButton(tr("settings.backup_now"))
        self.btn_backup_now.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_backup_now.clicked.connect(self.create_backup_now)
        backup_btn_layout.addWidget(self.btn_backup_now)
        
        self.btn_save_backup = QPushButton(tr("settings.save"))
        self.btn_save_backup.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.btn_save_backup.clicked.connect(self.save_backup_settings)
        backup_btn_layout.addWidget(self.btn_save_backup)
        
        backup_layout.addLayout(backup_btn_layout)
        backup_group.layout().addLayout(backup_layout)
        main_layout.addWidget(backup_group)

        # === ГРУППА: АВТООБНОВЛЕНИЕ ===
        update_group = self.create_group("🔄 Автообновление")
        update_layout = QVBoxLayout()
        
        # Включить проверку обновлений
        self.update_check_enabled = QCheckBox("🔍 Проверять обновления при запуске")
        self.update_check_enabled.setStyleSheet("font-size: 14px; padding: 5px;")
        self.update_check_enabled.setChecked(True)
        update_layout.addWidget(self.update_check_enabled)
        
        # Информация о версии
        version_info = QLabel(f"Текущая версия: {UpdateChecker().current_version}")
        version_info.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 5px 0;")
        update_layout.addWidget(version_info)
        
        # Последняя проверка
        self.last_check_label = QLabel("Последняя проверка: —")
        self.last_check_label.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 5px 0;")
        update_layout.addWidget(self.last_check_label)
        
        # Кнопки
        update_btn_layout = QHBoxLayout()
        update_btn_layout.addStretch()
        
        self.btn_check_updates = QPushButton("🔍 Проверить обновления")
        self.btn_check_updates.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_check_updates.clicked.connect(self.check_for_updates)
        update_btn_layout.addWidget(self.btn_check_updates)
        
        self.btn_save_update = QPushButton("💾 Сохранить настройки")
        self.btn_save_update.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.btn_save_update.clicked.connect(self.save_update_settings)
        update_btn_layout.addWidget(self.btn_save_update)
        
        update_layout.addLayout(update_btn_layout)
        update_group.layout().addLayout(update_layout)
        main_layout.addWidget(update_group)

        # --- ПОЛЬЗОВАТЕЛИ (только для админа) ---
        if self.user and self.user.role.value == 'admin':
            users_group = self.create_group(tr("settings.users"))
            users_layout = QVBoxLayout()
            
            users_info = QLabel(tr("settings.users_desc"))
            users_info.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 5px 0;")
            users_layout.addWidget(users_info)
            
            btn_manage_users = QPushButton(tr("settings.manage_users"))
            btn_manage_users.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn_manage_users.clicked.connect(self.open_user_management)
            users_layout.addWidget(btn_manage_users)
            
            btn_audit_log = QPushButton(tr("settings.audit_log"))
            btn_audit_log.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            btn_audit_log.clicked.connect(self.open_audit_log)
            users_layout.addWidget(btn_audit_log)
            
            users_group.layout().addLayout(users_layout)
            main_layout.addWidget(users_group)
        
                # --- ТЕСТОВЫЕ ДАННЫЕ (только для админа) ---
        if self.user and self.user.role.value == 'admin':
            test_data_group = self.create_group("🧪 Тестовые данные")
            test_data_layout = QVBoxLayout()
            
            test_info = QLabel("Генерация демонстрационных данных для тестирования")
            test_info.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 5px 0;")
            test_data_layout.addWidget(test_info)
            
            btn_generate = QPushButton("🚀 Сгенерировать тестовые данные")
            btn_generate.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
            btn_generate.clicked.connect(self.generate_test_data)
            test_data_layout.addWidget(btn_generate)
            
            test_data_group.layout().addLayout(test_data_layout)
            main_layout.addWidget(test_data_group)
        
        # --- КОМПАНИЯ ---
        if self.user and self.user.has_permission('edit_settings'):
            company_group = self.create_group(tr("settings.company"))
            company_layout = QGridLayout()
            company_layout.setSpacing(10)
            
            company_layout.addWidget(QLabel(tr("settings.company_name") + ":"), 0, 0)
            self.company_name_edit = QLineEdit()
            self.company_name_edit.setPlaceholderText(tr("settings.company_name_placeholder", default="Например: Автомойка №1"))
            self.company_name_edit.setStyleSheet(self.get_input_style())
            self.company_name_edit.setFixedWidth(400)
            company_layout.addWidget(self.company_name_edit, 0, 1)
            
            company_layout.addWidget(QLabel(tr("settings.phone") + ":"), 1, 0)
            self.company_phone_edit = QLineEdit()
            self.company_phone_edit.setPlaceholderText("+7 (999) 000-00-00")
            self.company_phone_edit.setStyleSheet(self.get_input_style())
            self.company_phone_edit.setFixedWidth(400)
            company_layout.addWidget(self.company_phone_edit, 1, 1)
            
            company_layout.addWidget(QLabel(tr("settings.address") + ":"), 2, 0)
            self.company_address_edit = QTextEdit()
            self.company_address_edit.setPlaceholderText(tr("settings.address_placeholder", default="г. Москва, ул. Примерная, д. 1"))
            self.company_address_edit.setStyleSheet(self.get_textarea_style())
            self.company_address_edit.setMaximumHeight(60)
            self.company_address_edit.setFixedWidth(400)
            company_layout.addWidget(self.company_address_edit, 2, 1)
            
            company_layout.addWidget(QLabel(tr("settings.website") + ":"), 3, 0)
            self.company_website_edit = QLineEdit()
            self.company_website_edit.setPlaceholderText("www.example.ru")
            self.company_website_edit.setStyleSheet(self.get_input_style())
            self.company_website_edit.setFixedWidth(400)
            company_layout.addWidget(self.company_website_edit, 3, 1)
            
            company_layout.addWidget(QLabel(tr("settings.logo") + ":"), 4, 0)
            logo_layout = QHBoxLayout()
            self.logo_path_edit = QLineEdit()
            self.logo_path_edit.setPlaceholderText("Путь к файлу логотипа")
            self.logo_path_edit.setStyleSheet(self.get_input_style())
            self.logo_path_edit.setFixedWidth(300)
            logo_layout.addWidget(self.logo_path_edit)
            
            self.btn_browse_logo = QPushButton(tr("settings.browse"))
            self.btn_browse_logo.setFixedWidth(100)
            self.btn_browse_logo.clicked.connect(self.browse_logo)
            self.btn_browse_logo.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    padding: 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            logo_layout.addWidget(self.btn_browse_logo)
            company_layout.addLayout(logo_layout, 4, 1)
            
            # Кнопка сохранения
            btn_save_layout = QHBoxLayout()
            btn_save_layout.addStretch()
            self.btn_save_company = QPushButton(tr("settings.save"))
            self.btn_save_company.setFixedWidth(250)
            self.btn_save_company.clicked.connect(self.save_company_settings)
            self.btn_save_company.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    padding: 12px 25px;
                    font-weight: bold;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            btn_save_layout.addWidget(self.btn_save_company)
            company_layout.addLayout(btn_save_layout, 5, 0, 1, 2)
            
            company_group.layout().addLayout(company_layout)
            main_layout.addWidget(company_group)
        
        # --- ОФОРМЛЕНИЕ И ЯЗЫК ---
        theme_group = self.create_group(tr("settings.theme"))
        theme_main_layout = QVBoxLayout()
        
        # Тема
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel(tr("settings.theme") + ":"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([tr("settings.theme_light"), tr("settings.theme_dark")])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        self.theme_combo.setStyleSheet(self.get_input_style())
        self.theme_combo.setFixedWidth(200)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        theme_main_layout.addLayout(theme_layout)
        
        # Язык
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel(tr("settings.language") + ":"))
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("settings.language_ru"), "ru")
        self.language_combo.addItem(tr("settings.language_en"), "en")
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.language_combo.setStyleSheet(self.get_input_style())
        self.language_combo.setFixedWidth(200)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        theme_main_layout.addLayout(language_layout)
        
        theme_group.layout().addLayout(theme_main_layout)
        main_layout.addWidget(theme_group)

        # === ГРУППА: ЛИЦЕНЗИЯ ===
        if self.user and self.user.role.value == 'admin':
            license_group = self.create_group(tr("settings.license"))
            license_layout = QVBoxLayout()
            
            # Информация о лицензии
            self.license_info_label = QLabel(tr("common.loading"))
            self.license_info_label.setStyleSheet("font-size: 13px; color: #7f8c8d; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
            self.license_info_label.setWordWrap(True)
            license_layout.addWidget(self.license_info_label)
            
            # Поле ввода ключа
            key_layout = QHBoxLayout()
            key_layout.addWidget(QLabel(tr("settings.license_key", default="Ключ активации") + ":"))
            
            self.license_key_edit = QLineEdit()
            self.license_key_edit.setPlaceholderText("CW-30-XXXX-XXXX или CW-LIFE-XXXX-XXXX")
            self.license_key_edit.setStyleSheet(self.get_input_style())
            self.license_key_edit.setMaxLength(23)  # CW-LIFE-XXXX-XXXXXXXX = 23 символа
            key_layout.addWidget(self.license_key_edit)
            
            license_layout.addLayout(key_layout)
            
            # Кнопки
            license_btn_layout = QHBoxLayout()
            license_btn_layout.addStretch()
            
            self.btn_activate_license = QPushButton(tr("settings.activate", default="✅ Активировать"))
            self.btn_activate_license.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white;
                    padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            self.btn_activate_license.clicked.connect(self.activate_license)
            license_btn_layout.addWidget(self.btn_activate_license)
            
            self.btn_deactivate_license = QPushButton(tr("settings.deactivate", default="❌ Деактивировать"))
            self.btn_deactivate_license.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c; color: white;
                    padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            self.btn_deactivate_license.clicked.connect(self.deactivate_license)
            license_btn_layout.addWidget(self.btn_deactivate_license)
            
            license_layout.addLayout(license_btn_layout)
            license_group.layout().addLayout(license_layout)
            main_layout.addWidget(license_group)
        
        # --- О ПРОГРАММЕ ---
        info_group = self.create_group(tr("settings.about"))
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"<b>{tr('settings.about_text')}</b>"))
        info_layout.addWidget(QLabel(f"{tr('app.version')}: 3.0"))
        info_layout.addWidget(QLabel(tr("settings.copyright")))
        info_group.layout().addLayout(info_layout)
        main_layout.addWidget(info_group)
        
        main_layout.addStretch()
        
        scroll.setWidget(main_widget)
        
        # Основной layout
        main_container = QVBoxLayout(self)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.addWidget(scroll)
    
    def create_group(self, title):
        """Создает стилизованную группу"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #2980b9;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)
        return group
    
    def get_input_style(self):
        """Стиль для полей ввода"""
        return """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QLineEdit:hover {
                border: 1px solid #95a5a6;
            }
        """
    
    def get_textarea_style(self):
        """Стиль для текстовой области"""
        return """
            QTextEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
        """
    
    def load_settings(self):
        """Загружает настройки из БД"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        
        # Заполняем поля только если они существуют
        if hasattr(self, 'company_name_edit'):
            self.company_name_edit.setText(settings.get('company_name', 'Автомойка'))
        if hasattr(self, 'company_phone_edit'):
            self.company_phone_edit.setText(settings.get('company_phone', ''))
        if hasattr(self, 'company_address_edit'):
            self.company_address_edit.setText(settings.get('company_address', ''))
        if hasattr(self, 'company_website_edit'):
            self.company_website_edit.setText(settings.get('company_website', ''))
        if hasattr(self, 'logo_path_edit'):
            self.logo_path_edit.setText(settings.get('logo_path', ''))       
        if hasattr(self, 'theme_combo'):
            theme = settings.get('theme', 'light')
            self.theme_combo.setCurrentIndex(0 if theme == 'light' else 1)
        # 🆕 Загружаем язык
        if hasattr(self, 'language_combo'):
            language = settings.get('language', 'ru')
            index = self.language_combo.findData(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

        self.load_update_settings()
    
    def change_password(self):
        """Смена пароля текущего пользователя"""
        current = self.current_password_edit.text().strip()
        new = self.new_password_edit.text().strip()
        confirm = self.confirm_password_edit.text().strip()
        
        if not current or not new or not confirm:
            QMessageBox.warning(self, "⚠️ Ошибка", "Заполните все поля!")
            return
        
        if new != confirm:
            QMessageBox.warning(self, "⚠️ Ошибка", "Новые пароли не совпадают!")
            return
        
        if len(new) < 6:
            QMessageBox.warning(self, "⚠️ Ошибка", "Пароль должен быть не менее 6 символов!")
            return
        
        # Проверяем текущий пароль
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (self.current_user,))
        row = cursor.fetchone()
        
        if not row or not bcrypt.checkpw(current.encode(), row['password_hash'].encode()):
            QMessageBox.critical(self, "❌ Ошибка", "Неверный текущий пароль!")
            conn.close()
            return
        
        # Обновляем пароль
        new_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt())
        cursor.execute("""
            UPDATE users 
            SET password_hash = ? 
            WHERE username = ?
        """, (new_hash.decode(), self.current_user))
        conn.commit()
        conn.close()
        
        # Очищаем поля
        self.current_password_edit.clear()
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()
        
        QMessageBox.information(self, "✅ Успешно", "Пароль успешно изменён!")
    
    def save_company_settings(self):
        """Сохраняет настройки компании"""
        if not hasattr(self, 'company_name_edit'):
            return
        
        settings = {
            'company_name': self.company_name_edit.text().strip(),
            'company_phone': self.company_phone_edit.text().strip(),
            'company_address': self.company_address_edit.toPlainText().strip(),
            'company_website': self.company_website_edit.text().strip(),
            'logo_path': self.logo_path_edit.text().strip(),
        }
        
        conn = get_connection()
        cursor = conn.cursor()
        for key, value in settings.items():
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "✅ Успешно", "Настройки компании сохранены!")
    
    def browse_logo(self):
        """Выбор файла логотипа"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите логотип",
            "",
            "Изображения (*.png *.jpg *.jpeg *.ico)"
        )
        
        if filepath:
            self.logo_path_edit.setText(filepath)
    
    def change_theme(self, index):
        """Смена темы оформления"""
        if not hasattr(self, 'theme_combo'):
            return
        theme = 'light' if index == 0 else 'dark'
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, ('theme', theme))
        conn.commit()
        conn.close()
        
        # Применяем тему (базовая реализация)
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: white; }
                QGroupBox { border: 1px solid #555; }
            """)
        else:
            self.setStyleSheet("")

    def browse_backup_folder(self):
        """Выбор папки для бэкапов"""
        folder = QFileDialog.getExistingDirectory(
            self, "📁 Выберите папку для бэкапов"
        )
        if folder:
            self.backup_folder_edit.setText(folder)
    
    def load_backup_settings(self):
        """Загружает настройки бэкапа из БД"""
        from backup_manager import BackupManager
        
        self.backup_manager = BackupManager()
        self.backup_manager.load_settings()
        
        # Заполняем поля только если они существуют
        if hasattr(self, 'backup_enabled_check'):
            self.backup_enabled_check.setChecked(self.backup_manager.backup_enabled)
        if hasattr(self, 'backup_folder_edit'):
            self.backup_folder_edit.setText(self.backup_manager.backup_folder or '')
        if hasattr(self, 'backup_day_combo'):
            self.backup_day_combo.setCurrentIndex(self.backup_manager.backup_day)
        if hasattr(self, 'backup_time_edit'):
            self.backup_time_edit.setText(self.backup_manager.backup_time)
        
        # Информация о последнем бэкапе
        if hasattr(self, 'last_backup_label'):
            info = self.backup_manager.get_last_backup_info()
            self.last_backup_label.setText(f"ℹ️ Последний бэкап: {info['message']}")
            
            # Цвет статуса
            if info['status'] == 'ok':
                self.last_backup_label.setStyleSheet("color: #27ae60;")
            elif info['status'] == 'warning':
                self.last_backup_label.setStyleSheet("color: #f39c12;")
            elif info['status'] == 'critical':
                self.last_backup_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def save_backup_settings(self):
        """Сохраняет настройки бэкапа"""
        from backup_manager import BackupManager
        from logger import log_info
        
        # 🔍 ОТЛАДКА: проверь что читается
        is_enabled = self.backup_enabled_check.isChecked()
        print(f"🔧 Сохранение бэкапа: enabled={is_enabled}")
        
        # Валидация времени
        time_text = self.backup_time_edit.text().strip()
        try:
            hour, minute = map(int, time_text.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            QMessageBox.warning(
                self, "⚠️ Ошибка",
                "Неверный формат времени! Используйте ЧЧ:ММ (например, 23:00)"
            )
            return
        
        # Сохраняем
        self.backup_manager = BackupManager()
        self.backup_manager.load_settings()  # ← Загружаем текущие
        
        # 🔧 Устанавливаем значения ПЕРЕД сохранением
        self.backup_manager.backup_enabled = is_enabled
        self.backup_manager.backup_folder = self.backup_folder_edit.text().strip()
        self.backup_manager.backup_day = self.backup_day_combo.currentIndex()
        self.backup_manager.backup_time = time_text
        
        # 🔍 ОТЛАДКА: проверь что сохраняется
        print(f"   backup_enabled перед save: {self.backup_manager.backup_enabled}")
        
        self.backup_manager.save_settings()
        
        log_info("Настройки бэкапа сохранены")
        
        QMessageBox.information(
            self, "✅ Успешно",
            "Настройки резервного копирования сохранены!"
        )
        self.load_backup_settings()
    
    def create_backup_now(self):
        """Создаёт бэкап прямо сейчас"""
        from backup_manager import BackupManager
        from logger import log_backup
        
        self.backup_manager = BackupManager()
        self.backup_manager.load_settings()
        
        if not self.backup_manager.backup_folder:
            QMessageBox.warning(
                self, "⚠️ Ошибка",
                "Сначала укажите папку для бэкапов!"
            )
            return
        
        success, path = self.backup_manager.create_backup()
        log_backup(success, path)
        
        if success:
            QMessageBox.information(
                self, "✅ Бэкап создан",
                f"Резервная копия создана:\n{path}"
            )
            self.load_backup_settings()
        else:
            QMessageBox.critical(
                self, "❌ Ошибка",
                f"Не удалось создать бэкап:\n{path}"
            )

    def load_license_settings(self):
        """Загружает информацию о лицензии"""
        from license_manager import LicenseManager
        
        self.license_manager = LicenseManager()
        self.license_manager.load_license()
        
        info = self.license_manager.get_license_info()
        
        if not hasattr(self, 'license_info_label'):
            return
        
        # 🆕 Скрываем ключ, показываем только маску
        if info['status'] == 'lifetime':
            # Показываем только тип лицензии, ключ скрыт
            masked_key = self._mask_license_key(info.get('key', ''))
            display_text = f"✅ Бессрочная лицензия\nКлюч: {masked_key}"
            
            self.license_info_label.setText(display_text)
            self.license_info_label.setStyleSheet(
                "font-size: 13px; color: #27ae60; padding: 10px; "
                "background-color: #e8f5e9; border-radius: 5px;"
            )
            if hasattr(self, 'license_key_edit'):
                self.license_key_edit.setEnabled(False)
            if hasattr(self, 'btn_activate_license'):
                self.btn_activate_license.setEnabled(False)
            if hasattr(self, 'btn_deactivate_license'):
                self.btn_deactivate_license.setEnabled(True)
            
        elif info['status'] == 'trial':
            masked_key = self._mask_license_key(info.get('key', ''))
            days_left = info.get('days_left', 0)
            
            if days_left <= 7:
                color = "#e74c3c"
                bg = "#fdedec"
                status_text = "⚠️ Пробный период"
            else:
                color = "#f39c12"
                bg = "#fef9e7"
                status_text = "⏳ Пробный период"
            
            display_text = f"{status_text}\nКлюч: {masked_key}\nОсталось дней: {days_left}"
            
            self.license_info_label.setText(display_text)
            self.license_info_label.setStyleSheet(
                f"font-size: 13px; color: {color}; padding: 10px; "
                f"background-color: {bg}; border-radius: 5px;"
            )
            if hasattr(self, 'license_key_edit'):
                self.license_key_edit.setEnabled(False)
            if hasattr(self, 'btn_activate_license'):
                self.btn_activate_license.setEnabled(False)
            if hasattr(self, 'btn_deactivate_license'):
                self.btn_deactivate_license.setEnabled(True)
            
        elif info['status'] == 'expired':
            self.license_info_label.setText(info['message'])
            self.license_info_label.setStyleSheet(
                "font-size: 13px; color: #e74c3c; padding: 10px; "
                "background-color: #fdedec; border-radius: 5px;"
            )
            if hasattr(self, 'license_key_edit'):
                self.license_key_edit.setEnabled(True)
            if hasattr(self, 'btn_activate_license'):
                self.btn_activate_license.setEnabled(True)
            if hasattr(self, 'btn_deactivate_license'):
                self.btn_deactivate_license.setEnabled(False)
            
        else:
            self.license_info_label.setText(f"ℹ️ {info['message']}")
            self.license_info_label.setStyleSheet(
                "font-size: 13px; color: #7f8c8d; padding: 10px; "
                "background-color: #f8f9fa; border-radius: 5px;"
            )
            if hasattr(self, 'license_key_edit'):
                self.license_key_edit.setEnabled(True)
            if hasattr(self, 'btn_activate_license'):
                self.btn_activate_license.setEnabled(True)
            if hasattr(self, 'btn_deactivate_license'):
                self.btn_deactivate_license.setEnabled(False)
    
    def _mask_license_key(self, key: str) -> str:
        """Маскирует лицензионный ключ, показывая только первые и последние символы"""
        if not key:
            return "—"
        
        parts = key.split('-')
        if len(parts) >= 5:
            # CW-LIFE-XXXX-XXXX-CCCC -> CW-LIFE-****-****-CCCC
            return f"{parts[0]}-{parts[1]}-****-****-{parts[4]}"
        elif len(key) > 8:
            # Показываем первые 4 и последние 4 символа
            return f"{key[:4]}...{key[-4:]}"
        else:
            return "****"
    
    def activate_license(self):
        """Активирует лицензию"""
        from license_manager import LicenseManager
        
        key = self.license_key_edit.text().strip()
        
        if not key:
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите лицензионный ключ!")
            return
        
        self.license_manager = LicenseManager()
        success, message = self.license_manager.activate(key)
        
        if success:
            QMessageBox.information(self, "✅ Успешно", message)
            self.load_license_settings()
            
            # 🔧 РАЗБЛОКИРУЕМ ИНТЕРФЕЙС ЕСЛИ БЫЛ ЗАБЛОКИРОВАН
            if self.parent_window and hasattr(self.parent_window, 'tabs'):
                for i in range(self.parent_window.tabs.count()):
                    self.parent_window.tabs.widget(i).setEnabled(True)
                self.parent_window.tabs.setCurrentIndex(0)  # Возвращаем на заказы
                self.parent_window.statusBar().showMessage("✅ Лицензия активирована", 3000)
        else:
            QMessageBox.critical(self, "❌ Ошибка", message)
    
    def deactivate_license(self):
        """Деактивирует лицензию"""
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            "Вы уверены, что хотите деактивировать лицензию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from license_manager import LicenseManager
            
            self.license_manager = LicenseManager()
            self.license_manager.deactivate()
            
            QMessageBox.information(self, "✅ Деактивировано", "Лицензия деактивирована!")
            self.load_license_settings()

    def open_user_management(self):
        """Открывает диалог управления пользователями"""
        dialog = UserManagementDialog(self)
        dialog.exec()
    
    def open_audit_log(self):
        """Открывает журнал аудита"""
        from ui.dialogs.audit_log_dialog import AuditLogDialog
        dialog = AuditLogDialog(self)
        dialog.exec()

    def change_language(self, index):
        """Меняет язык интерфейса"""
        language = self.language_combo.currentData()
        tr.set_language(language)
        
        QMessageBox.information(
            self, 
            tr("common.success"), 
            tr("settings.language_changed", default="Язык изменён. Перезапустите программу для применения всех изменений.")
        )

    def load_update_settings(self):
        """Загружает настройки автообновления"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        
        # Загружаем настройку проверки обновлений
        if hasattr(self, 'update_check_enabled'):
            enabled = settings.get('auto_check_updates', 'true').lower() == 'true'
            self.update_check_enabled.setChecked(enabled)
        
        # Обновляем информацию о последней проверке
        self.update_last_check_info()
    
    def update_last_check_info(self):
        """Обновляет информацию о последней проверке"""
        if hasattr(self, 'last_check_label'):
            checker = UpdateChecker()
            last_check = checker.get_last_check()
            if last_check:
                self.last_check_label.setText(f"Последняя проверка: {last_check.strftime('%d.%m.%Y %H:%M')}")
            else:
                self.last_check_label.setText("Последняя проверка: —")
    
    def save_update_settings(self):
        """Сохраняет настройки автообновления"""
        conn = get_connection()
        cursor = conn.cursor()
        
        enabled = 'true' if self.update_check_enabled.isChecked() else 'false'
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES ('auto_check_updates', ?)
        """, (enabled,))
        
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "✅ Успешно", "Настройки автообновления сохранены!")
    
    def check_for_updates(self):
        """Проверяет наличие обновлений"""
        self.btn_check_updates.setEnabled(False)
        self.btn_check_updates.setText("⏳ Проверка...")
        
        checker = UpdateChecker()
        has_update, update_info, error = checker.check_for_updates()
        
        self.btn_check_updates.setEnabled(True)
        self.btn_check_updates.setText("🔍 Проверить обновления")
        
        if error:
            QMessageBox.warning(
                self,
                "⚠️ Ошибка проверки",
                f"Не удалось проверить обновления:\n{error}"
            )
        elif has_update:
            dialog = UpdateDialog(update_info, self)
            dialog.exec()
            checker.save_last_check()
            self.update_last_check_info()
        else:
            checker.save_last_check()
            self.update_last_check_info()
            QMessageBox.information(
                self,
                "✅ Обновлений нет",
                f"У вас установлена последняя версия ({checker.current_version})!"
            )

    def generate_test_data(self):
        """Генерирует тестовые данные"""
        reply = QMessageBox.question(
            self,
            "🧪 Генерация тестовых данных",
            "Будут созданы тестовые клиенты и заказы.\n\n"
            "Существующие данные НЕ будут удалены.\n"
            "Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from utils.test_data_generator import TestDataGenerator
            
            generator = TestDataGenerator()
            generator.generate_all(clients=30, orders=100)
            generator.close()
            
            QMessageBox.information(
                self,
                "✅ Готово",
                "Тестовые данные успешно сгенерированы!\n\n"
                "Создано:\n"
                "👤 30 клиентов\n"
                "📋 100 заказов\n"
                "🧴 Списания расходников\n\n"
                "Перезайдите во вкладки для обновления."
            )