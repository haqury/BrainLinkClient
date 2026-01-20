"""Test tray icon visibility"""

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[ERROR] System tray not available on this system!")
        return
    
    print("[OK] System tray is available")
    
    # Create main window
    window = MainWindow()
    window.show()
    
    print(f"[OK] Application started")
    print(f"[OK] Tray icon visible: {window.tray_icon.tray_icon.isVisible()}")
    print(f"[OK] Tray tooltip: {window.tray_icon.tray_icon.toolTip()}")
    print()
    print("=" * 60)
    print("INSTRUKCIYA:")
    print("1. Posmotrite v praviy nizhniy ugol ekrana (okolo chasov)")
    print("2. Esli ne vidite - nazhmite strelku ^ dlya skrytih ikonok")
    print("3. Dolzhna byt zelenaya ikonka s 'BL' ili sinyaya (i)")
    print("4. Navedite myshu - poyavitsya podskazka")
    print()
    print("Nazhmite Ctrl+C v etom okne chtoby zakryt")
    print("=" * 60)
    
    # Run app
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
