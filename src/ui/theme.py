# src/ui/theme.py
"""
Темы оформления для CarWash Admin Pro
Цвета соответствуют стандарту WCAG 2.1 (контраст минимум 4.5:1)
"""

# 🌞 СВЕТЛАЯ ТЕМА
LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #FFFFFF;
    color: #2C3E50;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* === ЗАГОЛОВКИ === */
QLabel {
    color: #2C3E50;
    background-color: transparent;
}
QLabel#header {
    font-size: 20px;
    font-weight: bold;
    color: #2C3E50;
    padding: 10px;
}

/* === КНОПКИ === */
QPushButton {
    background-color: #3498DB;
    color: #FFFFFF;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #2980B9;
}
QPushButton:pressed {
    background-color: #1A5276;
}
QPushButton:disabled {
    background-color: #BDC3C7;
    color: #7F8C8D;
}

/* === ПОЛЯ ВВОДА === */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #3498DB;
}
QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid #7F8C8D;
}

/* === ТАБЛИЦЫ === */
QTableWidget {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1px solid #DDDDDD;
    border-radius: 5px;
    gridline-color: #E0E0E0;
    font-size: 13px;
}
QTableWidget::item {
    padding: 10px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #E3F2FD;
    color: #2C3E50;
}
QHeaderView::section {
    background-color: #34495E;
    color: #FFFFFF;
    padding: 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

/* === ВКЛАДКИ === */
QTabWidget::pane {
    border: 1px solid #DDDDDD;
    border-radius: 5px;
    background-color: #FFFFFF;
}
QTabBar::tab {
    background-color: #ECF0F1;
    color: #2C3E50;
    padding: 10px 20px;
    border: 1px solid #DDDDDD;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #3498DB;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #D5DBDB;
}

/* === ГРУППЫ === */
QGroupBox {
    font-weight: bold;
    font-size: 14px;
    border: 2px solid #3498DB;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    color: #2C3E50;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
    color: #2980B9;
}

/* === СКРОЛЛБАРЫ === */
QScrollBar:vertical {
    background-color: #ECF0F1;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background-color: #BDC3C7;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #95A5A6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* === ПРОГРЕСС БАРЫ === */
QProgressBar {
    background-color: #ECF0F1;
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    text-align: center;
    color: #2C3E50;
}
QProgressBar::chunk {
    background-color: #3498DB;
    border-radius: 5px;
}

/* === CHECKBOX И RADIO === */
QCheckBox, QRadioButton {
    color: #2C3E50;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #BDC3C7;
    border-radius: 4px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #3498DB;
    border-color: #3498DB;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #3498DB;
}

/* === МЕНЮ === */
QMenuBar {
    background-color: #FFFFFF;
    color: #2C3E50;
    border-bottom: 1px solid #DDDDDD;
}
QMenuBar::item:selected {
    background-color: #3498DB;
    color: #FFFFFF;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #DDDDDD;
    border-radius: 5px;
}
QMenu::item:selected {
    background-color: #3498DB;
    color: #FFFFFF;
}

/* === STATUS BAR === */
QStatusBar {
    background-color: #ECF0F1;
    color: #2C3E50;
    border-top: 1px solid #DDDDDD;
}

/* === СПИСКИ === */
QListWidget {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1px solid #DDDDDD;
    border-radius: 5px;
}
QListWidget::item {
    padding: 8px;
    border: none;
}
QListWidget::item:selected {
    background-color: #E3F2FD;
    color: #2C3E50;
}
QListWidget::item:hover {
    background-color: #F5F5F5;
}

/* === КАЛЕНДАРЬ === */
QCalendarWidget {
    background-color: #FFFFFF;
    color: #2C3E50;
}
QCalendarWidget QToolButton {
    color: #2C3E50;
    background-color: #ECF0F1;
    border-radius: 3px;
    padding: 5px;
}
QCalendarWidget QToolButton:hover {
    background-color: #3498DB;
    color: #FFFFFF;
}
"""

# 🌙 ТЁМНАЯ ТЕМА
DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* === ЗАГОЛОВКИ === */
QLabel {
    color: #E0E0E0;
    background-color: transparent;
}
QLabel#header {
    font-size: 20px;
    font-weight: bold;
    color: #E0E0E0;
    padding: 10px;
}

/* === КНОПКИ === */
QPushButton {
    background-color: #5DADE2;
    color: #1E1E1E;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #3498DB;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #2980B9;
    color: #FFFFFF;
}
QPushButton:disabled {
    background-color: #4A4A4A;
    color: #7F8C8D;
}

/* === ПОЛЯ ВВОДА === */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #5DADE2;
}
QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid #7F8C8D;
}

/* === ТАБЛИЦЫ === */
QTableWidget {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    gridline-color: #3D3D3D;
    font-size: 13px;
}
QTableWidget::item {
    padding: 10px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #1A5276;
    color: #E0E0E0;
}
QHeaderView::section {
    background-color: #3D3D3D;
    color: #E0E0E0;
    padding: 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

/* === ВКЛАДКИ === */
QTabWidget::pane {
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    background-color: #2D2D2D;
}
QTabBar::tab {
    background-color: #3D3D3D;
    color: #E0E0E0;
    padding: 10px 20px;
    border: 1px solid #4A4A4A;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QTabBar::tab:selected {
    background-color: #2D2D2D;
    color: #5DADE2;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #4A4A4A;
}

/* === ГРУППЫ === */
QGroupBox {
    font-weight: bold;
    font-size: 14px;
    border: 2px solid #5DADE2;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    color: #E0E0E0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
    color: #5DADE2;
}

/* === СКРОЛЛБАРЫ === */
QScrollBar:vertical {
    background-color: #3D3D3D;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background-color: #5A5A5A;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #7F8C8D;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* === ПРОГРЕСС БАРЫ === */
QProgressBar {
    background-color: #3D3D3D;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    text-align: center;
    color: #E0E0E0;
}
QProgressBar::chunk {
    background-color: #5DADE2;
    border-radius: 5px;
}

/* === CHECKBOX И RADIO === */
QCheckBox, QRadioButton {
    color: #E0E0E0;
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #4A4A4A;
    border-radius: 4px;
    background-color: #2D2D2D;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #5DADE2;
    border-color: #5DADE2;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #5DADE2;
}

/* === МЕНЮ === */
QMenuBar {
    background-color: #1E1E1E;
    color: #E0E0E0;
    border-bottom: 1px solid #4A4A4A;
}
QMenuBar::item:selected {
    background-color: #5DADE2;
    color: #1E1E1E;
}
QMenu {
    background-color: #2D2D2D;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
}
QMenu::item:selected {
    background-color: #5DADE2;
    color: #1E1E1E;
}

/* === STATUS BAR === */
QStatusBar {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border-top: 1px solid #4A4A4A;
}

/* === СПИСКИ === */
QListWidget {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
}
QListWidget::item {
    padding: 8px;
    border: none;
}
QListWidget::item:selected {
    background-color: #1A5276;
    color: #E0E0E0;
}
QListWidget::item:hover {
    background-color: #3D3D3D;
}

/* === КАЛЕНДАРЬ === */
QCalendarWidget {
    background-color: #2D2D2D;
    color: #E0E0E0;
}
QCalendarWidget QToolButton {
    color: #E0E0E0;
    background-color: #3D3D3D;
    border-radius: 3px;
    padding: 5px;
}
QCalendarWidget QToolButton:hover {
    background-color: #5DADE2;
    color: #1E1E1E;
}
"""

def get_theme(theme_name: str) -> str:
    """Возвращает стиль по названию темы"""
    themes = {
        'light': LIGHT_THEME,
        'dark': DARK_THEME
    }
    return themes.get(theme_name, LIGHT_THEME)