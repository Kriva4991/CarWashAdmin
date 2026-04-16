# src/ui/login_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from services.user_service import user_service
from utils.translator import tr

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("app.title"))
        self.setFixedSize(480, 600)
        self.setModal(True)
        self.current_user = None
        
        # Убираем стандартную рамку
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.FramelessWindowHint
        )
        
        # 🔧 Флаг для защиты от двойного вызова
        self.is_logging_in = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Главный layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === ВЕРХНЯЯ ЧАСТЬ (исправленная) ===
        header = QWidget()
        header.setFixedHeight(240)  # ← Уменьшил с 280 до 240
        
        # 🔧 ОДНОЦВЕТНЫЙ фон вместо градиента (убираем полосы)
        header.setStyleSheet("""
            QWidget {
                background-color: #3498db;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 35, 40, 35)
        header_layout.setSpacing(10)
        
        # Иконка машины
        icon = QLabel("🚗")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 64px;")
        header_layout.addWidget(icon)
        
        # Название (без фона, просто белый текст)
        title = QLabel(tr("app.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title)
        
        # Подзаголовок
        subtitle = QLabel(tr("app.subtitle"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.95);
        """)
        header_layout.addWidget(subtitle)
        
        header_layout.addStretch()
        main_layout.addWidget(header)
        
        # === НИЖНЯЯ ЧАСТЬ (оставляем как есть) ===
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(50, 35, 50, 35)
        content_layout.setSpacing(20)
        
        # Поле логина
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText(tr("login.username"))
        self.username_edit.setFixedHeight(50)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                padding: 0 18px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                font-size: 15px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
            QLineEdit:hover {
                border: 2px solid #b2bec3;
            }
        """)
        content_layout.addWidget(self.username_edit)
        
        # Поле пароля
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(tr("login.password"))
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setFixedHeight(50)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 0 18px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                font-size: 15px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
            QLineEdit:hover {
                border: 2px solid #b2bec3;
            }
        """)
        content_layout.addWidget(self.password_edit)
        
        # Кнопка входа
        self.login_button = QPushButton(tr("login.login_btn"))
        self.login_button.setFixedHeight(55)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:1 #2ecc71
                );
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2980b9,
                    stop:1 #27ae60
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #21618c,
                    stop:1 #1e8449
                );
            }
        """)
        self.login_button.clicked.connect(self.login)
        content_layout.addWidget(self.login_button)
        
        # Подсказка
        hint = QLabel(tr("login.hint"))
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #95a5a6; padding: 8px 0;")
        content_layout.addWidget(hint)
        
        content_layout.addStretch()
        main_layout.addWidget(content)
        
        # Enter для входа
        self.password_edit.returnPressed.connect(self.login)
    
    def login(self):
        """Обработка входа"""
        # 🔧 Защита от двойного вызова
        if self.is_logging_in:
            return
        self.is_logging_in = True
        
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(
                self, tr("common.error"),
                tr("login.error_empty"),
                QMessageBox.StandardButton.Ok
            )
            self.is_logging_in = False
            return
        
        # 🆕 Используем UserService вместо прямого SQL
        from services.user_service import user_service
        
        user = user_service.login(username, password)
        
        if user:
            self.current_user = user.username
            self.accept()
        else:
            QMessageBox.critical(
                self, tr("common.error"),
                tr("login.error_invalid"),
                QMessageBox.StandardButton.Ok
            )
            self.is_logging_in = False