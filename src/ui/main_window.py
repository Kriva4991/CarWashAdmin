# src/ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QHeaderView, QMessageBox, QFileDialog, QScrollArea,
    QFrame, QLineEdit, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from database import get_connection, DB_PATH
import os
from datetime import datetime
from ui.reports_tab import ReportsTab
from ui.shift_manager import ShiftManagerDialog
from ui.clients_tab import ClientsTab
from ui.settings_tab import SettingsTab
from utils.excel_exporter import ExcelExporter
from services.user_service import user_service
from ui.consumables_tab import ConsumablesTab
from utils.translator import tr

class CarWashMainWindow(QMainWindow):
    def __init__(self, current_user="admin", parent=None):
        super().__init__(parent)
        self.current_user = current_user  # ← Сохраняем пользователя
        self.user = user_service.current_user  # 🆕 Текущий пользователь с правами
        self.setWindowTitle(f"🚗 CarWash Admin Pro | Пользователь: {current_user}")
        self.setGeometry(100, 100, 1200, 700)
        
        # --- Центральный виджет ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Заголовок ---
        header = QLabel("📋 Панель администратора")
        header.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(header)
        
        # --- Вкладки ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_orders_tab(), tr("tabs.orders"))
        self.tabs.addTab(self.create_services_tab(), tr("tabs.services"))
        self.tabs.addTab(ClientsTab(), tr("tabs.clients"))
        self.tabs.addTab(ReportsTab(), tr("tabs.reports"))
        self.tabs.addTab(ConsumablesTab(), tr("tabs.consumables"))
        self.tabs.addTab(SettingsTab(self, current_user=self.current_user), tr("tabs.settings"))
        main_layout.addWidget(self.tabs)
        
        # --- Статус бар ---
        self.statusBar().showMessage("Готов к работе")
        
        # --- Загружаем данные при старте ---
        self.load_orders()
        self.load_services()
        self.setup_hotkeys()

        # 🔧 ПРОВЕРКА ЛИЦЕНЗИИ (с блокировкой)
        #allowed, status = self.check_and_enforce_license()
        #if not allowed:
         #   if status == "EXIT":
          #      # Закрываем приложение
           #     from PyQt6.QtWidgets import QApplication
            #    QApplication.quit()
             #   return
        # Если BLOCKED_SHOW_SETTINGS — оставляем окно но с блокировкой

        # 🔧 ТАЙМЕР ПРОВЕРКИ БЭКАПА (каждую минуту)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.check_auto_backup)
        self.backup_timer.start(60000)  # 60 секунд
        
        # Проверка при запуске
        self.check_backup_on_startup()
    
    def create_orders_tab(self) -> QWidget:
        """Вкладка с текущими заказами (группировка по статусам)"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(15)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ СО СТАТИСТИКОЙ ===
        stats_widget = QWidget()
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(20)
        
        # Карточки статистики
        orders_word = tr("orders.orders_count", default="заказов")
        self.today_orders_label = QLabel(f"{tr('orders.today')}\n0 {orders_word}")
        self.today_orders_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 20px;
                background-color: #e3f2fd;
                border-radius: 8px;
            }
        """)
        self.today_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.today_orders_label)
        
        self.today_revenue_label = QLabel(f"{tr('orders.revenue')}\n0 ₽")
        self.today_revenue_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 20px;
                background-color: #e8f5e9;
                border-radius: 8px;
            }
        """)
        self.today_revenue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.today_revenue_label)
        
        self.in_progress_label = QLabel(f"{tr('orders.in_progress')}\n0")
        self.in_progress_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 20px;
                background-color: #fff3e0;
                border-radius: 8px;
            }
        """)
        self.in_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.in_progress_label)
        
        stats_layout.addStretch()
        main_layout.addWidget(stats_widget)
        
        # === ПАНЕЛЬ ДЕЙСТВИЙ ===
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Поиск
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 16px;")
        actions_layout.addWidget(search_label)
        
        self.orders_search = QLineEdit()
        self.orders_search.setPlaceholderText(tr("orders.search_placeholder"))
        self.orders_search.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.orders_search.textChanged.connect(self.filter_orders)
        actions_layout.addWidget(self.orders_search)
        
        actions_layout.addStretch()
        
        # Кнопка "Новый заказ" — только для admin и manager
        if self.user and self.user.has_permission('create_order'):
            self.btn_add_order = QPushButton(tr("orders.new_order"))
            self.btn_add_order.clicked.connect(self.add_order)
            self.btn_add_order.setStyleSheet(self.get_btn_style("#27ae60", bold=True))
            actions_layout.addWidget(self.btn_add_order)
        
        # Кнопка "Обновить" — всем
        self.btn_refresh_orders = QPushButton(tr("orders.refresh"))
        self.btn_refresh_orders.clicked.connect(self.load_orders)
        self.btn_refresh_orders.setStyleSheet(self.get_btn_style("#3498db"))
        actions_layout.addWidget(self.btn_refresh_orders)
        
        # Кнопка "Excel" — admin и manager
        if self.user and self.user.has_permission('export_reports'):
            self.btn_export_orders = QPushButton(tr("orders.export"))
            self.btn_export_orders.clicked.connect(self.export_to_excel)
            self.btn_export_orders.setStyleSheet(self.get_btn_style("#95a5a6"))
            actions_layout.addWidget(self.btn_export_orders)
        
        main_layout.addWidget(actions_widget)
        
        # === ГРУППЫ ЗАКАЗОВ ПО СТАТУСАМ ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        groups_container = QWidget()
        groups_layout = QVBoxLayout(groups_container)
        groups_layout.setSpacing(20)
        groups_layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа "В очереди"
        self.queue_group = self.create_order_group(tr("orders.queue"), "queue")
        groups_layout.addWidget(self.queue_group)
        
        # Группа "В работе"
        self.process_group = self.create_order_group(tr("orders.process"), "process")
        groups_layout.addWidget(self.process_group)
        
        # Группа "Готово"
        self.done_group = self.create_order_group(tr("orders.done"), "done")
        groups_layout.addWidget(self.done_group)
        
        groups_layout.addStretch()
        
        scroll.setWidget(groups_container)
        main_layout.addWidget(scroll)
        
        # Подсказка
        hint = QLabel(tr("orders.hint"))
        hint.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        main_layout.addWidget(hint)
        
        return tab
    
    def create_order_group(self, title: str, status: str) -> QFrame:
        """Создаёт группу для заказов определённого статуса"""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Заголовок группы
        header = QLabel(title)
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px 0;
            border-bottom: 2px solid #ecf0f1;
        """)
        layout.addWidget(header)
        
        # Контейнер для карточек заказов
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)
        cards_layout.setSpacing(8)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # Сохраняем ссылку на layout для добавления заказов
        if status == "queue":
            self.queue_layout = cards_layout
            self.queue_container = cards_widget
        elif status == "process":
            self.process_layout = cards_layout
            self.process_container = cards_widget
        else:
            self.done_layout = cards_layout
            self.done_container = cards_widget
        
        layout.addWidget(cards_widget)
        
        return group
    
    def create_order_card(self, order_data: dict) -> QFrame:
        """Создаёт карточку заказа с кнопками"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-left: 5px solid #3498db;
                border-radius: 6px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(15)
        
        # Время и номер
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setSpacing(2)
        
        time_label = QLabel(order_data.get('time', '--:--'))
        time_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        time_layout.addWidget(time_label)
        
        id_label = QLabel(f"#{order_data.get('id', '')}")
        id_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        time_layout.addWidget(id_label)
        
        layout.addWidget(time_widget)
        
        # Информация об авто
        car_widget = QWidget()
        car_layout = QVBoxLayout(car_widget)
        car_layout.setSpacing(2)
        
        car_number = order_data.get('car_number', '—')
        car_model = order_data.get('car_model', '')
        
        car_label = QLabel(f"🚗 {car_number}")
        car_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50;")
        car_layout.addWidget(car_label)
        
        if car_model:
            model_label = QLabel(car_model)
            model_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            car_layout.addWidget(model_label)
        
        if order_data.get('client_phone'):
            phone_label = QLabel(f"📞 {order_data.get('client_phone')}")
            phone_label.setStyleSheet("font-size: 11px; color: #3498db;")
            car_layout.addWidget(phone_label)
        
        layout.addWidget(car_widget, 1)
        
        # Услуги
        services_label = QLabel(order_data.get('services', '—'))
        services_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        services_label.setWordWrap(True)
        services_label.setMinimumWidth(200)
        layout.addWidget(services_label, 2)
        
        # Сумма и оплата
        price_widget = QWidget()
        price_layout = QVBoxLayout(price_widget)
        price_layout.setSpacing(2)
        
        price_label = QLabel(f"{order_data.get('total_price', 0):.0f} ₽")
        price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        price_layout.addWidget(price_label)
        
        payment = order_data.get('payment_method', '')
        payment_display = {
            'cash': '💵 Нал',
            'card': '💳 Карта',
            'transfer': '📱 Перевод',
            'sbp': '📲 СБП'
        }.get(payment, '')
        
        if payment_display:
            pay_label = QLabel(payment_display)
            pay_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
            pay_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            price_layout.addWidget(pay_label)
        
        layout.addWidget(price_widget)
        
        # === КНОПКИ ДЕЙСТВИЙ ===
        btn_widget = QWidget()
        btn_layout = QVBoxLayout(btn_widget)
        btn_layout.setSpacing(5)
        
        order_id = order_data.get('id')
        status = order_data.get('status')
        
        # Кнопка смены статуса (только для queue и process)
        if status in ['queue', 'process'] and self.user and self.user.has_permission('change_order_status'):
            btn_text = "▶ В работу" if status == 'queue' else "✓ Готово"
            btn_color = "#3498db" if status == 'queue' else "#27ae60"
            
            btn_status = QPushButton(btn_text)
            btn_status.setFixedSize(100, 30)
            btn_status.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_status.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(btn_color)};
                }}
            """)
            btn_status.clicked.connect(lambda checked, oid=order_id: self.change_order_status_by_button(oid))
            btn_layout.addWidget(btn_status)
        
        # Кнопка редактирования
        if self.user and self.user.has_permission('edit_order'):
            btn_edit = QPushButton("✏️ Изменить")
            btn_edit.setFixedSize(100, 30)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d68910;
                }
            """)
            btn_edit.clicked.connect(lambda checked, oid=order_id: self.edit_order(oid))
            btn_layout.addWidget(btn_edit)
        
        # Кнопка удаления
        if self.user and self.user.has_permission('delete_order'):
            btn_delete = QPushButton("🗑️ Удалить")
            btn_delete.setFixedSize(100, 30)
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            btn_delete.clicked.connect(lambda checked, oid=order_id: self.delete_order(oid))
            btn_layout.addWidget(btn_delete)
            
            layout.addWidget(btn_widget)
        
        # Сохраняем ID в карточке
        card.setProperty('order_id', order_id)
        card.setProperty('order_status', status)
        
        return card
    
    def change_order_status_by_button(self, order_id: int):
        """Меняет статус заказа только вперёд (queue → process → done)"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
        
        current_status = row['status']
        
        # Только вперёд
        if current_status == 'queue':
            new_status = 'process'
        elif current_status == 'process':
            new_status = 'done'
        else:
            conn.close()
            return  # Готовые заказы не меняем
        
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        
        # 🆕 Перемещаем карточку (работает для всех переходов)
        self._move_order_card(order_id, current_status, new_status)
        
        # Обновляем статистику
        self._update_statistics_after_status_change(current_status, new_status)
        
        self.statusBar().showMessage(f"✅ Статус заказа #{order_id} изменён")

    def _move_order_card(self, order_id: int, old_status: str, new_status: str):
        """Перемещает карточку заказа между группами без сдвига интерфейса"""
        old_layout = None
        if old_status == 'queue':
            old_layout = self.queue_layout
        elif old_status == 'process':
            old_layout = self.process_layout
        elif old_status == 'done':
            old_layout = self.done_layout
        
        new_layout = None
        if new_status == 'queue':
            new_layout = self.queue_layout
        elif new_status == 'process':
            new_layout = self.process_layout
        elif new_status == 'done':
            new_layout = self.done_layout
        
        if not old_layout or not new_layout:
            print(f"⚠️ Не найден layout: old={old_status} -> new={new_status}")
            return
        
        # 🆕 Сохраняем позицию скролла ДО изменений
        scroll_area = self._find_scroll_area()
        scroll_value = scroll_area.verticalScrollBar().value() if scroll_area else 0
        
        # Находим карточку и её высоту
        widget_to_move = None
        card_height = 0
        for i in range(old_layout.count()):
            item = old_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.property('order_id') == order_id:
                    widget_to_move = widget
                    card_height = widget.height() + old_layout.spacing()
                    old_layout.removeWidget(widget)
                    break
        
        if widget_to_move:
            # Обновляем свойство статуса
            widget_to_move.setProperty('order_status', new_status)
            
            # Обновляем текст кнопки
            self._update_card_button(widget_to_move, new_status)
            
            # Добавляем в начало новой группы
            new_layout.insertWidget(0, widget_to_move)
            
            # Обновляем видимость групп
            self.queue_group.setVisible(self._has_visible_cards(self.queue_layout))
            self.process_group.setVisible(self._has_visible_cards(self.process_layout))
            self.done_group.setVisible(self._has_visible_cards(self.done_layout))
            
            # 🆕 Компенсируем сдвиг: возвращаем скролл на место
            if scroll_area:
                # Если перемещаем НЕ в ту же группу, нужно скомпенсировать исчезновение карточки
                if old_status != new_status:
                    scroll_area.verticalScrollBar().setValue(scroll_value + card_height)
                else:
                    scroll_area.verticalScrollBar().setValue(scroll_value)

    def _find_scroll_area(self):
        """Находит ScrollArea содержащий группы заказов"""
        # Ищем через родительские виджеты
        if hasattr(self, 'queue_group') and self.queue_group:
            parent = self.queue_group.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    return parent
                parent = parent.parent()
        return None

    def _scroll_to_group(self, status: str):
        """Прокручивает область к указанной группе"""
        group = None
        if status == 'queue':
            group = self.queue_group
        elif status == 'process':
            group = self.process_group
        elif status == 'done':
            group = self.done_group
        
        if group and group.isVisible():
            # Находим ScrollArea (родитель контейнера групп)
            scroll_area = None
            parent = group.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    scroll_area = parent
                    break
                parent = parent.parent()
            
            if scroll_area:
                # Прокручиваем так, чтобы группа была видна
                scroll_area.ensureWidgetVisible(group, 0, 50)

    def _update_card_button(self, card: QFrame, new_status: str):
        """Обновляет кнопку статуса на карточке"""
        # Находим кнопку внутри карточки
        for child in card.findChildren(QPushButton):
            if child.text() in ["▶ В работу", "✓ Готово"]:
                if new_status == 'queue':
                    child.setText("▶ В работу")
                    child.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 12px;
                            font-weight: bold;
                        }
                    """)
                elif new_status == 'process':
                    child.setText("✓ Готово")
                    child.setStyleSheet("""
                        QPushButton {
                            background-color: #27ae60;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 12px;
                            font-weight: bold;
                        }
                    """)
                elif new_status == 'done':
                    child.hide()
                break

    def _update_statistics_after_status_change(self, old_status: str, new_status: str):
        """Обновляет только статистику без перезагрузки"""
        # Получаем текущие значения из лейблов
        today_text = self.today_orders_label.text()
        revenue_text = self.today_revenue_label.text()
        progress_text = self.in_progress_label.text()
        
        # Парсим числа
        import re
        today_match = re.search(r'(\d+)', today_text)
        revenue_match = re.search(r'(\d+)', revenue_text)
        progress_match = re.search(r'(\d+)', progress_text)
        
        today_orders = int(today_match.group(1)) if today_match else 0
        today_revenue = int(revenue_match.group(1)) if revenue_match else 0
        in_progress = int(progress_match.group(1)) if progress_match else 0
        
        # Обновляем счётчики
        if new_status == 'process':
            in_progress += 1
        elif old_status == 'process' and new_status == 'done':
            in_progress -= 1
        
        # Обновляем лейблы
        orders_word = tr("orders.orders_count", default="заказов")
        self.today_orders_label.setText(f"{tr('orders.today')}\n{today_orders} {orders_word}")
        self.in_progress_label.setText(f"{tr('orders.in_progress')}\n{in_progress}")
    
    def load_orders(self):
        """Загружает заказы и распределяет по группам"""
        # Очищаем все группы
        if hasattr(self, 'queue_layout'):
            self._clear_order_layout(self.queue_layout)
        if hasattr(self, 'process_layout'):
            self._clear_order_layout(self.process_layout)
        if hasattr(self, 'done_layout'):
            self._clear_order_layout(self.done_layout)
        
        # Если новый интерфейс ещё не создан, используем старый
        if not hasattr(self, 'queue_group'):
            self._load_orders_legacy()
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Проверяем, нужно ли показывать все заказы
        show_all = hasattr(self, 'show_all_checkbox') and self.show_all_checkbox.isChecked()
        
        if show_all:
            cursor.execute("""
                SELECT 
                    o.id,
                    o.created_at,
                    o.car_number,
                    o.car_model,
                    o.client_phone,
                    o.status,
                    o.total_price,
                    o.payment_method,
                    GROUP_CONCAT(s.name, ', ') as services_list
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN services s ON oi.service_id = s.id
                GROUP BY o.id
                ORDER BY o.created_at ASC
                LIMIT 200
            """)
        else:
            cursor.execute("""
                SELECT 
                    o.id,
                    o.created_at,
                    o.car_number,
                    o.car_model,
                    o.client_phone,
                    o.status,
                    o.total_price,
                    o.payment_method,
                    GROUP_CONCAT(s.name, ', ') as services_list
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN services s ON oi.service_id = s.id
                WHERE DATE(o.created_at) = ?
                GROUP BY o.id
                ORDER BY o.created_at ASC
            """, (today,))
        
        rows = cursor.fetchall()
        conn.close()
        
        queue_count = 0
        process_count = 0
        done_count = 0
        today_revenue = 0
        
        for row in rows:
            order_data = {
                'id': row['id'],
                'time': str(row['created_at'])[11:16] if row['created_at'] else '--:--',
                'car_number': row['car_number'] or '—',
                'car_model': row['car_model'] or '',
                'client_phone': row['client_phone'] or '',
                'services': row['services_list'] or '—',
                'total_price': row['total_price'] or 0,
                'payment_method': row['payment_method'] or 'cash',
                'status': row['status']
            }
            
            card = self.create_order_card(order_data)
            card.mouseDoubleClickEvent = lambda e, oid=row['id']: self.edit_order(oid)
            
            # Добавляем в соответствующую группу
            if row['status'] == 'queue':
                self.queue_layout.addWidget(card)
                queue_count += 1
            elif row['status'] == 'process':
                self.process_layout.addWidget(card)
                process_count += 1
            elif row['status'] == 'done':
                self.done_layout.addWidget(card)
                done_count += 1
            
            # Считаем выручку за сегодня
            if row['created_at'] and str(row['created_at'])[:10] == today:
                if row['status'] in ['process', 'done']:
                    today_revenue += row['total_price'] or 0
        
        # Показываем/скрываем пустые группы
        self.queue_group.setVisible(queue_count > 0)
        self.process_group.setVisible(process_count > 0)
        self.done_group.setVisible(done_count > 0)
        
        # Если группа пуста, показываем заглушку
        if queue_count == 0:
            empty_label = QLabel(tr("orders.no_orders_queue"))
            empty_label.setStyleSheet("color: #95a5a6; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.queue_layout.addWidget(empty_label)
            self.queue_group.setVisible(True)
        
        if process_count == 0:
            empty_label = QLabel(tr("orders.no_orders_process"))
            empty_label.setStyleSheet("color: #95a5a6; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.process_layout.addWidget(empty_label)
            self.process_group.setVisible(True)
        
        if done_count == 0:
            empty_label = QLabel(tr("orders.no_orders_done"))
            empty_label.setStyleSheet("color: #95a5a6; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.done_layout.addWidget(empty_label)
            self.done_group.setVisible(True)
        
        # Обновляем статистику
        total_today = queue_count + process_count + done_count
        orders_word = tr("orders.orders_count", default="заказов")
        self.today_orders_label.setText(f"{tr('orders.today')}\n{total_today} {orders_word}")
        self.today_revenue_label.setText(f"{tr('orders.revenue')}\n{today_revenue:.0f} ₽")
        self.in_progress_label.setText(f"{tr('orders.in_progress')}\n{process_count}")
    
    def _clear_order_layout(self, layout):
        """Очищает layout от всех виджетов"""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _has_visible_cards(self, layout) -> bool:
        """Проверяет, есть ли видимые карточки в layout"""
        if layout is None:
            return False
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # QLabel - это заглушка "Нет заказов", её не считаем
                if not isinstance(widget, QLabel) and not widget.isHidden():
                    return True
        return False
    
    def on_order_click(self, order_id: int, current_status: str):
        """Обработка клика по заказу - смена статуса"""
        status_map = {
            'queue': 'process',
            'process': 'done',
            'done': 'queue'
        }
        new_status = status_map.get(current_status, 'queue')
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        
        self.load_orders()
        self.statusBar().showMessage(f"✅ Статус заказа #{order_id} изменён")
    
    def filter_orders(self):
        """Фильтрует заказы по поиску"""
        search_text = self.orders_search.text().strip().lower()
        
        if not search_text:
            # Показываем все
            for group in [self.queue_group, self.process_group, self.done_group]:
                if group:
                    group.setVisible(True)
            return
        
        # Скрываем все
        self.queue_group.setVisible(False)
        self.process_group.setVisible(False)
        self.done_group.setVisible(False)
        
        # Ищем совпадения
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM orders
            WHERE car_number LIKE ? OR client_phone LIKE ? OR CAST(id AS TEXT) LIKE ?
        """, (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
        matching_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        # Показываем только совпадающие карточки
        for layout in [self.queue_layout, self.process_layout, self.done_layout]:
            if layout is None:
                continue
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    order_id = widget.property('order_id')
                    if order_id in matching_ids:
                        widget.show()
                        # Показываем родительскую группу
                        parent = widget.parent()
                        while parent:
                            if isinstance(parent, QFrame) and parent != widget:
                                parent.setVisible(True)
                                break
                            parent = parent.parent()
                    else:
                        widget.hide()
    
    def create_stat_card(self, title, value, color):
        """Создает карточку статистики"""
        card = QLabel()
        card.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                min-width: 200px;
            }}
        """)
        card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.setText(f"{title}\n{value}")
        return card
    
    def get_btn_style(self, color, bold=False):
        """Стиль для кнопок"""
        dark_color = self.darken_color(color)
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: {'bold' if bold else 'normal'};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {dark_color};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(dark_color)};
            }}
        """
    
    def darken_color(self, color):
        """Затемняет цвет для hover-эффекта"""
        # Простая реализация - можно улучшить
        color_map = {
            '#3498db': '#2980b9',
            '#2ecc71': '#27ae60',
            '#f39c12': '#d68910',
            '#95a5a6': '#7f8c8d',
            '#9b59b6': '#8e44ad',
            '#27ae60': '#229954',
            '#e74c3c': '#c0392b',
        }
        return color_map.get(color, color)
    
    def create_services_tab(self):
        """Создает вкладку с услугами (карточный интерфейс)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Заголовок
        header = QLabel("⚙️ Справочник услуг")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # === ПОИСК И КНОПКИ ===
        top_layout = QHBoxLayout()
        
        # Поиск
        search_label = QLabel("🔍 Поиск:")
        top_layout.addWidget(search_label)
        
        self.services_search = QLineEdit()
        self.services_search.setPlaceholderText("Название услуги...")
        self.services_search.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.services_search.textChanged.connect(self.filter_services)
        top_layout.addWidget(self.services_search)
        
        top_layout.addStretch()
        
        # Кнопка добавления
        self.btn_add_service = QPushButton("➕ Добавить услугу")
        self.btn_add_service.clicked.connect(self.add_service)
        self.btn_add_service.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        top_layout.addWidget(self.btn_add_service)
        
        layout.addLayout(top_layout)
        
        # === КАТЕГОРИИ ===
        categories_layout = QHBoxLayout()
        categories_layout.addWidget(QLabel("📂 Категория:"))
        
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Все категории", "Мойка", "Дополнительные", "Покрытия"])
        self.category_filter.currentIndexChanged.connect(self.filter_services)
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        categories_layout.addWidget(self.category_filter)
        categories_layout.addStretch()
        
        layout.addLayout(categories_layout)
        
        # === КАРТОЧКИ УСЛУГ (Scroll Area) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #f5f5f5;")
        
        self.services_container = QWidget()
        self.services_layout = QVBoxLayout(self.services_container)
        self.services_layout.setSpacing(15)
        self.services_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.services_container)
        layout.addWidget(scroll)
        
        # Загружаем услуги
        self.load_services()
        
        return tab
    
    def get_category_color(self, service_name):
        """Определяет цвет карточки по категории"""
        service_name = service_name.lower()
        
        if any(word in service_name for word in ['мойка', 'комплекс']):
            return '#3498db'  # Синий - мойка
        elif any(word in service_name for word in ['антидождь', 'чернение', 'коврики']):
            return '#f39c12'  # Оранжевый - допы
        elif any(word in service_name for word in ['воск', 'кварц', 'покрытие']):
            return '#9b59b6'  # Фиолетовый - покрытия
        else:
            return '#95a5a6'  # Серый - остальное
    
    def get_category_name(self, service_name):
        """Определяет категорию услуги"""
        service_name = service_name.lower()
        
        if any(word in service_name for word in ['мойка', 'комплекс']):
            return 'Мойка'
        elif any(word in service_name for word in ['антидождь', 'чернение', 'коврики']):
            return 'Дополнительные'
        elif any(word in service_name for word in ['воск', 'кварц', 'покрытие']):
            return 'Покрытия'
        else:
            return 'Другое'
    
    def load_services(self):
        """Загружает услуги в виде карточек"""
        # Очищаем контейнер
        while self.services_layout.count():
            item = self.services_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, duration_min FROM services ORDER BY name")
        services = cursor.fetchall()
        conn.close()
        
        if not services:
            empty_label = QLabel("📭 Услуги не найдены")
            empty_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_layout.addWidget(empty_label)
            return
        
        # Создаем карточки
        for service in services:
            card = self.create_service_card(service)
            self.services_layout.addWidget(card)
        
        self.services_layout.addStretch()
    
    def create_service_card(self, service):
        """Создает карточку услуги"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Определяем цвет по категории
        color = self.get_category_color(service['name'])
        category = self.get_category_name(service['name'])
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 5px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
        layout = QHBoxLayout(card)
        
        # Иконка категории
        icon_label = QLabel(self.get_category_icon(category))
        icon_label.setStyleSheet(f"font-size: 32px; padding: 10px;")
        layout.addWidget(icon_label)
        
        # Информация об услуге
        info_layout = QVBoxLayout()
        
        name_label = QLabel(f"<b>{service['name']}</b>")
        name_label.setStyleSheet("font-size: 16px; color: #2c3e50;")
        info_layout.addWidget(name_label)
        
        details_layout = QHBoxLayout()
        
        price_label = QLabel(f"💰 {service['price']:.0f} ₽")
        price_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        details_layout.addWidget(price_label)
        
        if service['duration_min']:
            time_label = QLabel(f"⏱ {service['duration_min']} мин")
            time_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
            details_layout.addWidget(time_label)
        
        category_label = QLabel(f"📂 {category}")
        category_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
        details_layout.addWidget(category_label)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Кнопки действий
        btn_layout = QHBoxLayout()
        
        btn_edit = QPushButton("✏️")
        btn_edit.setToolTip("Редактировать")
        btn_edit.setFixedSize(40, 40)
        btn_edit.clicked.connect(lambda checked, sid=service['id']: self.edit_service(sid))
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️")
        btn_delete.setToolTip("Удалить")
        btn_delete.setFixedSize(40, 40)
        btn_delete.clicked.connect(lambda checked, sid=service['id']: self.delete_service(sid))
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(btn_layout)
        
        return card
    
    def get_category_icon(self, category):
        """Возвращает иконку для категории"""
        icons = {
            'Мойка': '🧽',
            'Дополнительные': '➕',
            'Покрытия': '✨',
            'Другое': '📦'
        }
        return icons.get(category, '📦')
    
    def filter_services(self):
        """Фильтрует услуги по поиску и категории"""
        search_text = self.services_search.text().lower()
        category = self.category_filter.currentText()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, duration_min FROM services ORDER BY name")
        all_services = cursor.fetchall()
        conn.close()
        
        # Очищаем контейнер
        while self.services_layout.count():
            item = self.services_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        filtered = False
        
        for service in all_services:
            # Фильтр по поиску
            if search_text and search_text not in service['name'].lower():
                continue
            
            # Фильтр по категории
            service_category = self.get_category_name(service['name'])
            if category != "Все категории" and service_category != category:
                continue
            
            card = self.create_service_card(service)
            self.services_layout.addWidget(card)
            filtered = True
        
        if not filtered:
            empty_label = QLabel("📭 Услуги не найдены")
            empty_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_layout.addWidget(empty_label)
        
        self.services_layout.addStretch()
    
    def add_service(self):
        """Добавляет новую услугу"""
        from ui.services_editor import ServicesEditorDialog
        dialog = ServicesEditorDialog(self)
        if dialog.exec() == 1:
            self.load_services()
            QMessageBox.information(self, "✅ Успешно", "Услуга добавлена!")
    
    def edit_service(self, service_id):
        """Редактирует услугу"""
        from ui.services_editor import ServicesEditorDialog
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, duration_min FROM services WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        conn.close()
        
        if not service:
            return
        
        dialog = ServicesEditorDialog(self, service_id=service_id)
        if dialog.exec() == 1:
            self.load_services()
            QMessageBox.information(self, "✅ Успешно", "Услуга обновлена!")
    
    def delete_service(self, service_id):
        """Удаляет услугу"""
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            "Вы уверены, что хотите удалить эту услугу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()
        conn.close()
        
        self.load_services()
        QMessageBox.information(self, "✅ Успешно", "Услуга удалена!")

    def focus_search(self):
        """Переводит фокус на поле поиска"""
        if hasattr(self, 'orders_search'):
            self.orders_search.setFocus()
            self.orders_search.selectAll()
    
    def on_order_double_click(self, index):
        """Обработка двойного клика по заказу"""
        row = index.row()
        if row < 0:
            return
        
        order_id_item = self.orders_table.item(row, 0)
        if not order_id_item:
            return
        
        order_id = int(order_id_item.text())
        self.change_order_status(order_id)
    
    def change_order_status(self, order_id):
        """Меняет статус заказа"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем текущий статус
        cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        current_status = row['status']
        
        # Переключаем статусы: queue -> process -> done -> queue
        status_map = {
            'queue': 'process',
            'process': 'done',
            'done': 'queue'
        }
        new_status = status_map.get(current_status, 'queue')
        
        # Обновляем статус
        cursor.execute("""
            UPDATE orders 
            SET status = ? 
            WHERE id = ?
        """, (new_status, order_id))
        conn.commit()
        conn.close()
        
        # Перезагружаем таблицу
        self.load_orders()
        self.statusBar().showMessage(f"✅ Статус заказа {order_id} изменён")
    
    def translate_status(self, status: str) -> str:
        """Переводит статусы на русский"""
        statuses = {
            'queue': '🟡 В очереди',
            'process': '🔵 В работе',
            'done': '🟢 Готово',
            'cancelled': '🔴 Отменено'
        }
        return statuses.get(status, status)
    
    def load_statistics(self):
        """Обновляет статистику в карточках"""
        conn = get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Заказы сегодня
        cursor.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE DATE(created_at) = ?
        """, (today,))
        today_orders = cursor.fetchone()[0]
        
        # Выручка сегодня (только выполненные)
        cursor.execute("""
            SELECT COALESCE(SUM(oi.final_price * oi.quantity), 0) 
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) = ? AND o.status IN ('process', 'done')
        """, (today,))
        today_revenue = cursor.fetchone()[0]
        
        # В работе сейчас
        cursor.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE status = 'process'
        """)
        in_progress = cursor.fetchone()[0]
        
        conn.close()
        
        # 🔧 ОБНОВЛЯЕМ НОВЫЕ КАРТОЧКИ
        if hasattr(self, 'today_label'):
            self.today_label.setText(f"📋 Сегодня\n{today_orders} заказов")
        
        if hasattr(self, 'revenue_label'):
            self.revenue_label.setText(f"💰 Выручка\n{today_revenue:.0f} ₽")
        
        if hasattr(self, 'in_progress_label'):
            self.in_progress_label.setText(f"🔵 В работе\n{in_progress}")

    def setup_hotkeys(self):
        """Настраивает горячие клавиши"""
        
        # === ГЛОБАЛЬНЫЕ ===
        
        # Ctrl+N - Новый заказ
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self.add_order)
        
        # F5 - Обновить
        shortcut = QShortcut(QKeySequence("F5"), self)
        shortcut.activated.connect(self.load_orders)
        
        # F12 - Смены
        shortcut = QShortcut(QKeySequence("F12"), self)
        shortcut.activated.connect(self.open_shift_manager)
        
        # Ctrl+F - Фокус на поиск
        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.focus_search)
        
        # === НАВИГАЦИЯ ПО ВКЛАДКАМ ===
        
        # Ctrl+1 - Заказы
        shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(0))
        
        # Ctrl+2 - Услуги
        shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(1))
        
        # Ctrl+3 - Клиенты
        shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(2))
        
        # Ctrl+4 - Отчёты
        shortcut = QShortcut(QKeySequence("Ctrl+4"), self)
        shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(3))
        
        # Ctrl+5 - Настройки
        shortcut = QShortcut(QKeySequence("Ctrl+5"), self)
        shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(4))
    
    def add_order(self):
        """Открывает форму добавления заявки"""
        from services.user_service import user_service
        if not user_service.has_permission('create_order'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для создания заказов!")
            return
        
        """Открывает форму добавления заявки (с поддержкой N услуг)"""
        from ui.order_form_multi import OrderFormMultiDialog
        
        dialog = OrderFormMultiDialog(self)
        result = dialog.exec()
        
        if result == 1:  # QDialog.Accepted
            self.load_orders()
            self.load_statistics()
            self.statusBar().showMessage("✅ Заказ добавлен")

    def export_to_excel(self):
        """Экспорт в Excel"""
        from services.user_service import user_service
        if not user_service.has_permission('export_reports'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для экспорта отчётов!")
            return

        """Экспортирует заказы в Excel с форматированием"""
        from datetime import datetime
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        # Получаем данные из БД
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                o.id,
                o.created_at,
                o.car_number,
                o.car_model,
                o.client_phone,
                GROUP_CONCAT(s.name, ', ') as services_list,
                o.status,
                COALESCE(o.total_price, 0) as total_price,
                o.payment_method,
                o.comment
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
        
        # Получаем общую статистику
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_price), 0) as total_revenue
            FROM orders
        """)
        stats = cursor.fetchone()
        
        # Получаем статистику по способам оплаты
        cursor.execute("""
            SELECT 
                payment_method,
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as amount
            FROM orders
            GROUP BY payment_method
        """)
        payment_rows = cursor.fetchall()
        
        conn.close()
        
        # Формируем статистику
        statistics = {
            'total_orders': stats['total_orders'] if stats else 0,
            'total_revenue': stats['total_revenue'] if stats else 0,
            'cash_count': 0,
            'cash_amount': 0,
            'card_count': 0,
            'card_amount': 0,
            'transfer_count': 0,
            'transfer_amount': 0,
            'sbp_count': 0,
            'sbp_amount': 0,
        }
        
        # Заполняем статистику по оплате с нормализацией
        for row in payment_rows:
            method = (row['payment_method'] or '').lower()
            count = row['count'] or 0
            amount = row['amount'] or 0
            
            if method in ['нал', 'наличные', 'cash']:
                statistics['cash_count'] += count
                statistics['cash_amount'] += amount
            elif method in ['карта', 'card']:
                statistics['card_count'] += count
                statistics['card_amount'] += amount
            elif method in ['перевод', 'transfer']:
                statistics['transfer_count'] += count
                statistics['transfer_amount'] += amount
            elif method in ['сбп', 'sbp']:
                statistics['sbp_count'] += count
                statistics['sbp_amount'] += amount
            else:
                statistics['cash_count'] += count
                statistics['cash_amount'] += amount
        
        # Выбор файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"orders_report_{timestamp}.xlsx"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "📊 Сохранить отчёт Excel",
            default_filename,
            "Excel файлы (*.xlsx);;Все файлы (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            exporter = ExcelExporter()
            saved_path = exporter.export_orders(
                orders=[dict(row) for row in orders],
                statistics=statistics,
                filepath=filepath
            )
            
            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"Отчёт сохранён:\n{saved_path}\n\n"
                f"Заказов: {len(orders)}\n"
                f"Выручка: {statistics['total_revenue']:.0f} ₽"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Ошибка экспорта",
                f"Не удалось создать Excel файл:\n{str(e)}"
            )
    
    # Оставляем старый метод для совместимости
    def export_to_csv(self):
        """Перенаправляет на Excel экспорт"""
        self.export_to_excel()
            
    def open_services_editor(self):
        """Открывает редактор услуг"""
        from ui.services_editor import ServicesEditorDialog
        dialog = ServicesEditorDialog(self)
        dialog.exec()

    def delete_order(self, order_id):
        """Удаление заказа"""
        from services.user_service import user_service
        if not user_service.has_permission('delete_order'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для удаления заказов!")
            return

        """Удаляет заказ"""
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            f"Вы уверены, что хотите удалить заказ ID={order_id}?\n\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            
            self.load_orders()
            self.load_statistics()
            self.statusBar().showMessage(f"✅ Заказ {order_id} удалён")

    def edit_order(self, order_id):
        """Редактирование заказа"""
        from services.user_service import user_service
        if not user_service.has_permission('edit_order'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для редактирования заказов!")
            return
        
        """Открывает форму редактирования заказа"""
        from ui.order_form_multi import OrderFormMultiDialog
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем данные заказа
        cursor.execute("""
            SELECT id, car_number, car_model, client_phone, 
                   car_class_id, total_price, payment_method, comment
            FROM orders WHERE id = ?
        """, (order_id,))
        order = cursor.fetchone()
        
        # Получаем услуги заказа
        cursor.execute("""
            SELECT service_id, quantity, final_price
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        services = cursor.fetchall()
        conn.close()
        
        if not order:
            return
        
        # Открываем форму с данными
        dialog = OrderFormMultiDialog(
            self, 
            order_id=order_id, 
            order_data=dict(order), 
            services=services
        )
        result = dialog.exec()
        
        if result == 1:
            self.load_orders()
            self.load_statistics()
            self.statusBar().showMessage("✅ Заказ обновлён")

    def open_shift_manager(self):
        """Открывает управление сменами"""
        dialog = ShiftManagerDialog(self)
        dialog.exec()
        self.load_orders()
        self.load_statistics()

    def eventFilter(self, obj, event):
        """Перехватывает события для горячих клавиш в таблице"""
        
        if obj == self.orders_table and event.type() == QEvent.Type.KeyPress:
            # F2 - Редактировать
            if event.key() == Qt.Key.Key_F2:
                row = self.orders_table.currentRow()
                if row >= 0:
                    order_id_item = self.orders_table.item(row, 0)
                    if order_id_item:
                        self.edit_order(int(order_id_item.text()))
                return True
            
            # Delete - Удалить
            if event.key() == Qt.Key.Key_Delete:
                row = self.orders_table.currentRow()
                if row >= 0:
                    order_id_item = self.orders_table.item(row, 0)
                    if order_id_item:
                        self.delete_order(int(order_id_item.text()))
                return True
            
            # Enter - Сменить статус
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                row = self.orders_table.currentRow()
                if row >= 0:
                    order_id_item = self.orders_table.item(row, 0)
                    if order_id_item:
                        self.change_order_status(int(order_id_item.text()))
                return True
        
        return super().eventFilter(obj, event)
    
    def check_backup_on_startup(self):
        """Проверяет настройки бэкапа при запуске"""
        from backup_manager import BackupManager
        from logger import log_info

        print("\n🔍 Проверка бэкапа при запуске...")
        
        backup_manager = BackupManager()
        backup_manager.load_settings()

        print(f"   Enabled: {backup_manager.backup_enabled}")
        print(f"   Folder: {backup_manager.backup_folder}")
        print(f"   is_configured: {backup_manager.is_configured()}")
        
        # Если бэкап не настроен
        if not backup_manager.is_configured():
            log_info("⚠️ Бэкап не настроен!")
            
            reply = QMessageBox.warning(
                self, "⚠️ Бэкап не настроен",
                "Резервное копирование не настроено!\n\n"
                "Рекомендуем настроить автобэкап в настройках программы,\n"
                "чтобы не потерять данные в случае сбоя.\n\n"
                "Открыть настройки бэкапа?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Переключаем на вкладку настроек (индекс 4)
                self.tabs.setCurrentIndex(4)
        
        # Если бэкап настроен, но старый
        info = backup_manager.get_last_backup_info()
        if info['status'] in ['warning', 'critical']:
            log_info(f"⚠️ Последний бэкап: {info['message']}")
            
            QMessageBox.warning(
                self, "⚠️ Старый бэкап",
                f"Последний бэкап был: {info['message']}\n\n"
                "Рекомендуем создать свежую резервную копию!",
                QMessageBox.StandardButton.Ok
            )
    
    def check_auto_backup(self):
        """Проверяет нужно ли делать автобэкап (вызывается каждую минуту)"""
        from backup_manager import BackupManager
        from logger import log_info, log_backup

        print(f"\n🕐 [{datetime.now().strftime('%H:%M:%S')}] Проверка автобэкапа...")
        
        backup_manager = BackupManager()
        backup_manager.load_settings()

        print(f"   Enabled: {backup_manager.backup_enabled}")
        print(f"   Folder: {backup_manager.backup_folder}")
        print(f"   Day: {backup_manager.backup_day} (сейчас {datetime.now().weekday()})")
        print(f"   Time: {backup_manager.backup_time} (сейчас {datetime.now().strftime('%H:%M')})")
        print(f"   Last: {backup_manager.last_backup}")
        
        if backup_manager.should_backup_now():
            print("   ✅ Время бэкапа!")
            log_info("🕐 Время автобэкапа!")
            
            success, path = backup_manager.create_backup()
            log_backup(success, path)
            
            if success:
                self.statusBar().showMessage("✅ Автобэкап создан", 5000)
            else:
                self.statusBar().showMessage("❌ Автобэкап не создан", 5000)
                QMessageBox.warning(
                    self, "⚠️ Автобэкап",
                    f"Не удалось создать автоматический бэкап:\n{path}"
                )

        else:
            print("   ❌ Не время для бэкапа")

    def check_and_enforce_license(self):
        """
        Проверяет лицензию и блокирует интерфейс если истекла
        Возвращает: (is_allowed, message)
        """
        from license_manager import LicenseManager
        from PyQt6.QtWidgets import QMessageBox
        
        license_mgr = LicenseManager()
        license_mgr.load_license()
        is_valid, message = license_mgr.is_valid()
        
        # Если лицензия валидна — всё ок
        if is_valid:
            # Дополнительная проверка: если мало дней — предупредить но не блокировать
            info = license_mgr.get_license_info()
            if info.get('days_left') is not None and 0 < info['days_left'] <= 7:
                # Предупреждение но не блокировка
                QMessageBox.warning(
                    self, "⚠️ Лицензия истекает",
                    f"Осталось дней: {info['days_left']}\n\n"
                    f"Продлите лицензию чтобы продолжить работу без перерывов.\n"
                    f"📧 andreykrivtsov94@gmail.com",
                    QMessageBox.StandardButton.Ok
                )
            return True, "OK"
        
        # ❌ Лицензия не валидна — блокируем интерфейс
        reply = QMessageBox.critical(
            self, "❌ Лицензия истекла",
            f"{message}\n\n"
            f"Для продолжения работы введите новый лицензионный ключ.\n\n"
            f"📧 andreykrivtsov94@gmail.com\n"
            f"📱 +7 (XXX) XXX-XX-XX\n\n"
            f"Открыть настройки для активации?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Переключаем на вкладку настроек
            self.tabs.setCurrentIndex(4)  # Индекс вкладки "Настройки"
            # Блокируем все вкладки кроме настроек
            for i in range(self.tabs.count()):
                if i != 4:
                    self.tabs.widget(i).setEnabled(False)
            return False, "BLOCKED_SHOW_SETTINGS"
        else:
            # Пользователь выбрал "Нет" — закрываем приложение
            return False, "EXIT"