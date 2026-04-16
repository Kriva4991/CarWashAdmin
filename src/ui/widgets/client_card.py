# src/ui/widgets/client_card.py
"""
Виджет карточки клиента
Отображает информацию о клиенте в компактном и стильном виде
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QMouseEvent

from models.client import Client


class ClientCard(QFrame):
    """
    Карточка клиента с основной информацией и кнопками действий
    
    Сигналы:
        doubleClicked(client_id) - двойной клик по карточке
        historyRequested(client_id) - запрос истории заказов
        commentEditRequested(client_id, current_comment) - запрос редактирования комментария
    """
    
    # Сигналы
    doubleClicked = pyqtSignal(int)  # client_id
    historyRequested = pyqtSignal(int)  # client_id
    commentEditRequested = pyqtSignal(int, str)  # client_id, current_comment
    
    def __init__(self, client: Client, parent=None):
        """
        Инициализация карточки
        
        Args:
            client: Объект Client с данными
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Настраивает интерфейс карточки"""
        # Основные настройки
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
        # Главный layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(15)
        
        # === ЛЕВАЯ ЧАСТЬ: ИНФОРМАЦИЯ ===
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Верхняя строка: Госномер и марка
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Госномер (крупно)
        self.car_number_label = QLabel(self.client.car_number)
        self.car_number_label.setObjectName("carNumber")
        header_layout.addWidget(self.car_number_label)
        
        # Марка авто (если есть)
        if self.client.car_model:
            self.car_model_label = QLabel(f"({self.client.car_model})")
            self.car_model_label.setObjectName("carModel")
            header_layout.addWidget(self.car_model_label)
        
        header_layout.addStretch()
        info_layout.addLayout(header_layout)
        
        # Средняя строка: Телефон, визиты, сумма, последний визит
        details_layout = QHBoxLayout()
        details_layout.setSpacing(15)
        
        # Телефон
        if self.client.phone:
            self.phone_label = QLabel(f"📞 {self.client.formatted_phone}")
            self.phone_label.setObjectName("phone")
            details_layout.addWidget(self.phone_label)
        
        # Количество визитов
        visits_text = self._get_visits_text()
        self.visits_label = QLabel(f"📋 {visits_text}")
        self.visits_label.setObjectName("visits")
        details_layout.addWidget(self.visits_label)
        
        # Потрачено всего
        self.spent_label = QLabel(f"💰 {self.client.formatted_total_spent}")
        self.spent_label.setObjectName("spent")
        details_layout.addWidget(self.spent_label)
        
        # Последний визит
        self.last_visit_label = QLabel(f"⏰ {self.client.last_visit_display}")
        self.last_visit_label.setObjectName("lastVisit")
        details_layout.addWidget(self.last_visit_label)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        # Комментарий (если есть)
        if self.client.comment:
            self.comment_label = QLabel(f"📝 {self.client.comment}")
            self.comment_label.setObjectName("comment")
            self.comment_label.setWordWrap(True)
            self.comment_label.setMaximumHeight(40)
            info_layout.addWidget(self.comment_label)
        
        info_layout.addStretch()
        main_layout.addWidget(info_widget, 1)
        
        # === ПРАВАЯ ЧАСТЬ: КНОПКИ ===
        buttons_widget = QWidget()
        buttons_widget.setFixedWidth(110)
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        # Кнопка "История"
        self.btn_history = QPushButton("📋 История")
        self.btn_history.setObjectName("historyButton")
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_history.clicked.connect(self._on_history_clicked)
        buttons_layout.addWidget(self.btn_history)
        
        # Кнопка "Комментарий" — только admin и manager
        from services.user_service import user_service
        if user_service.has_permission('edit_client'):
            self.btn_comment = QPushButton("✏️ Комментарий")
            self.btn_comment.setObjectName("commentButton")
            self.btn_comment.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_comment.clicked.connect(self._on_comment_clicked)
            buttons_layout.addWidget(self.btn_comment)
            
            buttons_layout.addStretch()
            main_layout.addWidget(buttons_widget)
    
    def apply_styles(self):
        """Применяет стили к карточке"""
        # Цвет рамки в зависимости от уровня лояльности
        border_color = self.client.loyalty_level.border_color
        
        # Основной стиль карточки
        self.setStyleSheet(f"""
            ClientCard {{
                background-color: white;
                border-left: 5px solid {border_color};
                border-radius: 8px;
            }}
            ClientCard:hover {{
                background-color: #f8f9fa;
            }}
            
            QLabel#carNumber {{
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            QLabel#carModel {{
                font-size: 14px;
                color: #7f8c8d;
            }}
            
            QLabel#phone {{
                font-size: 13px;
                color: #3498db;
            }}
            
            QLabel#visits {{
                font-size: 13px;
                color: #7f8c8d;
            }}
            
            QLabel#spent {{
                font-size: 13px;
                color: #27ae60;
                font-weight: bold;
            }}
            
            QLabel#lastVisit {{
                font-size: 12px;
                color: #95a5a6;
            }}
            
            QLabel#comment {{
                font-size: 12px;
                color: #e67e22;
                font-style: italic;
            }}
            
            QPushButton#historyButton {{
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            
            QPushButton#historyButton:hover {{
                background-color: #2980b9;
            }}
            
            QPushButton#historyButton:pressed {{
                background-color: #1a5276;
            }}
            
            QPushButton#commentButton {{
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            
            QPushButton#commentButton:hover {{
                background-color: #d68910;
            }}
            
            QPushButton#commentButton:pressed {{
                background-color: #b36b00;
            }}
        """)
    
    def _get_visits_text(self) -> str:
        """Формирует текст с количеством визитов"""
        visits = self.client.total_visits
        
        if visits == 0:
            return "0 визитов"
        
        # Склоняем слово "визит"
        if visits % 10 == 1 and visits % 100 != 11:
            word = "визит"
        elif 2 <= visits % 10 <= 4 and not (12 <= visits % 100 <= 14):
            word = "визита"
        else:
            word = "визитов"
        
        return f"{visits} {word}"
    
    def _on_history_clicked(self):
        """Обработчик клика по кнопке История"""
        self.historyRequested.emit(self.client.id)
    
    def _on_comment_clicked(self):
        """Обработчик клика по кнопке Комментарий"""
        self.commentEditRequested.emit(self.client.id, self.client.comment or "")
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Обработчик двойного клика"""
        self.doubleClicked.emit(self.client.id)
        super().mouseDoubleClickEvent(event)
    
    def update_client(self, client: Client):
        """
        Обновляет данные клиента в карточке
        
        Args:
            client: Новые данные клиента
        """
        self.client = client
        self.apply_styles()
        
        # Обновляем текст в лейблах
        self.car_number_label.setText(client.car_number)
        
        if hasattr(self, 'car_model_label'):
            if client.car_model:
                self.car_model_label.setText(f"({client.car_model})")
            else:
                self.car_model_label.hide()
        
        if hasattr(self, 'phone_label'):
            if client.phone:
                self.phone_label.setText(f"📞 {client.formatted_phone}")
            else:
                self.phone_label.hide()
        
        self.visits_label.setText(f"📋 {self._get_visits_text()}")
        self.spent_label.setText(f"💰 {client.formatted_total_spent}")
        self.last_visit_label.setText(f"⏰ {client.last_visit_display}")
        
        if hasattr(self, 'comment_label'):
            if client.comment:
                self.comment_label.setText(f"📝 {client.comment}")
                self.comment_label.show()
            else:
                self.comment_label.hide()


