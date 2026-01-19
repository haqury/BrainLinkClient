"""Gyroscope data display form"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt

from services.head_tracker_service import HeadTracker


class GyroForm(QDialog):
    """Dialog for displaying gyroscope data"""
    
    def __init__(self, head_tracker: HeadTracker):
        super().__init__()
        self.head_tracker = head_tracker
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Gyroscope Data")
        self.setGeometry(300, 300, 350, 300)
        
        layout = QVBoxLayout(self)
        
        # Gyro values group
        gyro_group = QGroupBox("Gyroscope Values")
        gyro_layout = QGridLayout()
        
        # X value
        gyro_layout.addWidget(QLabel("X:"), 0, 0)
        self.lbl_x = QLabel("0")
        gyro_layout.addWidget(self.lbl_x, 0, 1)
        
        # Y value
        gyro_layout.addWidget(QLabel("Y:"), 1, 0)
        self.lbl_y = QLabel("0")
        gyro_layout.addWidget(self.lbl_y, 1, 1)
        
        # Z value
        gyro_layout.addWidget(QLabel("Z:"), 2, 0)
        self.lbl_z = QLabel("0")
        gyro_layout.addWidget(self.lbl_z, 2, 1)
        
        gyro_group.setLayout(gyro_layout)
        layout.addWidget(gyro_group)
        
        # Direction group
        direction_group = QGroupBox("Detected Direction")
        direction_layout = QVBoxLayout()
        
        self.lbl_direction = QLabel("Not calibrated")
        self.lbl_direction.setAlignment(Qt.AlignCenter)
        direction_layout.addWidget(self.lbl_direction)
        
        direction_group.setLayout(direction_layout)
        layout.addWidget(direction_group)
        
        # Control group
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()
        
        self.cb_use_gyro = QCheckBox("Use Gyro for Control")
        control_layout.addWidget(self.cb_use_gyro)
        
        self.btn_calibrate = QPushButton("Calibrate")
        self.btn_calibrate.clicked.connect(self.on_calibrate_clicked)
        control_layout.addWidget(self.btn_calibrate)
        
        self.btn_reset = QPushButton("Reset Calibration")
        self.btn_reset.clicked.connect(self.on_reset_clicked)
        control_layout.addWidget(self.btn_reset)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Close button
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)
    
    def update_gyro_data(self, x: int, y: int, z: int):
        """Update gyroscope data display"""
        self.current_x = x
        self.current_y = y
        self.current_z = z
        
        self.lbl_x.setText(str(x))
        self.lbl_y.setText(str(y))
        self.lbl_z.setText(str(z))
        
        # Update direction if calibrated
        if self.head_tracker.is_calibrated():
            direction = self.head_tracker.get_direction_key(x, y, z)
            if direction:
                self.lbl_direction.setText(f"Direction: {direction.upper()}")
            else:
                self.lbl_direction.setText("Center (No movement)")
        else:
            self.lbl_direction.setText("Not calibrated")
    
    def on_calibrate_clicked(self):
        """Handle calibrate button click"""
        self.head_tracker.calibrate(self.current_x, self.current_y, self.current_z)
        self.lbl_direction.setText("Calibrated! Center position set.")
    
    def on_reset_clicked(self):
        """Handle reset button click"""
        self.head_tracker.de_calibrate()
        self.lbl_direction.setText("Not calibrated")
    
    def is_using_gyro(self) -> bool:
        """Check if gyro control is enabled"""
        return self.cb_use_gyro.isChecked()
    
    def get_event_name(self) -> str:
        """Get current direction as event name"""
        if not self.head_tracker.is_calibrated():
            return ""
        
        direction = self.head_tracker.get_direction_key(
            self.current_x, self.current_y, self.current_z
        )
        
        # Convert direction to event name
        if direction == "left":
            return "ml"
        elif direction == "right":
            return "mr"
        elif direction == "up":
            return "mu"
        elif direction == "down":
            return "md"
        
        return ""
