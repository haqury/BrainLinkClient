"""Common styles for BrainLink Client application"""

# Dark theme with YellowGreen accents (darker shade, like original BrainLinkConnect)
BRAINLINK_DARK_STYLE = """
QMainWindow, QDialog {
    background-color: #000000;
    color: #9ACD32;
}

QWidget {
    background-color: #000000;
    color: #9ACD32;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QLabel {
    color: #9ACD32;
    background-color: transparent;
    font-size: 10pt;
}

QPushButton {
    background-color: #000000;
    color: #9ACD32;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 5px 15px;
    font-weight: bold;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #1a1a1a;
    border: 1px solid #9ACD32;
}

QPushButton:pressed {
    background-color: #0a0a0a;
}

QPushButton:disabled {
    background-color: #0a0a0a;
    color: #555555;
}

QLineEdit, QTextEdit {
    background-color: #0a0a0a;
    color: #9ACD32;
    border: 1px solid #333333;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 10pt;
    selection-background-color: #2d5016;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #9ACD32;
}

QLineEdit:disabled, QTextEdit:disabled {
    color: #555555;
    background-color: #050505;
}

QCheckBox {
    color: #9ACD32;
    spacing: 8px;
    font-size: 10pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #333333;
    border-radius: 3px;
    background-color: #0a0a0a;
}

QCheckBox::indicator:hover {
    border: 1px solid #9ACD32;
}

QCheckBox::indicator:checked {
    background-color: #9ACD32;
    border: 1px solid #9ACD32;
}

QGroupBox {
    color: #9ACD32;
    font-weight: bold;
    border: 1px solid #333333;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 15px;
    font-size: 11pt;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
}

QListWidget {
    background-color: #0a0a0a;
    color: #9ACD32;
    border: 1px solid #333333;
    border-radius: 4px;
    font-size: 10pt;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #2d5016;
}

QListWidget::item:hover {
    background-color: #1a1a1a;
}

QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 12px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9ACD32;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QProgressBar {
    background-color: #0a0a0a;
    border: 1px solid #333333;
    border-radius: 4px;
    text-align: center;
    color: #9ACD32;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6B8E23, stop:0.5 #9ACD32, stop:1 #7FFF00);
    border-radius: 3px;
}

QComboBox {
    background-color: #0a0a0a;
    color: #9ACD32;
    border: 1px solid #333333;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 10pt;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9ACD32;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #0a0a0a;
    color: #9ACD32;
    selection-background-color: #2d5016;
    border: 1px solid #333333;
}

QTabWidget::pane {
    border: 1px solid #333333;
    border-radius: 4px;
    background-color: #000000;
}

QTabBar::tab {
    background-color: #1a1a1a;
    color: #9ACD32;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #333333;
}

QTabBar::tab:selected {
    background-color: #2d5016;
    color: #9ACD32;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #2a2a2a;
}

QMessageBox {
    background-color: #000000;
}

QMessageBox QLabel {
    color: #9ACD32;
}

QMessageBox QPushButton {
    min-width: 80px;
    min-height: 25px;
}
"""


def apply_brainlink_style(widget):
    """Apply BrainLink dark theme to a widget"""
    widget.setStyleSheet(BRAINLINK_DARK_STYLE)
