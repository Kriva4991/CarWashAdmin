# src/ui/shift_manager.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from database import get_connection

class ShiftManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 Управление сменами")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        self.current_shift_id = None
        self.setup_ui()
        self.load_shifts()
        self.check_active_shift()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        header = QLabel("📋 Журнал смен")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Инфо о текущей смене
        self.shift_info = QLabel("ℹ️ Нет активной смены")
        self.shift_info.setStyleSheet("font-size: 14px; padding: 10px; background-color: #FFF3E0; border-radius: 5px;")
        layout.addWidget(self.shift_info)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("🟢 Открыть смену")
        self.btn_open.clicked.connect(self.open_shift)
        self.btn_open.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #4CAF50; color: white;")
        
        self.btn_close = QPushButton("🔴 Закрыть смену")
        self.btn_close.clicked.connect(self.close_shift)
        self.btn_close.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #f44336; color: white;")
        self.btn_close.setEnabled(False)
        
        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Таблица смен
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(6)
        self.shifts_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Админ", "Открытие", "Закрытие", "Выручка"
        ])
        self.shifts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.shifts_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.shifts_table)
        
        # Кнопка обновления
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.load_shifts)
        layout.addWidget(btn_refresh)
    
    def check_active_shift(self):
        """Проверяет, есть ли открытая смена"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, opened_at, username 
            FROM shifts 
            WHERE closed_at IS NULL 
            ORDER BY opened_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.current_shift_id = row['id']
            self.shift_info.setText(
                f"✅ Активная смена #{row['id']} | "
                f"Админ: {row['username']} | "
                f"Открыта: {row['opened_at']}"
            )
            self.btn_open.setEnabled(False)
            self.btn_close.setEnabled(True)
        else:
            self.current_shift_id = None
            self.shift_info.setText("ℹ️ Нет активной смены")
            self.btn_open.setEnabled(True)
            self.btn_close.setEnabled(False)
    
    def open_shift(self):
        """Открывает новую смену"""
        username = "admin"  # Можно сохранить при логине
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO shifts (username, opened_at, revenue)
            VALUES (?, ?, 0)
        """, (username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "✅ Смена открыта", "Новая смена успешно открыта!")
        self.load_shifts()
        self.check_active_shift()
    
    def close_shift(self):
        """Закрывает текущую смену и подсчитывает выручку"""
        if not self.current_shift_id:
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем время открытия смены
        cursor.execute("SELECT opened_at FROM shifts WHERE id = ?", (self.current_shift_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        opened_at = row['opened_at']
        
        # 🔧 ИСПРАВЛЕНО: Считаем выручку из order_items
        cursor.execute("""
            SELECT COALESCE(SUM(oi.final_price * oi.quantity), 0) as total_revenue
            FROM order_items oi
            INNER JOIN orders o ON oi.order_id = o.id
            WHERE o.shift_id = ?
            AND o.status IN ('process', 'done')
        """, (self.current_shift_id,))
        revenue_row = cursor.fetchone()
        total_revenue = revenue_row['total_revenue'] if revenue_row else 0
        
        # Закрываем смену с выручкой
        cursor.execute("""
            UPDATE shifts 
            SET closed_at = ?, revenue = ?
            WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total_revenue, self.current_shift_id))
        conn.commit()
        conn.close()
        
        QMessageBox.information(
            self, "✅ Смена закрыта", 
            f"Смена успешно закрыта!\n\n💰 Выручка за смену: {total_revenue:.0f} ₽"
        )
        self.load_shifts()
        self.check_active_shift()
    
    def load_shifts(self):
        """Загружает историю смен"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, date(opened_at) as shift_date, username, 
                   opened_at, closed_at, revenue
            FROM shifts 
            ORDER BY opened_at DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.shifts_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.shifts_table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.shifts_table.setItem(row_idx, 1, QTableWidgetItem(row['shift_date'] or ''))
            self.shifts_table.setItem(row_idx, 2, QTableWidgetItem(row['username'] or ''))
            self.shifts_table.setItem(row_idx, 3, QTableWidgetItem(row['opened_at'] or ''))
            self.shifts_table.setItem(row_idx, 4, QTableWidgetItem(row['closed_at'] or '🟡 Открыта'))
            revenue = row['revenue'] if row['revenue'] else 0
            self.shifts_table.setItem(row_idx, 5, QTableWidgetItem(f"{revenue:.0f} ₽"))