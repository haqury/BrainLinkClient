"""System tray icon for BrainLink Client"""

import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class TrayIcon(QObject):
    """System tray icon for background operation"""
    
    # Signals
    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    quit_app = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize system tray icon
        
        Args:
            parent: Parent widget (MainWindow)
        """
        super().__init__(parent)
        
        self.tray_icon = QSystemTrayIcon(parent)
        self.parent_window = parent
        
        # Create icon (simple colored icon if no file available)
        self._create_icon()
        
        # Create menu
        self._create_menu()
        
        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Check system tray availability and show icon immediately
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available - tray icon may not be shown")
        else:
            self.tray_icon.show()
            # Принудительно показываем уведомление при старте, чтобы Windows зарегистрировал иконку
            # Это помогает в exe-версии, где иконка может не появиться без уведомления
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, lambda: self._force_show_with_notification())
            logger.info("System tray icon initialized and shown")
    
    def _create_icon(self):
        """Create tray icon"""
        import sys
        import os
        
        icon_path = None
        
        # В exe PyInstaller ресурсы находятся в sys._MEIPASS
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'resources', 'icon.png')
        else:
            # Обычный запуск из Python
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icon.png')
        
        try:
            if icon_path and os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self.tray_icon.setIcon(icon)
                    logger.info(f"Loaded custom tray icon from {icon_path}")
                    self.tray_icon.setToolTip("BrainLink Client - Double-click to show")
                    return
        except Exception as e:
            logger.warning(f"Failed to load icon from {icon_path}: {e}")
        
        # Fallback: используем стандартную иконку Qt
        try:
            from PyQt5.QtWidgets import QStyle, QApplication
            style = QApplication.style()
            # Используем более заметную иконку
            icon = style.standardIcon(QStyle.SP_ComputerIcon)
            self.tray_icon.setIcon(icon)
            logger.info("Using default Qt tray icon (SP_ComputerIcon)")
        except Exception as e:
            logger.error(f"Failed to set any tray icon: {e}")
        
        self.tray_icon.setToolTip("BrainLink Client - Double-click to show")
    
    def _create_menu(self):
        """Create tray icon context menu"""
        menu = QMenu()
        
        # Show/Hide action
        self.show_action = QAction("Show Window", self)
        self.show_action.triggered.connect(self.show_window.emit)
        menu.addAction(self.show_action)
        
        self.hide_action = QAction("Hide to Tray", self)
        self.hide_action.triggered.connect(self.hide_window.emit)
        menu.addAction(self.hide_action)
        
        menu.addSeparator()
        
        # Status action (disabled, just shows status)
        self.status_action = QAction("Status: Not Connected", self)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
    
    def _on_tray_activated(self, reason):
        """
        Handle tray icon activation
        
        Args:
            reason: Activation reason (click, double-click, etc.)
        """
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click to show window
            self.show_window.emit()
            logger.info("Tray icon double-clicked - showing window")
    
    def show(self):
        """Show tray icon"""
        # В exe под Windows QSystemTrayIcon иногда не появляется с первого раза.
        # Принудительно проверяем доступность и повторно вызываем show().
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available (show() called)")
            return
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
            logger.info("Tray icon shown")
    
    def hide(self):
        """Hide tray icon"""
        if self.tray_icon.isVisible():
            self.tray_icon.hide()
            logger.info("Tray icon hidden")
    
    def update_status(self, connected: bool):
        """
        Update connection status in tray menu
        
        Args:
            connected: True if connected to device
        """
        if connected:
            self.status_action.setText("Status: Connected ✓")
        else:
            self.status_action.setText("Status: Not Connected")
        
        logger.debug(f"Tray status updated: {'Connected' if connected else 'Not Connected'}")
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, duration: int = 3000):
        """
        Show tray notification
        
        Args:
            title: Notification title
            message: Notification message
            icon: Icon type (Information, Warning, Critical)
            duration: Duration in milliseconds
        """
        self.tray_icon.showMessage(title, message, icon, duration)
        logger.info(f"Tray notification: {title} - {message}")
    
    def _force_show_with_notification(self):
        """Force show tray icon with notification to ensure Windows registers it"""
        try:
            # Повторно показываем иконку
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
                logger.info("Tray icon force-shown")
            
            # Показываем краткое уведомление - это заставляет Windows зарегистрировать иконку
            # В Windows 11 иконки часто не появляются до первого уведомления
            self.tray_icon.showMessage(
                "BrainLink Client",
                "Application started",
                QSystemTrayIcon.Information,
                1000  # Очень короткое уведомление, чтобы не мешать
            )
            logger.debug("Startup notification shown to force tray icon registration")
        except Exception as e:
            logger.warning(f"Error forcing tray icon show: {e}")
    
    def cleanup(self):
        """Cleanup tray icon"""
        self.hide()
        logger.info("Tray icon cleanup completed")
