# src/ui/order_form_multi.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QLabel, QMessageBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from database import get_connection

class OrderFormMultiDialog(QDialog):
    def __init__(self, parent=None, order_id=None, order_data=None, services=None):
        super().__init__(parent)
        
        # 🔧 Сохраняем параметры для редактирования
        self.order_id = order_id
        self.order_data = order_data
        self.services = services or []
        self.is_edit_mode = order_id is not None
        self.selected_services = {}  # ← Инициализируем словарь!
        
        # Заголовок окна
        if self.is_edit_mode:
            self.setWindowTitle("✏️ Редактирование заказа")
        else:
            self.setWindowTitle("➕ Новый заказ")
        
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.load_services()  # ← Загружаем услуги СРАЗУ
        
        # 🔧 Если редактируем — заполняем данные
        if self.is_edit_mode and order_data:
            self.fill_order_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Заголовок ---
        header = QLabel("📝 Данные автомобиля и клиента")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # --- Основная информация ---
        form_layout = QFormLayout()
        
        self.car_number_edit = QLineEdit()
        self.car_number_edit.setPlaceholderText("А 123 АА 77")
        self.car_number_edit.setStyleSheet("padding: 8px;")
        form_layout.addRow("Гос. номер *", self.car_number_edit)
        
        self.car_model_edit = QLineEdit()
        self.car_model_edit.setPlaceholderText("Toyota Camry")
        self.car_model_edit.setStyleSheet("padding: 8px;")
        form_layout.addRow("Марка/Модель", self.car_model_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (999) 000-00-00")
        self.phone_edit.setStyleSheet("padding: 8px;")
        form_layout.addRow("Телефон", self.phone_edit)
        
        self.car_class_combo = QComboBox()
        self.car_class_combo.setStyleSheet("padding: 8px;")
        form_layout.addRow("Класс авто", self.car_class_combo)
        
        layout.addLayout(form_layout)
        
        # --- Таблица услуг ---
        services_label = QLabel("📋 Выберите услуги (можно несколько)")
        services_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 0;")
        layout.addWidget(services_label)
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels([
            "✓", "Услуга", "Базовая цена", "Цена для клиента", "Кол-во"
        ])
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.services_table)
        
        # --- Итоговая сумма ---
        self.total_label = QLabel("💰 Итого: 0 ₽")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px; background-color: #E8F5E9; border-radius: 5px;")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.total_label)
        
        # --- Оплата и комментарий ---
        payment_layout = QHBoxLayout()
        
        payment_layout.addWidget(QLabel("Оплата:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "СБП"])
        self.payment_combo.setStyleSheet("padding: 8px;")
        payment_layout.addWidget(self.payment_combo)
        payment_layout.addStretch()
        
        layout.addLayout(payment_layout)
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(60)
        self.comment_edit.setPlaceholderText("Особые отметки...")
        layout.addWidget(QLabel("Комментарий:"))
        layout.addWidget(self.comment_edit)
        
        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.setStyleSheet("padding: 10px 30px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_save.clicked.connect(self.save_order)
        
        self.btn_cancel = QPushButton("❌ Отмена")
        self.btn_cancel.setStyleSheet("padding: 10px 30px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        # Привязка событий
        self.services_table.cellChanged.connect(self.on_table_changed)

    def fill_order_data(self):
        """Заполняет форму данными существующего заказа"""
        if not self.order_data:
            return
        
        # Заполняем поля
        self.car_number_edit.setText(self.order_data.get('car_number', ''))
        self.car_model_edit.setText(self.order_data.get('car_model', ''))
        self.phone_edit.setText(self.order_data.get('client_phone', ''))  # ← ИСПРАВЛЕНО: phone_edit
        self.comment_edit.setPlainText(self.order_data.get('comment', ''))
        
        # Класс автомобиля
        car_class_id = self.order_data.get('car_class_id')
        if car_class_id:
            index = self.car_class_combo.findData(car_class_id)
            if index >= 0:
                self.car_class_combo.setCurrentIndex(index)
        
        # Способ оплаты
        payment_method = self.order_data.get('payment_method')
        if payment_method:
            index = self.payment_combo.findText(payment_method)
            if index >= 0:
                self.payment_combo.setCurrentIndex(index)
        
        # 🔧 Отмечаем услуги из заказа
        if self.services:
            for service in self.services:
                service_id = service['service_id']
                # Находим строку с этой услугой
                for row_idx in range(self.services_table.rowCount()):
                    checkbox = self.services_table.cellWidget(row_idx, 0)
                    if checkbox:
                        # Проверяем название услуги (костыль, но работает)
                        service_name_item = self.services_table.item(row_idx, 1)
                        if service_name_item:
                            # Получаем ID услуги из self.services_data
                            if row_idx < len(self.services_data):
                                if self.services_data[row_idx]['id'] == service_id:
                                    checkbox.setChecked(True)
                                    # Устанавливаем цену и количество
                                    price_widget = self.services_table.cellWidget(row_idx, 3)
                                    quantity_widget = self.services_table.cellWidget(row_idx, 4)
                                    if price_widget:
                                        price_widget.setValue(service['final_price'])
                                    if quantity_widget:
                                        quantity_widget.setValue(service['quantity'])
        
        # Пересчитываем итог
        self.calculate_total()
    
    def load_services(self):
        """Загружает услуги и классы авто из БД"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Услуги
        cursor.execute("SELECT id, name, price FROM services ORDER BY name")
        self.services_data = cursor.fetchall()
        
        # Классы авто
        cursor.execute("SELECT id, name, coefficient FROM car_classes ORDER BY coefficient")
        car_classes = cursor.fetchall()
        
        conn.close()
        
        # Заполняем таблицу услуг
        self.services_table.setRowCount(len(self.services_data))
        for row_idx, service in enumerate(self.services_data):
            # Чекбокс
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left: 10px;")
            checkbox.stateChanged.connect(lambda state, idx=row_idx: self.on_checkbox_changed(idx, state))
            self.services_table.setCellWidget(row_idx, 0, checkbox)
            
            # Название услуги
            self.services_table.setItem(row_idx, 1, QTableWidgetItem(service['name']))
            
            # Базовая цена (только чтение)
            base_price_item = QTableWidgetItem(f"{service['price']:.0f} ₽")
            base_price_item.setFlags(base_price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            base_price_item.setBackground(Qt.GlobalColor.lightGray)
            self.services_table.setItem(row_idx, 2, base_price_item)
            
            # Цена для клиента (редактируемая)
            final_price_spin = QDoubleSpinBox()
            final_price_spin.setRange(0, 100000)
            final_price_spin.setSuffix(" ₽")
            final_price_spin.setValue(service['price'])
            final_price_spin.valueChanged.connect(self.calculate_total)
            self.services_table.setCellWidget(row_idx, 3, final_price_spin)
            
            # Количество
            quantity_spin = QSpinBox()
            quantity_spin.setRange(1, 10)
            quantity_spin.setValue(1)
            quantity_spin.valueChanged.connect(self.calculate_total)
            self.services_table.setCellWidget(row_idx, 4, quantity_spin)
        
        # Заполняем классы авто
        self.car_class_combo.clear()
        for car_class in car_classes:
            self.car_class_combo.addItem(car_class['name'], car_class['id'])
    
    def on_checkbox_changed(self, row_idx, state):
        """Включение/выключение услуги"""
        service = self.services_data[row_idx]
        service_id = service['id']
        
        if state == Qt.CheckState.Checked.value:
            final_price_widget = self.services_table.cellWidget(row_idx, 3)
            quantity_widget = self.services_table.cellWidget(row_idx, 4)
            
            self.selected_services[service_id] = {
                'row': row_idx,
                'name': service['name'],
                'base': service['price'],
                'final': final_price_widget.value(),
                'quantity': quantity_widget.value()
            }
        else:
            if service_id in self.selected_services:
                del self.selected_services[service_id]
        
        self.calculate_total()
    
    def on_table_changed(self, row, column):
        """Обновление данных при изменении таблицы"""
        if row >= 0 and row < len(self.services_data):
            service_id = self.services_data[row]['id']
            if service_id in self.selected_services:
                final_price_widget = self.services_table.cellWidget(row, 3)
                quantity_widget = self.services_table.cellWidget(row, 4)
                
                self.selected_services[service_id]['final'] = final_price_widget.value()
                self.selected_services[service_id]['quantity'] = quantity_widget.value()
                
                self.calculate_total()
    
    def calculate_total(self):
        """Подсчёт итоговой суммы"""
        total = 0
        for service_id, data in self.selected_services.items():
            total += data['final'] * data['quantity']
        
        self.total_label.setText(f"💰 Итого: {total:.0f} ₽")
    
    def validate(self):
        """Проверка заполненности"""
        if not self.car_number_edit.text().strip():
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите гос. номер автомобиля!")
            return False
        
        if not self.selected_services:
            QMessageBox.warning(self, "⚠️ Ошибка", "Выберите хотя бы одну услугу!")
            return False
        
        return True
    
    def save_order(self):
        """Сохраняет заказ (создание или обновление)"""
        # 🆕 Показываем индикатор загрузки
        self.btn_save.setEnabled(False)
        self.btn_save.setText("⏳ Сохранение...")
        QApplication.processEvents()

        car_number = self.car_number_edit.text().strip()
        car_model = self.car_model_edit.text().strip()
        client_phone = self.phone_edit.text().strip()
        car_class_id = self.car_class_combo.currentData()
        payment_method = self.payment_combo.currentText()
        comment = self.comment_edit.toPlainText().strip()
        
        if not car_number:
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите гос. номер автомобиля!")
            return
        
        # Собираем услуги
        services_data = []
        for service_id, data in self.selected_services.items():
            services_data.append({
                'service_id': service_id,
                'quantity': data['quantity'],
                'price': data['final']
            })
        
        if not services_data:
            QMessageBox.warning(self, "⚠️ Ошибка", "Выберите хотя бы одну услугу!")
            return
        
        # Считаем общую сумму
        total = sum(s['quantity'] * s['price'] for s in services_data)
        
        # 🔧 Сохранение в БД
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Находим или создаём клиента
            client_id = None
            if car_number:
                from repositories.client_repo import ClientRepository
                client_repo = ClientRepository()
                client_id = client_repo.find_or_create_by_car_number(
                    car_number=car_number,
                    car_model=car_model,
                    phone=client_phone
                )
            
            if self.is_edit_mode and self.order_id:
                # Обновление существующего заказа
                cursor.execute("""
                    UPDATE orders SET
                        car_number = ?,
                        car_model = ?,
                        client_phone = ?,
                        client_id = ?,
                        car_class_id = ?,
                        payment_method = ?,
                        comment = ?,
                        total_price = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (car_number, car_model, client_phone, client_id, car_class_id, 
                      payment_method, comment, total, self.order_id))
                
                # Удаляем старые услуги
                cursor.execute("DELETE FROM order_items WHERE order_id = ?", (self.order_id,))
                
                order_id = self.order_id
                message = "✅ Заказ обновлён!"
            else:
                # Создание нового заказа
                cursor.execute("""
                    INSERT INTO orders (
                        car_number, car_model, client_phone, client_id, car_class_id,
                        payment_method, comment, total_price, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queue')
                """, (car_number, car_model, client_phone, client_id, car_class_id,
                      payment_method, comment, total))
                
                order_id = cursor.lastrowid
                self._last_order_id = order_id  #  Сохраняем ID для быстрого добавления
                message = "✅ Заказ создан!"
            
            # Добавляем услуги
            for service in services_data:
                cursor.execute("""
                    INSERT INTO order_items (order_id, service_id, quantity, final_price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, service['service_id'], service['quantity'], service['price']))
            
            conn.commit()

            # Сбрасываем кэш клиентского сервиса
            from services.client_service import ClientService
            client_service = ClientService()
            client_service.invalidate_cache()
            
            # Восстанавливаем кнопку перед показом сообщения
            self.btn_save.setEnabled(True)
            self.btn_save.setText("💾 Сохранить")
            
            QMessageBox.information(self, "Успешно", message)
            self.accept()
            
        except Exception as e:
            conn.rollback()
            # Восстанавливаем кнопку при ошибке
            self.btn_save.setEnabled(True)
            self.btn_save.setText("💾 Сохранить")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заказ:\n{e}")
        
        finally:
            conn.close()
    
    def get_last_order_id(self):
        """Возвращает ID последнего созданного заказа"""
        return getattr(self, '_last_order_id', None)