"""
BrainLink Client - Python Edition
Main application entry point

A Python port of the C# BrainLinkConnect application for controlling
computer input using EEG (electroencephalography) and gyroscope data
from BrainLink devices.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from logger_config import setup_logging
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Initialize logging system
    setup_logging(log_level=logging.INFO)
    
    logger.info("Starting BrainLink Client application")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        # Allow app to stay живым, даже когда главное окно закрыто,
        # чтобы треевый значок продолжал работать.
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName("BrainLink Client")
        app.setOrganizationName("BrainLink")
        
        logger.info("Qt application initialized")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Main window created and shown")
        
        # Обрабатываем события, чтобы убедиться что иконка в трее создана
        app.processEvents()
        
        # Даём Windows время зарегистрировать иконку в трее
        # Это особенно важно для exe-версии
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: window.tray_icon._force_show_with_notification())
        
        # Run application event loop
        exit_code = app.exec_()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    # On Windows + PyInstaller + multiprocessing we must call freeze_support()
    # so that child processes (used for ML training) terminate correctly and
    # не размножаются лишними экземплярами exe.
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except Exception:
        # Safe fallback: if anything goes wrong, just continue.
        pass
    
    # Prevent running main() in worker processes (multiprocessing spawn)
    import os
    if os.environ.get('BRAINLINK_WORKER_PROCESS') == '1':
        # This is a worker process for ML training, don't start Qt app
        logger.info("Worker process detected, skipping Qt application initialization")
        sys.exit(0)
    
    main()
