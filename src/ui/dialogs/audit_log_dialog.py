# src/ui/dialogs/audit_log_dialog.py
"""
Диалог просмотра журнала аудита
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt
from services.user_service import user_service


class AuditLogDialog(QDialog):
    """Диалог просмотра журнала аудита"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.setWindowTitle("📋 Журнал аудита")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = QLabel("📋 Журнал действий")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px 0;
        """)
        layout.addWidget(header)
        
        # Фильтры
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр по пользователю:"))
        
        self.user_filter = QComboBox()
        self.user_filter.addItem("Все пользователи", None)
        
        users = self.user_service.get_all_users()
        for user in users:
            self.user_filter.addItem(user.username, user.id)
        
        self.user_filter.currentIndexChanged.connect(self.load_logs)
        self.user_filter.setStyleSheet("padding: 6px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.user_filter)
        
        filter_layout.addWidget(QLabel("Действие:"))
        self.action_filter = QLineEdit()
        self.action_filter.setPlaceholderText("login, create_order...")
        self.action_filter.textChanged.connect(self.load_logs)
        self.action_filter.setStyleSheet("padding: 6px; border: 1px solid #bdc3c7; border-radius: 4px;")
        filter_layout.addWidget(self.action_filter)
        
        filter_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.load_logs)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        filter_layout.addWidget(btn_refresh)
        
        layout.addLayout(filter_layout)
        
        # Таблица логов
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Время", "Пользователь", "Действие", "Тип", "Детали"
        ])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        # Кнопка закрытия
        btn_close = QPushButton("❌ Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
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
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(btn_close)
        layout.addLayout(close_layout)
    
    def load_logs(self):
        """Загружает логи с учётом фильтров"""
        logs = self.user_service.get_audit_logs(limit=500)
        
        # Применяем фильтры
        user_id = self.user_filter.currentData()
        action_filter = self.action_filter.text().strip().lower()
        
        filtered_logs = []
        for log in logs:
            if user_id and log.user_id != user_id:
                continue
            if action_filter and action_filter not in log.action.lower():
                continue
            filtered_logs.append(log)
        
        self.table.setRowCount(len(filtered_logs))
        
        action_names = {
            'login': '🔐 Вход',
            'logout': '🚪 Выход',
            'login_failed': '❌ Ошибка входа',
            'create_order': '📝 Создание заказа',
            'edit_order': '✏️ Изменение заказа',
            'delete_order': '🗑️ Удаление заказа',
            'change_order_status': '🔄 Смена статуса',
            'create_user': '👤 Создание пользователя',
            'update_user': '✏️ Обновление пользователя',
            'delete_user': '🗑️ Удаление пользователя',
            'change_password': '🔑 Смена пароля',
            'permission_denied': '⛔ Доступ запрещён',
        }
        
        for row_idx, log in enumerate(filtered_logs):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(log.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(log.username))
            
            action_display = action_names.get(log.action, log.action)
            self.table.setItem(row_idx, 3, QTableWidgetItem(action_display))
            
            entity = f"{log.entity_type}:{log.entity_id}" if log.entity_type else "—"
            self.table.setItem(row_idx, 4, QTableWidgetItem(entity))
            
            self.table.setItem(row_idx, 5, QTableWidgetItem(log.details or "—"))