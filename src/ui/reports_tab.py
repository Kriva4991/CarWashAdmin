# src/ui/reports_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database import get_connection
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime, timedelta
import csv
import os

class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_reports()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок
        header = QLabel("📊 Аналитика и отчёты")
        header.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; color: #2c3e50;")
        layout.addWidget(header)
        
        # === ФИЛЬТРЫ ===
        filter_layout = QHBoxLayout()
        
        # Период
        filter_layout.addWidget(QLabel("📅 Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Сегодня", "Неделя", "Месяц", "Произвольно"])
        self.period_combo.currentIndexChanged.connect(self.load_reports)
        self.period_combo.setStyleSheet(self.get_input_style())
        filter_layout.addWidget(self.period_combo)
        
        # Даты для произвольного периода
        self.date_from = QDateEdit()
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_reports)
        self.date_from.setStyleSheet(self.get_input_style())
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("—"))
        
        self.date_to = QDateEdit()
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_reports)
        self.date_to.setStyleSheet(self.get_input_style())
        filter_layout.addWidget(self.date_to)
        
        filter_layout.addStretch()
        
        btn_export_excel = QPushButton("📊 Excel")
        btn_export_excel.clicked.connect(self.export_excel)
        btn_export_excel.setStyleSheet(self.get_btn_style("#95a5a6"))
        filter_layout.addWidget(btn_export_excel)
        
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.load_reports)
        btn_refresh.setStyleSheet(self.get_btn_style("#3498db"))
        filter_layout.addWidget(btn_refresh)
        
        layout.addLayout(filter_layout)
        
        # === КАРТОЧКИ МЕТРИК ===
        metrics_layout = QHBoxLayout()
        
        self.metric_revenue = self.create_metric_card("💰 Выручка", "0 ₽", "#27ae60")
        metrics_layout.addWidget(self.metric_revenue)
        
        self.metric_orders = self.create_metric_card("📋 Заказы", "0", "#3498db")
        metrics_layout.addWidget(self.metric_orders)
        
        self.metric_avg = self.create_metric_card("🧮 Средний чек", "0 ₽", "#9b59b6")
        metrics_layout.addWidget(self.metric_avg)
        
        self.metric_services = self.create_metric_card("🔧 Услуг", "0", "#f39c12")
        metrics_layout.addWidget(self.metric_services)
        
        layout.addLayout(metrics_layout)
        
        # === ГРАФИКИ ===
        charts_layout = QHBoxLayout()
        
        # График выручки
        self.revenue_chart = self.create_chart_placeholder("Выручка по дням")
        charts_layout.addWidget(self.revenue_chart, 2)
        
        # Топ услуг
        self.services_chart = self.create_chart_placeholder("Топ услуг")
        charts_layout.addWidget(self.services_chart, 1)
        
        layout.addLayout(charts_layout)
        
        # === ТАБЛИЦА ДЕТАЛИЗАЦИИ ===
        detail_label = QLabel("📋 Детализация заказов")
        detail_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
        layout.addWidget(detail_label)
        
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels([
            "Дата", "Гос. номер", "Услуги", "Сумма", "Статус", "Оплата"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
                font-size: 12px;
                background-color: white;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.detail_table)
    
    def get_input_style(self):
        return """
            QComboBox, QDateEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox:focus, QDateEdit:focus {
                border: 2px solid #3498db;
            }
        """
    
    def get_btn_style(self, color):
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
    
    def darken_color(self, color):
        color_map = {
            '#27ae60': '#229954', '#3498db': '#2980b9',
            '#9b59b6': '#8e44ad', '#f39c12': '#d68910',
            '#e74c3c': '#c0392b', '#95a5a6': '#7f8c8d'
        }
        return color_map.get(color, color)
    
    def create_metric_card(self, title, value, color):
        """Создает карточку метрики"""
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
                min-width: 180px;
                text-align: center;
            }}
        """)
        card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.setText(f"{title}\n{value}")
        return card
    
    def create_chart_placeholder(self, title):
        """Создает placeholder для графика"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                min-height: 250px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        label = QLabel(f"📊 {title}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #7f8c8d; padding: 20px;")
        layout.addWidget(label)
        
        frame.label = label  # Сохраняем ссылку для обновления
        return frame
    
    def get_date_range(self):
        """Возвращает диапазон дат для фильтра"""
        period = self.period_combo.currentText()
        today = datetime.now().date()
        
        if period == "Сегодня":
            return today, today
        elif period == "Неделя":
            return today - timedelta(days=6), today
        elif period == "Месяц":
            return today.replace(day=1), today
        else:  # Произвольно
            from_date = self.date_from.date().toPyDate()
            to_date = self.date_to.date().toPyDate()
            return from_date, to_date
    
    def load_reports(self):
        """Загружает данные для отчётов"""
        from_date, to_date = self.get_date_range()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # === МЕТРИКИ ===
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT o.id) as orders,
                COALESCE(SUM(oi.final_price * oi.quantity), 0) as revenue,
                COUNT(DISTINCT oi.service_id) as services
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (from_date.isoformat(), to_date.isoformat()))
        metrics = cursor.fetchone()
        
        orders = metrics['orders'] or 0
        revenue = metrics['revenue'] or 0
        avg_check = revenue / orders if orders > 0 else 0
        services = metrics['services'] or 0
        
        # Обновляем карточки
        self.metric_revenue.setText(f"💰 Выручка\n{revenue:.0f} ₽")
        self.metric_orders.setText(f"📋 Заказы\n{orders}")
        self.metric_avg.setText(f"🧮 Средний чек\n{avg_check:.0f} ₽")
        self.metric_services.setText(f"🔧 Услуг\n{services}")
        
        # === ГРАФИК: ВЫРУЧКА ПО ДНЯМ ===
        cursor.execute("""
            SELECT DATE(created_at) as date, 
                   COALESCE(SUM(oi.final_price * oi.quantity), 0) as daily_revenue
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (from_date.isoformat(), to_date.isoformat()))
        revenue_data = cursor.fetchall()
        
        dates = [row['date'] for row in revenue_data]
        values = [row['daily_revenue'] for row in revenue_data]
        
        self.draw_bar_chart(self.revenue_chart, dates, values, "Выручка, ₽", "#3498db")
        
        # === ГРАФИК: ТОП УСЛУГ ===
        cursor.execute("""
            SELECT s.name, COUNT(oi.id) as count
            FROM order_items oi
            JOIN services s ON oi.service_id = s.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY s.name
            ORDER BY count DESC
            LIMIT 5
        """, (from_date.isoformat(), to_date.isoformat()))
        services_data = cursor.fetchall()
        
        service_names = [row['name'] for row in services_data]
        service_counts = [row['count'] for row in services_data]
        
        self.draw_pie_chart(self.services_chart, service_names, service_counts)
        
        # === ТАБЛИЦА ДЕТАЛИЗАЦИИ ===
        cursor.execute("""
            SELECT o.created_at, o.car_number, 
                   GROUP_CONCAT(s.name, ', ') as services,
                   o.total_price, o.status, o.payment_method
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 100
        """, (from_date.isoformat(), to_date.isoformat()))
        orders_data = cursor.fetchall()
        conn.close()
        
        self.detail_table.setRowCount(len(orders_data))
        for row_idx, row in enumerate(orders_data):
            self.detail_table.setItem(row_idx, 0, QTableWidgetItem(str(row['created_at'])[:16] if row['created_at'] else ''))
            self.detail_table.setItem(row_idx, 1, QTableWidgetItem(row['car_number'] or '—'))
            self.detail_table.setItem(row_idx, 2, QTableWidgetItem(row['services'] or '—'))
            self.detail_table.setItem(row_idx, 3, QTableWidgetItem(f"{row['total_price']:.0f} ₽"))
            self.detail_table.setItem(row_idx, 4, QTableWidgetItem(self.translate_status(row['status'])))
            self.detail_table.setItem(row_idx, 5, QTableWidgetItem(row['payment_method'] or '—'))
    
    def draw_bar_chart(self, chart_frame, labels, values, ylabel, color):
        """Рисует столбчатый график"""
        # Удаляем старый график
        for i in range(chart_frame.layout().count() - 1, 0, -1):
            item = chart_frame.layout().itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not labels:
            chart_frame.label.setText("📊 Нет данных за выбранный период")
            return
        
        chart_frame.label.setText("")  # Скрываем placeholder
        
        # 🔧 Улучшенные параметры для избежания предупреждений
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)
        bars = ax.bar(range(len(labels)), values, color=color, alpha=0.8)
        
        ax.set_xlabel('Дата', fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(axis='y', alpha=0.3)
        
        # 🔧 Добавляем значения на столбцы
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                   f'{value:.0f}', ha='center', va='bottom', fontsize=8)
        
        # 🔧 Исправленное tight_layout
        plt.tight_layout(pad=2.0, h_pad=1.0, w_pad=1.0)
        
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: white;")
        canvas.setMinimumHeight(200)
        chart_frame.layout().addWidget(canvas)
        plt.close(fig)
    
    def draw_pie_chart(self, chart_frame, labels, values):
        """Рисует круговую диаграмму"""
        # Удаляем старый график
        for i in range(chart_frame.layout().count() - 1, 0, -1):
            item = chart_frame.layout().itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not labels:
            chart_frame.label.setText("📊 Нет данных")
            return
        
        chart_frame.label.setText("")
        
        colors = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c']
        
        # 🔧 Улучшенная круговая диаграмма
        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        
        # 🔧 Автоматическое позиционирование легенды
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=None,  # Убираем labels из pie
            autopct='%1.0f%%', 
            colors=colors[:len(values)], 
            startangle=90,
            pctdistance=0.85
        )
        
        # 🔧 Добавляем легенду отдельно
        ax.legend(
            wedges, 
            labels,
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            fontsize=8
        )
        
        # 🔧 Делаем текст процентов читаемым
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)
            autotext.set_weight('bold')
        
        ax.axis('equal')
        plt.tight_layout(pad=2.0)
        
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: white;")
        canvas.setMinimumHeight(200)
        chart_frame.layout().addWidget(canvas)
        plt.close(fig)
    
    def translate_status(self, status):
        """Переводит статусы"""
        statuses = {
            'queue': '🟡 В очереди',
            'process': '🔵 В работе',
            'done': '🟢 Готово',
            'cancelled': '🔴 Отменено'
        }
        return statuses.get(status, status)
    
    def export_excel(self):
        """Экспорт детализации в Excel"""
        from PyQt6.QtWidgets import QFileDialog
        from utils.excel_exporter import ExcelExporter
        
        from_date, to_date = self.get_date_range()
        
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
                o.total_price,
                o.status,
                o.payment_method
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN services s ON oi.service_id = s.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """, (from_date.isoformat(), to_date.isoformat()))
        orders = cursor.fetchall()
        conn.close()
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "📊 Сохранить отчёт Excel",
            f"report_{from_date}_to_{to_date}.xlsx",
            "Excel файлы (*.xlsx)"
        )
        
        if not filepath:
            return
        
        try:
            exporter = ExcelExporter()
            saved_path = exporter.export_orders(
                orders=[dict(row) for row in orders],
                date_from=from_date,
                date_to=to_date,
                filepath=filepath
            )
            
            QMessageBox.information(self, "✅ Экспорт завершён", f"Файл сохранён:\n{saved_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось создать Excel:\n{str(e)}")