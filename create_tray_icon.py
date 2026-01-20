"""Create a simple tray icon image"""

from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt
import os

def create_tray_icon():
    """Create a simple colored icon with 'BL' text"""
    size = 64  # Larger size for better quality
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background circle (GreenYellow color)
    painter.setBrush(QColor("#ADFF2F"))  # GreenYellow
    painter.setPen(QPen(QColor("#000000"), 2))  # Black border
    painter.drawEllipse(2, 2, size-4, size-4)
    
    # Draw text "BL"
    painter.setPen(QColor("#000000"))  # Black text
    font = QFont("Arial", int(size * 0.4), QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "BL")
    
    painter.end()
    
    # Save icon
    os.makedirs("resources", exist_ok=True)
    icon_path = "resources/icon.png"
    pixmap.save(icon_path, "PNG")
    print(f"[OK] Icon created: {icon_path}")
    return icon_path

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    path = create_tray_icon()
    print(f"Icon saved to: {path}")
    
    # Test loading
    from PyQt5.QtGui import QIcon
    icon = QIcon(path)
    print(f"Icon loaded successfully: {not icon.isNull()}")
    
    app.quit()
