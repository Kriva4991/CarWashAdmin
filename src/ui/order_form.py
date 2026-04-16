# src/ui/order_form.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QLabel, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from database import get_connection

class OrderFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Новая заявка")
        self.setMinimumSize(400, 500)
        self.setModal(True)  # Блокирует основное окно
        
        self.setup_ui()
        self.load_services()
    
    def setup_ui(self):
        """Создаёт элементы формы"""
        layout = QVBoxLayout(self)
        
        # --- Заголовок ---
        header = QLabel("📝 Данные автомобиля и клиента")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # --- Форма ввода ---
        form_layout = QFormLayout()
        
        # Гос. номер
        self.car_number_edit = QLineEdit()
        self.car_number_edit.setPlaceholderText("А 123 АА 77")
        self.car_number_edit.setStyleSheet("padding: 5px;")
        form_layout.addRow("Гос. номер *", self.car_number_edit)
        
        # Марка авто
        self.car_model_edit = QLineEdit()
        self.car_model_edit.setPlaceholderText("Toyota Camry")
        self.car_model_edit.setStyleSheet("padding: 5px;")
        form_layout.addRow("Марка/Модель", self.car_model_edit)
        
        # Телефон
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (999) 000-00-00")
        self.phone_edit.setStyleSheet("padding: 5px;")
        form_layout.addRow("Телефон", self.phone_edit)
        
        # Услуга (выпадающий список)
        self.service_combo = QComboBox()
        self.service_combo.setStyleSheet("padding: 5px;")
        form_layout.addRow("Услуга *", self.service_combo)

        # Класс авто (добавить после service_combo)
        self.car_class_combo = QComboBox()
        self.car_class_combo.setStyleSheet("padding: 5px;")
        form_layout.insertRow(4, "Класс авто", self.car_class_combo)
        
        # Цена (автоматически из услуги, но можно изменить)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 100000)
        self.price_spin.setSuffix(" ₽")
        self.price_spin.setStyleSheet("padding: 5px;")
        form_layout.addRow("Стоимость", self.price_spin)
        
        # Способ оплаты
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "СБП"])
        self.payment_combo.setStyleSheet("padding: 5px;")
        form_layout.addRow("Оплата", self.payment_combo)
        
        # Комментарий
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Особые отметки...")
        form_layout.addRow("Комментарий", self.comment_edit)
        
        layout.addLayout(form_layout)
        
        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.setStyleSheet("padding: 8px 20px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_save.clicked.connect(self.save_order)
        
        self.btn_cancel = QPushButton("❌ Отмена")
        self.btn_cancel.setStyleSheet("padding: 8px 20px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        # Привязка изменения услуги к изменению цены
        self.service_combo.currentIndexChanged.connect(self.on_service_changed)
        self.load_car_classes()
    
    def load_services(self):
        """Загружает услуги из БД в выпадающий список"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM services ORDER BY name")
        self.services = cursor.fetchall()
        conn.close()
        
        self.service_combo.clear()
        for service in self.services:
            self.service_combo.addItem(service['name'], service['id'])
        
        # Обновить цену для первой услуги
        if self.services:
            self.on_service_changed(0)
    
    def on_service_changed(self, index):
        """При выборе услуги обновляет цену"""
        if index >= 0 and index < len(self.services):
            price = self.services[index]['price']
            self.price_spin.setValue(price)
    
    def validate(self):
        """Проверяет заполненность обязательных полей"""
        if not self.car_number_edit.text().strip():
            QMessageBox.warning(self, "⚠️ Ошибка", "Введите гос. номер автомобиля!")
            return False
        if self.service_combo.currentIndex() < 0:
            QMessageBox.warning(self, "⚠️ Ошибка", "Выберите услугу!")
            return False
        return True
    
    def save_order(self):
        """Сохраняет заказ в БД"""
        if not self.validate():
            return
        
        # Собираем данные
        car_number = self.car_number_edit.text().strip().upper()
        car_model = self.car_model_edit.text().strip()
        phone = self.phone_edit.text().strip()
        service_id = self.service_combo.currentData()
        car_class_id = self.car_class_combo.currentData()
        final_price = self.price_spin.value()
        payment_method = self.payment_combo.currentText().lower()
        comment = self.comment_edit.toPlainText().strip()
        
        # Получаем ID активной смены
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM shifts 
            WHERE closed_at IS NULL 
            ORDER BY opened_at DESC 
            LIMIT 1
        """)
        shift_row = cursor.fetchone()
        shift_id = shift_row['id'] if shift_row else None
        
        print(f"🔍 Active shift_id: {shift_id}")
        
        conn.close()
        
        # Сохраняем в БД
        conn = get_connection()
        cursor = conn.cursor()
        
        if shift_id:
            # 10 столбцов = 10 значений
            cursor.execute("""
                INSERT INTO orders 
                (car_number, car_model, client_phone, service_id, car_class_id, 
                 shift_id, status, final_price, payment_method, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                car_number,        # 1
                car_model,         # 2
                phone,             # 3
                service_id,        # 4
                car_class_id,      # 5
                shift_id,          # 6
                'queue',           # 7 ← status (хардкод)
                final_price,       # 8
                payment_method,    # 9
                comment            # 10
            ))
            print(f"✅ Заказ привязан к смене #{shift_id}")
        else:
            # 9 столбцов = 9 значений (без shift_id)
            cursor.execute("""
                INSERT INTO orders 
                (car_number, car_model, client_phone, service_id, car_class_id, 
                 status, final_price, payment_method, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                car_number,        # 1
                car_model,         # 2
                phone,             # 3
                service_id,        # 4
                car_class_id,      # 5
                'queue',           # 6 ← status
                final_price,       # 7
                payment_method,    # 8
                comment            # 9
            ))
            print("⚠️ Нет активной смены, заказ сохранён без привязки")
        
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "✅ Успешно", 
            f"Заявка создана!\nГос. номер: {car_number}\nСумма: {final_price:.0f} ₽")
        
        self.accept()

    def load_car_classes(self):
        """Загружает классы авто из БД"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, coefficient FROM car_classes ORDER BY coefficient")
        self.car_classes = cursor.fetchall()
        conn.close()
        
        self.car_class_combo.clear()
        for car_class in self.car_classes:
            self.car_class_combo.addItem(car_class['name'], car_class['id'])