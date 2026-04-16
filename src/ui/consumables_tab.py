# src/ui/consumables_tab.py
"""
Вкладка учёта расходных материалов
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from datetime import date
from services.consumable_service import consumable_service
from models.consumable import Consumable


class ConsumablesTab(QWidget):
    """Вкладка управления расходными материалами"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = consumable_service
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок и статистика
        header_layout = QHBoxLayout()
        
        title = QLabel("🧴 Расходные материалы")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.stats_label = QLabel("📊 Загрузка...")
        self.stats_label.setStyleSheet("""
            font-size: 14px;
            padding: 8px 15px;
            background-color: #e3f2fd;
            border-radius: 6px;
            color: #2c3e50;
        """)
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Предупреждение о низком запасе
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("""
            font-size: 13px;
            padding: 10px 15px;
            background-color: #fef9e7;
            border-left: 4px solid #f39c12;
            border-radius: 4px;
            color: #e67e22;
        """)
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)
        
        # Кнопки действий
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_add.clicked.connect(self.add_consumable)
        self.btn_add.setStyleSheet(self.get_btn_style("#27ae60"))
        btn_layout.addWidget(self.btn_add)
        
        self.btn_restock = QPushButton("📦 Пополнить")
        self.btn_restock.clicked.connect(self.restock_consumable)
        self.btn_restock.setStyleSheet(self.get_btn_style("#3498db"))
        btn_layout.addWidget(self.btn_restock)
        
        self.btn_use = QPushButton("📉 Списать")
        self.btn_use.clicked.connect(self.use_consumable)
        self.btn_use.setStyleSheet(self.get_btn_style("#f39c12"))
        btn_layout.addWidget(self.btn_use)
        
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.clicked.connect(self.edit_consumable)
        self.btn_edit.setStyleSheet(self.get_btn_style("#9b59b6"))
        btn_layout.addWidget(self.btn_edit)
        
        self.btn_history = QPushButton("📋 История")
        self.btn_history.clicked.connect(self.show_history)
        self.btn_history.setStyleSheet(self.get_btn_style("#95a5a6"))
        btn_layout.addWidget(self.btn_history)
        
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self.delete_consumable)
        self.btn_delete.setStyleSheet(self.get_btn_style("#e74c3c"))
        btn_layout.addWidget(self.btn_delete)
        
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_refresh.setStyleSheet(self.get_btn_style("#34495e"))
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # Таблица расходников
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Название", "Ед.изм", "Остаток", "Мин.запас", "Статус", "Цена"
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
                background-color: white;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        # Скрываем кнопки если нет прав
        if not self.service._check_permission('manage_consumables'):
            self.btn_add.setVisible(False)
            self.btn_restock.setVisible(False)
            self.btn_use.setVisible(False)
            self.btn_edit.setVisible(False)
            self.btn_delete.setVisible(False)
    
    def get_btn_style(self, color: str) -> str:
        """Стиль для кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
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
            '#34495e': '#2c3e50',
        }
        return color_map.get(color, color)
    
    def load_data(self):
        """Загружает данные"""
        consumables = self.service.get_all()
        stats = self.service.get_stats()
        low_stock = self.service.get_low_stock()
        
        # Обновляем статистику
        low_total = stats.low_stock_count + stats.empty_count
        self.stats_label.setText(
            f"📊 Всего: {stats.total_items} | "
            f"⚠️ Мало/пусто: {low_total} | "
            f"💰 Стоимость: {stats.total_cost:.0f} ₽"
        )
        
        # Предупреждение
        if low_total > 0:
            names = [c.name for c in low_stock[:3]]
            self.warning_label.setText(f"⚠️ Низкий запас: {', '.join(names)}" + 
                                       (f" и ещё {len(low_stock)-3}..." if len(low_stock) > 3 else ""))
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setVisible(False)
        
        # Заполняем таблицу
        self.table.setRowCount(len(consumables))
        for row_idx, c in enumerate(consumables):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(c.name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(c.unit))
            self.table.setItem(row_idx, 3, QTableWidgetItem(c.formatted_stock))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{c.min_stock:.0f} {c.unit}"))
            
            from PyQt6.QtGui import QColor
            
            status_item = QTableWidgetItem(c.stock_status_display)
            if c.stock_status == 'empty':
                status_item.setForeground(QColor('#e74c3c'))
            elif c.stock_status == 'low':
                status_item.setForeground(QColor('#f39c12'))
            else:
                status_item.setForeground(QColor('#27ae60'))
            self.table.setItem(row_idx, 5, status_item)
            
            self.table.setItem(row_idx, 6, QTableWidgetItem(c.formatted_cost))
            
            # Сохраняем ID
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, c.id)
    
    def get_selected_id(self) -> int:
        """Возвращает ID выбранного расходника"""
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    
    def add_consumable(self):
        """Добавляет расходник"""
        dialog = ConsumableEditDialog(self, mode='add')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def edit_consumable(self):
        """Редактирует расходник"""
        consumable_id = self.get_selected_id()
        if not consumable_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите расходник!")
            return
        
        consumable = self.service.get_by_id(consumable_id)
        if not consumable:
            return
        
        dialog = ConsumableEditDialog(self, mode='edit', consumable=consumable)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def restock_consumable(self):
        """Пополняет запас"""
        consumable_id = self.get_selected_id()
        if not consumable_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите расходник!")
            return
        
        consumable = self.service.get_by_id(consumable_id)
        if not consumable:
            return
        
        dialog = StockDialog(self, mode='restock', consumable=consumable)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            quantity = dialog.quantity_spin.value()
            if self.service.add_stock(consumable_id, quantity):
                QMessageBox.information(self, "✅ Успешно", f"Запас пополнен на {quantity} {consumable.unit}")
                self.load_data()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось пополнить запас")
    
    def use_consumable(self):
        """Списывает материал"""
        consumable_id = self.get_selected_id()
        if not consumable_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите расходник!")
            return
        
        consumable = self.service.get_by_id(consumable_id)
        if not consumable:
            return
        
        dialog = StockDialog(self, mode='use', consumable=consumable)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            quantity = dialog.quantity_spin.value()
            notes = dialog.notes_edit.text().strip()
            
            if quantity > consumable.current_stock:
                QMessageBox.warning(self, "⚠️ Ошибка", "Недостаточно материала на складе!")
                return
            
            if self.service.use_stock(consumable_id, quantity, notes=notes if notes else None):
                QMessageBox.information(self, "✅ Успешно", f"Списано {quantity} {consumable.unit}")
                self.load_data()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось списать материал")
    
    def delete_consumable(self):
        """Удаляет расходник"""
        consumable_id = self.get_selected_id()
        if not consumable_id:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите расходник!")
            return
        
        consumable = self.service.get_by_id(consumable_id)
        if not consumable:
            return
        
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            f"Удалить расходник '{consumable.name}'?\n\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.service.delete(consumable_id):
                QMessageBox.information(self, "✅ Успешно", "Расходник удалён")
                self.load_data()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось удалить расходник")
    
    def show_history(self):
        """Показывает историю списаний"""
        consumable_id = self.get_selected_id()
        dialog = HistoryDialog(self, consumable_id)
        dialog.exec()


class ConsumableEditDialog(QDialog):
    """Диалог добавления/редактирования расходника"""
    
    def __init__(self, parent=None, mode='add', consumable: Consumable = None):
        super().__init__(parent)
        self.mode = mode
        self.consumable = consumable
        self.setWindowTitle("➕ Новый расходник" if mode == 'add' else "✏️ Редактировать расходник")
        self.setFixedSize(400, 350)
        self.setModal(True)
        
        self.setup_ui()
        
        if mode == 'edit' and consumable:
            self.fill_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название материала")
        self.name_edit.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Название:", self.name_edit)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(['шт', 'литр', 'кг', 'мл', 'г', 'упаковка'])
        self.unit_combo.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Ед. измерения:", self.unit_combo)
        
        self.stock_spin = QDoubleSpinBox()
        self.stock_spin.setRange(0, 10000)
        self.stock_spin.setSuffix("")
        self.stock_spin.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Текущий остаток:", self.stock_spin)
        
        self.min_stock_spin = QDoubleSpinBox()
        self.min_stock_spin.setRange(0, 10000)
        self.min_stock_spin.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Мин. запас:", self.min_stock_spin)
        
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 100000)
        self.cost_spin.setSuffix(" ₽")
        self.cost_spin.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Цена за единицу:", self.cost_spin)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self.save)
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
        self.name_edit.setText(self.consumable.name)
        
        index = self.unit_combo.findText(self.consumable.unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)
        
        self.stock_spin.setValue(self.consumable.current_stock)
        self.min_stock_spin.setValue(self.consumable.min_stock)
        self.cost_spin.setValue(self.consumable.cost_per_unit)
    
    def save(self):
        """Сохраняет расходник"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите название!")
            return
        
        data = {
            'name': name,
            'unit': self.unit_combo.currentText(),
            'current_stock': self.stock_spin.value(),
            'min_stock': self.min_stock_spin.value(),
            'cost_per_unit': self.cost_spin.value()
        }
        
        if self.mode == 'add':
            consumable_id = consumable_service.create(data)
            if consumable_id:
                QMessageBox.information(self, "✅ Успешно", "Расходник создан!")
                self.accept()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось создать расходник")
        else:
            if consumable_service.update(self.consumable.id, data):
                QMessageBox.information(self, "✅ Успешно", "Расходник обновлён!")
                self.accept()
            else:
                QMessageBox.critical(self, "❌ Ошибка", "Не удалось обновить расходник")


