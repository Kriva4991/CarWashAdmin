# src/ui/services_editor.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLineEdit, QDoubleSpinBox, QSpinBox, QMessageBox,
    QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
from database import get_connection

class ServicesEditorDialog(QDialog):
    def __init__(self, parent=None, service_id=None):
        super().__init__(parent)
        self.service_id = service_id
        self.setWindowTitle("⚙️ Редактор услуг")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        self.setup_ui()
        
        # 🔧 Если передан service_id - открываем редактирование
        if service_id:
            self.edit_service(service_id)
        else:
            self.load_services()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        header = QLabel("📋 Управление услугами и ценами")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Таблица услуг
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Название", "Цена (₽)", "Время (мин)", "Действия"
        ])
        self.services_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.services_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.services_table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Добавить услугу")
        btn_add.clicked.connect(self.add_service)
        btn_add.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #4CAF50; color: white;")
        
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.load_services)
        btn_refresh.setStyleSheet("padding: 8px 15px;")
        
        btn_close = QPushButton("❌ Закрыть")
        btn_close.clicked.connect(self.reject)
        btn_close.setStyleSheet("padding: 8px 15px;")
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def load_services(self):
        """Загружает услуги в таблицу"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, duration_min FROM services ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        
        self.services_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.services_table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.services_table.setItem(row_idx, 1, QTableWidgetItem(row['name']))
            self.services_table.setItem(row_idx, 2, QTableWidgetItem(f"{row['price']:.0f} ₽"))
            self.services_table.setItem(row_idx, 3, QTableWidgetItem(str(row['duration_min'])))
            
            # Кнопка удаления
            btn_delete = QPushButton("🗑️ Удалить")
            btn_delete.setStyleSheet("padding: 5px; background-color: #f44336; color: white;")
            btn_delete.clicked.connect(lambda checked, rid=row['id']: self.delete_service(rid))
            self.services_table.setCellWidget(row_idx, 4, btn_delete)
    
    def add_service(self):
        from services.user_service import user_service
        if not user_service.has_permission('manage_services'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для управления услугами!")
            return

        """Открывает диалог добавления услуги"""
        dialog = ServiceFormDialog(self, mode='add')
        if dialog.exec() == 1:
            self.load_services()
            self.parent().load_services() if hasattr(self.parent(), 'load_services') else None
    
    def edit_service(self, service_id):
        from services.user_service import user_service
        if not user_service.has_permission('manage_services'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для управления услугами!")
            return

        """Открывает диалог редактирования услуги"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, duration_min FROM services WHERE id = ?", (service_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            dialog = ServiceFormDialog(self, mode='edit', service_data=dict(row))
            if dialog.exec() == 1:
                self.load_services()
                self.parent().load_services() if hasattr(self.parent(), 'load_services') else None
    
    def delete_service(self, service_id):
        from services.user_service import user_service
        if not user_service.has_permission('manage_services'):
            QMessageBox.warning(self, "⛔ Доступ запрещён", "У вас нет прав для управления услугами!")
            return

        """Удаляет услугу"""
        reply = QMessageBox.question(
            self, "⚠️ Подтверждение",
            f"Вы уверены, что хотите удалить услугу ID={service_id}?\n\n"
            "Это может повлиять на существующие заказы!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            conn.commit()
            conn.close()
            
            self.load_services()
            self.parent().load_services() if hasattr(self.parent(), 'load_services') else None
            QMessageBox.information(self, "✅ Удалено", "Услуга удалена.")

class ServiceFormDialog(QDialog):
    """Форма добавления/редактирования услуги"""
    def __init__(self, parent=None, mode='add', service_data=None):
        super().__init__(parent)
        self.mode = mode
        self.service_data = service_data
        self.setWindowTitle("➕ Добавить услугу" if mode == 'add' else "✏️ Редактировать услугу")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        if mode == 'edit' and service_data:
            self.fill_data(service_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Антидождь")
        self.name_edit.setStyleSheet("padding: 8px;")
        form_layout.addRow("Название *", self.name_edit)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 100000)
        self.price_spin.setSuffix(" ₽")
        self.price_spin.setStyleSheet("padding: 8px;")
        form_layout.addRow("Цена *", self.price_spin)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 480)
        self.duration_spin.setSuffix(" мин")
        self.duration_spin.setStyleSheet("padding: 8px;")
        form_layout.addRow("Время *", self.duration_spin)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.setStyleSheet("padding: 8px 20px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_save.clicked.connect(self.save_service)
        
        self.btn_cancel = QPushButton("❌ Отмена")
        self.btn_cancel.setStyleSheet("padding: 8px 20px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
    
    def fill_data(self, data):
        self.name_edit.setText(data['name'])
        self.price_spin.setValue(data['price'])
        self.duration_spin.setValue(data['duration_min'])
    
    def save_service(self):
        name = self.name_edit.text().strip()
        price = self.price_spin.value()
        duration = self.duration_spin.value()
        
        if not name:
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите название услуги!")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        if self.mode == 'add':
            cursor.execute(
                "INSERT INTO services (name, price, duration_min) VALUES (?, ?, ?)",
                (name, price, duration)
            )
        else:
            cursor.execute(
                "UPDATE services SET name=?, price=?, duration_min=? WHERE id=?",
                (name, price, duration, self.service_data['id'])
            )
        
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "✅ Успешно", "Услуга сохранена!")
        self.accept()