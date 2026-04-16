# src/ui/clients_tab.py
"""
Вкладка "Клиенты" - обновлённая версия
Использует новую архитектуру: ClientService + ClientCard + пагинация
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QFileDialog,
    QTextEdit, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
import csv

# 🆕 Новые импорты
from services.client_service import ClientService
from ui.widgets.client_card import ClientCard, EmptyClientsPlaceholder
from models.client import Client
from utils.excel_exporter import ExcelExporter
from services.user_service import user_service
from utils.translator import tr


class ClientsTab(QWidget):
    """Вкладка управления клиентами"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = user_service.current_user
        
        # 🆕 Инициализация сервиса
        self.client_service = ClientService()
        
        # 🆕 Состояние пагинации
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        self.search_query = ""
        
        # 🆕 Таймер для отложенного поиска (debounce)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.setup_ui()
        self.load_clients()
    
    def setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # === ЗАГОЛОВОК ===
        header = QLabel(tr("clients.title"))
        header.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            padding: 10px; 
            color: #2c3e50;
        """)
        layout.addWidget(header)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ: ПОИСК И ДЕЙСТВИЯ ===
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Поиск
        search_label = QLabel(tr("clients.search"))
        search_label.setStyleSheet("font-size: 14px;")
        top_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("clients.search_placeholder"))
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 350px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        # 🆕 Используем debounce для поиска
        self.search_edit.textChanged.connect(self._on_search_changed)
        top_layout.addWidget(self.search_edit)
        
        top_layout.addStretch()
        
         # Кнопка синхронизации — admin и manager
        if self.user and self.user.has_permission('edit_client'):
            self.btn_sync = QPushButton(tr("clients.sync"))
            self.btn_sync.setToolTip(tr("clients.sync_tooltip"))
            self.btn_sync.clicked.connect(self.sync_clients)
            self.btn_sync.setStyleSheet(self._get_button_style("#9b59b6"))
            top_layout.addWidget(self.btn_sync)
        
        # Кнопка экспорта — admin и manager
        if self.user and self.user.has_permission('export_clients'):
            self.btn_export = QPushButton(tr("clients.export"))
            self.btn_export.clicked.connect(self.export_clients)
            self.btn_export.setStyleSheet(self._get_button_style("#95a5a6"))
            top_layout.addWidget(self.btn_export)
        
        layout.addLayout(top_layout)
        
        # === СТАТИСТИКА ===
        self.stats_label = QLabel("📋 Загрузка...")
        self.stats_label.setStyleSheet("""
            font-size: 14px; 
            padding: 10px 15px; 
            background-color: #e3f2fd; 
            border-radius: 6px;
            color: #2c3e50;
        """)
        layout.addWidget(self.stats_label)
        
        # === ОБЛАСТЬ ПРОКРУТКИ С КАРТОЧКАМИ ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #f5f5f5;")
        
        self.clients_container = QWidget()
        self.clients_layout = QVBoxLayout(self.clients_container)
        self.clients_layout.setSpacing(12)
        self.clients_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.clients_container)
        layout.addWidget(scroll, 1)  # Растягиваем на всё доступное пространство
        
        # === ПАНЕЛЬ ПАГИНАЦИИ ===
        self.pagination_widget = QWidget()
        self.pagination_layout = QHBoxLayout(self.pagination_widget)
        self.pagination_layout.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(self.pagination_widget)
        
        # Скрываем пагинацию по умолчанию
        self.pagination_widget.hide()
        
        # === ПОДСКАЗКА ===
        hint = QLabel(tr("clients.hint"))
        hint.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        layout.addWidget(hint)
    
    def _get_button_style(self, color: str) -> str:
        """Возвращает стиль для кнопки"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
        """
    
    def _darken_color(self, color: str) -> str:
        """Затемняет цвет для hover-эффекта"""
        color_map = {
            '#95a5a6': '#7f8c8d',
            '#9b59b6': '#8e44ad',
            '#3498db': '#2980b9',
            '#27ae60': '#229954',
            '#f39c12': '#d68910',
        }
        return color_map.get(color, color)
    
    # ============ ПОИСК И ПАГИНАЦИЯ ============
    
    def _on_search_changed(self, text: str):
        """Обработчик изменения текста поиска (с debounce)"""
        self.search_query = text.strip()
        self.current_page = 1  # Сбрасываем на первую страницу
        self.search_timer.stop()
        self.search_timer.start(300)  # Ждём 300мс после последнего ввода
    
    def _perform_search(self):
        """Выполняет поиск после задержки"""
        self.load_clients()
    
    def load_clients(self):
        """Загружает клиентов с учётом поиска и пагинации"""
        # Очищаем контейнер
        self._clear_container()
        
        try:
            # Сбрасываем кэш при каждой загрузке (чтобы данные были свежими)
            self.client_service.invalidate_cache('search')
            # 🆕 Используем сервис для поиска
            result = self.client_service.search_clients(
                query=self.search_query,
                page=self.current_page,
                page_size=self.page_size
            )
            
            self.total_pages = result.total_pages
            
            # Проверяем, есть ли клиенты
            if not result.clients:
                empty_widget = EmptyClientsPlaceholder(
                    tr("clients.empty") if self.search_query else tr("clients.empty")
                )
                self.clients_layout.addWidget(empty_widget)
                self.stats_label.setText(tr("clients.stats", count=result.total_count))
                self.pagination_widget.hide()
                return
            
            # 🆕 Создаём карточки из моделей Client
            for client in result.clients:
                card = ClientCard(client)
                card.doubleClicked.connect(self.show_client_history)
                card.historyRequested.connect(self.show_client_history)
                card.commentEditRequested.connect(self.edit_comment)
                self.clients_layout.addWidget(card)
            
            # Добавляем растяжку в конец
            self.clients_layout.addStretch()
            
            # Обновляем статистику и пагинацию
            self.stats_label.setText(f"📋 {result.total_count} клиентов в базе | {result.display_range}")
            self._update_pagination(result)
            
        except Exception as e:
            QMessageBox.critical(
                self, "❌ Ошибка",
                f"Не удалось загрузить клиентов:\n{str(e)}"
            )
    
    def _clear_container(self):
        """Очищает контейнер с карточками"""
        while self.clients_layout.count():
            item = self.clients_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _update_pagination(self, result):
        """Обновляет панель пагинации"""
        # Очищаем старые кнопки
        while self.pagination_layout.count():
            item = self.pagination_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if result.total_pages <= 1:
            self.pagination_widget.hide()
            return
        
        self.pagination_widget.show()
        
        # Добавляем растяжку слева
        self.pagination_layout.addStretch()
        
        # Кнопка "Предыдущая"
        if result.has_previous:
            btn_prev = QPushButton("← Назад")
            btn_prev.setStyleSheet(self._get_pagination_button_style())
            btn_prev.clicked.connect(self._prev_page)
            self.pagination_layout.addWidget(btn_prev)
        
        # Информация о странице
        page_info = QLabel(f"Стр. {result.page} из {result.total_pages}")
        page_info.setStyleSheet("""
            font-size: 14px;
            color: #2c3e50;
            padding: 8px 15px;
            font-weight: bold;
        """)
        self.pagination_layout.addWidget(page_info)
        
        # Выбор страницы (выпадающий список)
        if result.total_pages > 5:
            page_combo = QComboBox()
            page_combo.addItems([str(i) for i in range(1, result.total_pages + 1)])
            page_combo.setCurrentIndex(result.page - 1)
            page_combo.currentIndexChanged.connect(self._on_page_selected)
            page_combo.setStyleSheet("""
                QComboBox {
                    padding: 6px 10px;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    font-size: 13px;
                }
            """)
            self.pagination_layout.addWidget(page_combo)
        
        # Кнопка "Следующая"
        if result.has_next:
            btn_next = QPushButton("Вперёд →")
            btn_next.setStyleSheet(self._get_pagination_button_style())
            btn_next.clicked.connect(self._next_page)
            self.pagination_layout.addWidget(btn_next)
        
        # Добавляем растяжку справа
        self.pagination_layout.addStretch()
    
    def _get_pagination_button_style(self) -> str:
        """Стиль для кнопок пагинации"""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
    
    def _prev_page(self):
        """Переход на предыдущую страницу"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_clients()
    
    def _next_page(self):
        """Переход на следующую страницу"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_clients()
    
    def _on_page_selected(self, index: int):
        """Обработчик выбора страницы из выпадающего списка"""
        self.current_page = index + 1
        self.load_clients()
    
    # ============ СИНХРОНИЗАЦИЯ ============
    
    def sync_clients(self):
        """Синхронизация клиентов"""
        from services.user_service import user_service
        if not user_service.has_permission('edit_client'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для синхронизации клиентов!")
            return

        """Синхронизирует клиентов из таблицы заказов"""
        reply = QMessageBox.question(
            self,
            "🔄 Синхронизация",
            "Создать клиентов из существующих заказов?\n\n"
            "Будут созданы клиенты для всех госномеров,\n"
            "которых ещё нет в базе клиентов.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            count = self.client_service.sync_clients_from_orders()
            
            if count > 0:
                # Принудительно обновляем статистику клиентов
                for client in self.client_service.search_clients_simple():
                    self.client_service.invalidate_cache(f'client:{client.id}')
                    
                QMessageBox.information(
                    self,
                    "✅ Синхронизация завершена",
                    f"Создано клиентов: {count}"
                )
                self.load_clients()
            else:
                QMessageBox.information(
                    self,
                    "ℹ️ Синхронизация",
                    "Новых клиентов не найдено.\n"
                    "Все госномера уже есть в базе клиентов."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось выполнить синхронизацию:\n{str(e)}"
            )
    
    # ============ ИСТОРИЯ ЗАКАЗОВ ============
    
    def show_client_history(self, client_id: int):
        """Показывает историю заказов клиента"""
        try:
            # 🆕 Получаем клиента и историю через сервис
            client = self.client_service.get_client(client_id)
            if not client:
                QMessageBox.warning(self, "⚠️ Ошибка", "Клиент не найден")
                return
            
            history = self.client_service.get_client_history(client_id)
            
            # Создаём и показываем диалог
            dialog = ClientHistoryDialog(client, history, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось загрузить историю:\n{str(e)}"
            )
    
    # ============ РЕДАКТИРОВАНИЕ КОММЕНТАРИЯ ============
    
    def edit_comment(self, client_id: int, current_comment: str):
        """Редактирование комментария"""
        from services.user_service import user_service
        if not user_service.has_permission('edit_client'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для редактирования клиентов!")
            return

        """Редактирует комментарий клиента"""
        dialog = CommentEditDialog(client_id, current_comment, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 🆕 Сохраняем через сервис
            success = self.client_service.update_comment(client_id, dialog.get_comment())
            
            if success:
                QMessageBox.information(self, "✅ Сохранено", "Комментарий обновлён!")
                # Обновляем кэш и перезагружаем
                self.client_service.invalidate_cache(f'client:{client_id}')
                self.load_clients()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось сохранить комментарий")
    
    # ============ ЭКСПОРТ ============
    
    def export_clients(self):
        """Экспорт клиентов"""
        from services.user_service import user_service
        if not user_service.has_permission('export_clients'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для экспорта клиентов!")
            return
    
        """Экспорт клиентов в Excel"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"clients_export_{timestamp}.xlsx"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "📊 Сохранить базу клиентов",
            default_filename,
            "Excel файлы (*.xlsx);;Все файлы (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            # Получаем клиентов
            clients = self.client_service.search_clients_simple(self.search_query)
            clients_data = [c.to_dict() for c in clients]
            
            exporter = ExcelExporter()
            saved_path = exporter.export_clients(
                clients=clients_data,
                filepath=filepath
            )
            
            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"Экспортировано клиентов: {len(clients)}\n"
                f"Файл сохранён:\n{saved_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Ошибка экспорта",
                f"Не удалось создать Excel файл:\n{str(e)}"
            )
    
    # ============ УСТАРЕВШИЕ МЕТОДЫ (ОСТАВЛЕНЫ ДЛЯ СОВМЕСТИМОСТИ) ============
    
    def translate_status(self, status: str) -> str:
        """Переводит статусы (для совместимости)"""
        statuses = {
            'queue': '🟡 В очереди',
            'process': '🔵 В работе',
            'done': '🟢 Готово',
            'cancelled': '🔴 Отменено'
        }
        return statuses.get(status, status)