class StockDialog(QDialog):
    """Диалог пополнения/списания"""
    
    def __init__(self, parent=None, mode='restock', consumable: Consumable = None):
        super().__init__(parent)
        self.mode = mode
        self.consumable = consumable
        self.setWindowTitle("📦 Пополнить запас" if mode == 'restock' else "📉 Списать материал")
        self.setFixedSize(350, 220 if mode == 'restock' else 280)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        info = QLabel(f"Материал: {self.consumable.name}\nТекущий остаток: {self.consumable.formatted_stock}")
        info.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(info)
        
        form_layout = QFormLayout()
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.1, 10000)
        self.quantity_spin.setSingleStep(0.5)
        self.quantity_spin.setSuffix(f" {self.consumable.unit}")
        self.quantity_spin.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        form_layout.addRow("Количество:", self.quantity_spin)
        
        layout.addLayout(form_layout)
        
        if self.mode == 'use':
            layout.addWidget(QLabel("Примечание:"))
            self.notes_edit = QLineEdit()
            self.notes_edit.setPlaceholderText("Например: для заказа №123")
            self.notes_edit.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
            layout.addWidget(self.notes_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("✅ Подтвердить")
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


class HistoryDialog(QDialog):
    """Диалог истории списаний"""
    
    def __init__(self, parent=None, consumable_id: int = None):
        super().__init__(parent)
        self.consumable_id = consumable_id
        self.setWindowTitle("📋 История списаний")
        self.setMinimumSize(700, 400)
        self.setModal(True)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Материал", "Количество", "Заказ", "Примечание"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
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
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
    
    def load_data(self):
        """Загружает историю"""
        history = consumable_service.get_usage_history(self.consumable_id, limit=200)
        
        self.table.setRowCount(len(history))
        for row_idx, h in enumerate(history):
            self.table.setItem(row_idx, 0, QTableWidgetItem(h.formatted_date))
            self.table.setItem(row_idx, 1, QTableWidgetItem(h.consumable_name or "—"))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{h.quantity}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"#{h.order_id}" if h.order_id else "—"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(h.notes or "—"))