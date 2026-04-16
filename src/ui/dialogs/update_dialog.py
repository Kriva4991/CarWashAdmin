# src/ui/dialogs/update_dialog.py
"""
Диалог информации об обновлении
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from utils.update_checker import UpdateChecker, UpdateInfo


class DownloadThread(QThread):
    """Поток для скачивания обновления"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, update_info: UpdateInfo):
        super().__init__()
        self.update_info = update_info
        self.checker = UpdateChecker()
    
    def run(self):
        success, result = self.checker.download_update(
            self.update_info,
            progress_callback=self.progress.emit
        )
        self.finished.emit(success, result)


class UpdateDialog(QDialog):
    """Диалог с информацией об обновлении"""
    
    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.checker = UpdateChecker()
        self.download_thread = None
        self.downloaded_file = None
        
        self.setWindowTitle("🚀 Доступно обновление")
        self.setFixedSize(500, 450)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Заголовок
        title = QLabel(f"🚀 Доступна новая версия!")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
        """)
        layout.addWidget(title)
        
        # Информация о версии
        version_info = QLabel(
            f"Текущая версия: {self.checker.current_version}\n"
            f"Новая версия: {self.update_info.version}\n"
            f"Дата выпуска: {self.update_info.release_date}\n"
            f"Размер: {self.update_info.formatted_size}"
        )
        version_info.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        """)
        layout.addWidget(version_info)
        
        # Список изменений
        changelog_label = QLabel("📝 Что нового:")
        changelog_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(changelog_label)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setPlainText(self.update_info.changelog_text)
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(150)
        self.changelog_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                background-color: white;
            }
        """)
        layout.addWidget(self.changelog_text)
        
        # Прогресс-бар (скрыт по умолчанию)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_download = QPushButton("📥 Скачать обновление")
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.btn_download.clicked.connect(self.start_download)
        btn_layout.addWidget(self.btn_download)
        
        self.btn_later = QPushButton("⏰ Позже")
        self.btn_later.setStyleSheet("""
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
        self.btn_later.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_later)
        
        layout.addLayout(btn_layout)
    
    def start_download(self):
        """Начинает скачивание обновления"""
        self.btn_download.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Подготовка к скачиванию...")
        
        self.download_thread = DownloadThread(self.update_info)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
    
    def update_progress(self, percent: int):
        """Обновляет прогресс скачивания"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Скачивание: {percent}%")
    
    def download_finished(self, success: bool, result: str):
        """Обрабатывает завершение скачивания"""
        if success:
            self.downloaded_file = result
            self.status_label.setText("✅ Скачивание завершено!")
            self.progress_bar.setValue(100)
            
            reply = QMessageBox.question(
                self,
                "✅ Готово к установке",
                "Обновление успешно скачано!\n\n"
                "Для установки обновления программа будет закрыта.\n"
                "Установить сейчас?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.install_update()
            else:
                self.status_label.setText("Установка отложена. Файл сохранён.")
                self.btn_later.setText("❌ Закрыть")
                self.btn_later.setEnabled(True)
        else:
            self.status_label.setText(f"❌ Ошибка: {result}")
            self.btn_later.setEnabled(True)
            self.btn_later.setText("❌ Закрыть")
    
    def install_update(self):
        """Устанавливает обновление"""
        if self.downloaded_file and self.checker.install_update(self.downloaded_file):
            # Закрываем приложение
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
        else:
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                "Не удалось запустить установщик обновления.\n"
                "Пожалуйста, запустите его вручную."
            )