class ClientCardPlaceholder(QFrame):
    """
    Плейсхолдер для загрузки (скелетон)
    Показывается пока данные загружаются
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
        self.setStyleSheet("""
            ClientCardPlaceholder {
                background-color: #f5f5f5;
                border-left: 5px solid #bdc3c7;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Анимированные полоски
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        
        # Полоска для номера
        line1 = QLabel("    ")
        line1.setObjectName("placeholder")
        line1.setFixedSize(120, 20)
        line1.setStyleSheet("""
            QLabel#placeholder {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(line1)
        
        # Полоска для деталей
        line2 = QLabel("    ")
        line2.setObjectName("placeholder")
        line2.setFixedSize(300, 16)
        line2.setStyleSheet("""
            QLabel#placeholder {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(line2)
        
        layout.addWidget(info_widget, 1)
        layout.addStretch()


class EmptyClientsPlaceholder(QWidget):
    """
    Плейсхолдер для пустого списка клиентов
    """
    
    def __init__(self, message: str = "Клиенты не найдены", parent=None):
        super().__init__(parent)
        self.setup_ui(message)
    
    def setup_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 50, 0, 50)
        
        # Иконка
        icon_label = QLabel("📭")
        icon_label.setObjectName("emptyIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel#emptyIcon {
                font-size: 48px;
                color: #bdc3c7;
            }
        """)
        layout.addWidget(icon_label)
        
        # Сообщение
        message_label = QLabel(message)
        message_label.setObjectName("emptyMessage")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel#emptyMessage {
                font-size: 16px;
                color: #7f8c8d;
                padding: 10px;
            }
        """)
        layout.addWidget(message_label)
        
        # Подсказка
        hint_label = QLabel("Попробуйте изменить параметры поиска")
        hint_label.setObjectName("emptyHint")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel#emptyHint {
                font-size: 13px;
                color: #95a5a6;
            }
        """)
        layout.addWidget(hint_label)
        
        layout.addStretch()