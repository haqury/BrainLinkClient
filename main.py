"""
BrainLink Client - Python Edition
Main application entry point

A Python port of the C# BrainLinkConnect application for controlling
computer input using EEG (electroencephalography) and gyroscope data
from BrainLink devices.
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("BrainLink Client")
    app.setOrganizationName("BrainLink")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
