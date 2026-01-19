"""EEG data display form"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QGroupBox
)
from PyQt5.QtCore import Qt

from models.eeg_models import BrainLinkModel


class EEGDataForm(QDialog):
    """Dialog for displaying EEG data values"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EEG Data")
        self.setGeometry(300, 300, 400, 400)
        
        layout = QVBoxLayout(self)
        
        # Data display group
        data_group = QGroupBox("Current EEG Values")
        data_layout = QGridLayout()
        
        # Attention
        data_layout.addWidget(QLabel("Attention:"), 0, 0)
        self.lbl_attention = QLabel("0")
        data_layout.addWidget(self.lbl_attention, 0, 1)
        
        # Meditation
        data_layout.addWidget(QLabel("Meditation:"), 1, 0)
        self.lbl_meditation = QLabel("0")
        data_layout.addWidget(self.lbl_meditation, 1, 1)
        
        # Delta
        data_layout.addWidget(QLabel("Delta:"), 2, 0)
        self.lbl_delta = QLabel("0")
        data_layout.addWidget(self.lbl_delta, 2, 1)
        
        # Theta
        data_layout.addWidget(QLabel("Theta:"), 3, 0)
        self.lbl_theta = QLabel("0")
        data_layout.addWidget(self.lbl_theta, 3, 1)
        
        # Low Alpha
        data_layout.addWidget(QLabel("Low Alpha:"), 4, 0)
        self.lbl_low_alpha = QLabel("0")
        data_layout.addWidget(self.lbl_low_alpha, 4, 1)
        
        # High Alpha
        data_layout.addWidget(QLabel("High Alpha:"), 5, 0)
        self.lbl_high_alpha = QLabel("0")
        data_layout.addWidget(self.lbl_high_alpha, 5, 1)
        
        # Low Beta
        data_layout.addWidget(QLabel("Low Beta:"), 6, 0)
        self.lbl_low_beta = QLabel("0")
        data_layout.addWidget(self.lbl_low_beta, 6, 1)
        
        # High Beta
        data_layout.addWidget(QLabel("High Beta:"), 7, 0)
        self.lbl_high_beta = QLabel("0")
        data_layout.addWidget(self.lbl_high_beta, 7, 1)
        
        # Low Gamma
        data_layout.addWidget(QLabel("Low Gamma:"), 8, 0)
        self.lbl_low_gamma = QLabel("0")
        data_layout.addWidget(self.lbl_low_gamma, 8, 1)
        
        # High Gamma
        data_layout.addWidget(QLabel("High Gamma:"), 9, 0)
        self.lbl_high_gamma = QLabel("0")
        data_layout.addWidget(self.lbl_high_gamma, 9, 1)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Close button
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)
    
    def update_data(self, model: BrainLinkModel):
        """Update displayed EEG data"""
        self.lbl_attention.setText(str(model.attention))
        self.lbl_meditation.setText(str(model.meditation))
        self.lbl_delta.setText(str(model.delta))
        self.lbl_theta.setText(str(model.theta))
        self.lbl_low_alpha.setText(str(model.low_alpha))
        self.lbl_high_alpha.setText(str(model.high_alpha))
        self.lbl_low_beta.setText(str(model.low_beta))
        self.lbl_high_beta.setText(str(model.high_beta))
        self.lbl_low_gamma.setText(str(model.low_gamma))
        self.lbl_high_gamma.setText(str(model.high_gamma))
