# main.py
import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QSystemTrayIcon, 
                             QMenu, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QColor

from bot_handlers import run_bot


class BotSignals(QObject):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(bool)


class OutputRedirector:
    def __init__(self, signal, original):
        self.signal = signal
        self.original = original
    
    def write(self, text):
        if text and text.strip():
            self.signal.emit(text.strip())
        if self.original:
            try:
                self.original.write(text)
            except:
                pass
    
    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except:
                pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.bot_thread = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.signals = BotSignals()
        
        self.init_ui()
        self.setup_tray()
        self.start_bot()
        
    def init_ui(self):
        self.setWindowTitle("سیستم مدیریت حسابداری")
        self.setFixedSize(600, 500)
        self.setAttribute(Qt.WA_RightToLeft)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QLabel#title { color: #00ff88; font-size: 20px; font-weight: bold; padding: 15px; }
            QLabel#status { font-size: 16px; font-weight: bold; padding: 10px; background-color: #16213e; border-radius: 10px; color: #ffffff; }
            QTextEdit { background-color: #0f0f1a; color: #00ff88; font-size: 12px; font-family: 'Consolas', monospace; border: 1px solid #0f3460; border-radius: 8px; }
            QPushButton { background-color: #0f3460; color: white; font-size: 13px; border: none; border-radius: 8px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #1a4a7a; }
            QPushButton#hide { background-color: #e94560; }
            QPushButton#hide:hover { background-color: #ff5c77; }
            QPushButton#exit { background-color: #533483; }
            QPushButton#exit:hover { background-color: #6c44a3; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("ربات مدیریت حسابداری")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.status_label = QLabel("در حال راه‌اندازی...")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        btn_layout = QHBoxLayout()
        hide_btn = QPushButton("مخفی کردن (Tray)")
        hide_btn.setObjectName("hide")
        exit_btn = QPushButton("خروج کامل")
        exit_btn.setObjectName("exit")
        
        hide_btn.clicked.connect(self.hide_to_tray)
        exit_btn.clicked.connect(self.close_application)
        
        btn_layout.addWidget(hide_btn)
        btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)
        
        self.signals.log_signal.connect(self.append_log)
        self.signals.status_signal.connect(self.update_status_style)
        
        sys.stdout = OutputRedirector(self.signals.log_signal, self.original_stdout)
        sys.stderr = OutputRedirector(self.signals.log_signal, self.original_stderr)
    
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        if os.path.exists("icon.png"):
            self.tray_icon.setIcon(QIcon("icon.png"))
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#00ff88"))
            self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("نمایش پنجره")
        exit_action = tray_menu.addAction("خروج")
        
        show_action.triggered.connect(self.show_normal)
        exit_action.triggered.connect(self.close_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def start_bot(self):
        self.bot_thread = threading.Thread(target=run_bot, args=(self.signals,), daemon=True)
        self.bot_thread.start()
    
    def append_log(self, text):
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def update_status_style(self, connected):
        if connected:
            self.status_label.setText("ربات فعال و متصل به سرور است")
            self.status_label.setStyleSheet("color: #00ff88; background-color: #16213e;")
        else:
            self.status_label.setText("خطا در اتصال یا عدم دسترسی به سرور")
            self.status_label.setStyleSheet("color: #e94560; background-color: #16213e;")
    
    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "ربات حسابداری",
            "برنامه مخفی شد و در پس‌زمینه در حال اجراست.",
            QSystemTrayIcon.Information,
            2000
        )
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()
    
    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide_to_tray()
            event.ignore()
        else:
            event.accept()
    
    def close_application(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
