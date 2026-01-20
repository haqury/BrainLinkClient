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
        app.setApplicationName("BrainLink Client")
        app.setOrganizationName("BrainLink")
        
        logger.info("Qt application initialized")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Main window created and shown")
        
        # Run application event loop
        exit_code = app.exec_()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
