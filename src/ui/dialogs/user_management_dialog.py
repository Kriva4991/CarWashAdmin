# src/ui/dialogs/user_management_dialog.py
"""
Диалог управления пользователями (только для админа)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QComboBox, QLineEdit,
    QFormLayout, QCheckBox
)
from PyQt6.QtCore import Qt
from services.user_service import user_service, UserService
from models.user import UserRole


class UserManagementDialog(QDialog):
    """Диалог управления пользователями"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.setWindowTitle("👥 Управление пользователями")
        self.setMinimumSize(800, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = QLabel("👥 Пользователи системы")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px 0;
        """)
        layout.addWidget(header)
        
        # Таблица пользователей
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Логин", "Роль", "Активен", "Последний вход", "Создан"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        # Кнопки действий
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_add.clicked.connect(self.add_user)
        self.btn_add.setStyleSheet(self.get_btn_style("#27ae60"))
        btn_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_edit.setStyleSheet(self.get_btn_style("#3498db"))
        btn_layout.addWidget(self.btn_edit)
        
        self.btn_reset_password = QPushButton("🔑 Сбросить пароль")
        self.btn_reset_password.clicked.connect(self.reset_password)
        self.btn_reset_password.setStyleSheet(self.get_btn_style("#f39c12"))
        btn_layout.addWidget(self.btn_reset_password)
        
        self.btn_toggle_active = QPushButton("🔄 Активировать/Блокировать")
        self.btn_toggle_active.clicked.connect(self.toggle_active)
        self.btn_toggle_active.setStyleSheet(self.get_btn_style("#9b59b6"))
        btn_layout.addWidget(self.btn_toggle_active)
        
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self.delete_user)
        self.btn_delete.setStyleSheet(self.get_btn_style("#e74c3c"))
        btn_layout.addWidget(self.btn_delete)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Кнопка закрытия
        btn_close = QPushButton("❌ Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(self.get_btn_style("#95a5a6"))
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(btn_close)
        layout.addLayout(close_layout)
    
    def get_btn_style(self, color: str) -> str:
        """Стиль для кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """
    
    def darken_color(self, color: str) -> str:
        """Затемняет цвет"""
        color_map = {
            '#27ae60': '#229954',
            '#3498db': '#2980b9',
            '#f39c12': '#d68910',
            '#9b59b6': '#8e44ad',
            '#e74c3c': '#c0392b',
            '#95a5a6': '#7f8c8d',
        }
        return color_map.get(color, color)
    
    def load_users(self):
        """Загружает список пользователей"""
        users = self.user_service.get_all_users()
        
        self.table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user.username))
            
            role_item = QTableWidgetItem(user.role.display_name)
            self.table.setItem(row_idx, 2, role_item)
            
            active_text = "✅ Да" if user.is_active else "❌ Нет"
            active_item = QTableWidgetItem(active_text)
            self.table.setItem(row_idx, 3, active_item)
            
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "—"
            self.table.setItem(row_idx, 4, QTableWidgetItem(last_login))
            
            created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "—"
            self.table.setItem(row_idx, 5, QTableWidgetItem(created))
            
            # Сохраняем ID в строке
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, user.id)
    
    def get_selected_user_id(self) -> int:
        """Возвращает ID выбранного пользователя"""
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    
    def get_selected_username(self) -> str:
        """Возвращает логин выбранного пользователя"""
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 1).text()
    
    def add_user(self):
        """Добавляет нового пользователя"""
        dialog = UserEditDialog(self, mode='add')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_edit.text().strip()
            password = dialog.password_edit.text()
            role = dialog.role_combo.currentData()
            
            user_id = self.user_service.create_user(username, password, role)
            
            if user_id:
                QMessageBox.information(self, "✅ Успешно", f"Пользователь '{username}' создан!")
                self.load_users()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось создать пользователя. Возможно, такой логин уже существует.")
    
    def edit_user(self):
        """Редактирует пользователя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите пользователя!")
            return
        
        user = self.user_service.get_user(user_id)
        if not user:
            return
        
        dialog = UserEditDialog(self, mode='edit', user=user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_edit.text().strip()
            role = dialog.role_combo.currentData()
            
            update_data = {
                'username': username,
                'role': role
            }
            
            if self.user_service.update_user(user_id, update_data):
                QMessageBox.information(self, "✅ Успешно", "Пользователь обновлён!")
                self.load_users()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось обновить пользователя.")
    
    def reset_password(self):
        """Сбрасывает пароль пользователя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите пользователя!")
            return
        
        username = self.get_selected_username()
        
        dialog = ResetPasswordDialog(self, username)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = dialog.password_edit.text()
            
            if self.user_service.change_password(user_id, new_password):
                QMessageBox.information(self, "✅ Успешно", f"Пароль для '{username}' изменён!")
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось изменить пароль.")
    
    def toggle_active(self):
        """Активирует/блокирует пользователя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите пользователя!")
            return
        
        user = self.user_service.get_user(user_id)
        if not user:
            return
        
        # Нельзя заблокировать последнего админа
        if user.role.value == 'admin' and user.is_active:
            active_admins = [u for u in self.user_service.get_all_users() 
                           if u.role.value == 'admin' and u.is_active]
            if len(active_admins) == 1:
                QMessageBox.warning(self, "⚠️ Ошибка", "Нельзя заблокировать последнего администратора!")
                return
        
        new_active = not user.is_active
        action = "активирован" if new_active else "заблокирован"
        
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            f"Вы уверены, что хотите {action} пользователя '{user.username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.user_service.update_user(user_id, {'is_active': 1 if new_active else 0}):
                QMessageBox.information(self, "✅ Успешно", f"Пользователь {action}!")
                self.load_users()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось изменить статус.")
    
    def delete_user(self):
        """Удаляет пользователя"""
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите пользователя!")
            return
        
        username = self.get_selected_username()
        
        # Нельзя удалить самого себя
        current_user = self.user_service.current_user
        if current_user and current_user.id == user_id:
            QMessageBox.warning(self, "⚠️ Ошибка", "Нельзя удалить самого себя!")
            return
        
        # Нельзя удалить последнего админа
        user = self.user_service.get_user(user_id)
        if user and user.role.value == 'admin':
            active_admins = [u for u in self.user_service.get_all_users() 
                           if u.role.value == 'admin' and u.is_active]
            if len(active_admins) == 1:
                QMessageBox.warning(self, "⚠️ Ошибка", "Нельзя удалить последнего администратора!")
                return
        
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            f"Вы уверены, что хотите удалить пользователя '{username}'?\n\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.user_service.delete_user(user_id):
                QMessageBox.information(self, "✅ Успешно", f"Пользователь '{username}' удалён!")
                self.load_users()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось удалить пользователя.")


class UserEditDialog(QDialog):
    """Диалог добавления/редактирования пользователя"""
    
    def __init__(self, parent=None, mode='add', user=None):
        super().__init__(parent)
        self.mode = mode
        self.user = user
        self.setWindowTitle("➕ Новый пользователь" if mode == 'add' else "✏️ Редактировать пользователя")
        self.setFixedSize(400, 300 if mode == 'add' else 250)
        self.setModal(True)
        
        self.setup_ui()
        
        if mode == 'edit' and user:
            self.fill_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Логин
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("логин")
        self.username_edit.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Логин:", self.username_edit)
        
        if self.mode == 'add':
            # Пароль (только при создании)
            self.password_edit = QLineEdit()
            self.password_edit.setPlaceholderText("минимум 4 символа")
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_edit.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
            form_layout.addRow("Пароль:", self.password_edit)
        
        # Роль
        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        
        roles = user_service.get_available_roles()
        for role in roles:
            self.role_combo.addItem(role['label'], role['value'])
        
        form_layout.addRow("Роль:", self.role_combo)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self.validate_and_accept)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def fill_data(self):
        """Заполняет данные для редактирования"""
        self.username_edit.setText(self.user.username)
        
        index = self.role_combo.findData(self.user.role.value)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
    
    def validate_and_accept(self):
        """Проверяет данные и принимает диалог"""
        username = self.username_edit.text().strip()
        
        if not username:
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите логин!")
            return
        
        if len(username) < 3:
            QMessageBox.warning(self, "⚠️ Ошибка", "Логин должен быть не менее 3 символов!")
            return
        
        if self.mode == 'add':
            password = self.password_edit.text()
            if len(password) < 4:
                QMessageBox.warning(self, "⚠️ Ошибка", "Пароль должен быть не менее 4 символов!")
                return
        
        self.accept()


class ResetPasswordDialog(QDialog):
    """Диалог сброса пароля"""
    
    def __init__(self, parent=None, username=""):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"🔑 Сброс пароля: {username}")
        self.setFixedSize(350, 180)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        label = QLabel(f"Введите новый пароль для пользователя '{self.username}':")
        label.setStyleSheet("font-size: 13px;")
        layout.addWidget(label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Новый пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setStyleSheet("padding: 10px; border: 1px solid #bdc3c7; border-radius: 4px;")
        layout.addWidget(self.password_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self.validate_and_accept)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def validate_and_accept(self):
        """Проверяет пароль и принимает диалог"""
        password = self.password_edit.text()
        
        if len(password) < 4:
            QMessageBox.warning(self, "⚠️ Ошибка", "Пароль должен быть не менее 4 символов!")
            return
        
        self.accept()