# ============ ВСПОМОГАТЕЛЬНЫЕ ДИАЛОГИ ============

class ClientHistoryDialog(QDialog):
    """Диалог с историей заказов клиента"""
    
    def __init__(self, client: Client, history: list, parent=None):
        super().__init__(parent)
        self.client = client
        self.history = history
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"📋 История заказов: {self.client.car_number}")
        self.setMinimumSize(750, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Заголовок с информацией о клиенте
        header_text = f"🚗 {self.client.display_name}"
        if self.client.phone:
            header_text += f"  |  📞 {self.client.formatted_phone}"
        
        header = QLabel(header_text)
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 15px;
            background-color: #e3f2fd;
            border-radius: 8px;
            color: #2c3e50;
        """)
        layout.addWidget(header)
        
        # Статистика (считаем на основе истории)
        total_orders = len(self.history)
        total_spent = sum(o.total_price for o in self.history)
        avg_check = total_spent / total_orders if total_orders > 0 else 0
        
        stats_text = f"📊 Всего заказов: {total_orders}"
        stats_text += f"  |  💰 Потрачено: {total_spent:.0f} ₽"
        stats_text += f"  |  🧮 Средний чек: {avg_check:.0f} ₽"
        
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            color: #2c3e50;
        """)
        layout.addWidget(stats_label)
        
        # Таблица с историей
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "ID", "Дата", "Гос.номер", "Услуги", "Сумма", "Статус"
        ])
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
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
        
        table.setRowCount(len(self.history))
        for row_idx, order in enumerate(self.history):
            table.setItem(row_idx, 0, QTableWidgetItem(str(order.order_id)))
            table.setItem(row_idx, 1, QTableWidgetItem(order.formatted_date))
            table.setItem(row_idx, 2, QTableWidgetItem(order.car_number))
            table.setItem(row_idx, 3, QTableWidgetItem(order.services_display))
            table.setItem(row_idx, 4, QTableWidgetItem(f"{order.total_price:.0f} ₽"))
            table.setItem(row_idx, 5, QTableWidgetItem(order.status_display))
        
        layout.addWidget(table)
        
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
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

class CommentEditDialog(QDialog):
    """Диалог редактирования комментария"""
    
    def __init__(self, client_id: int, current_comment: str, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setup_ui(current_comment)
    
    def setup_ui(self, current_comment: str):
        self.setWindowTitle("✏️ Редактировать комментарий")
        self.setFixedSize(450, 280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        label = QLabel("Введите комментарий для клиента:")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Например: VIP клиент, любит кофе, скидка 10%")
        self.text_edit.setText(current_comment)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.text_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self.accept)
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
    
    def get_comment(self) -> str:
        """Возвращает введённый комментарий"""
        return self.text_edit.toPlainText().strip()