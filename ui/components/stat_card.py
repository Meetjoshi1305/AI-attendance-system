from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from config import COLORS

class StatCard(QFrame):
    def __init__(self, value="0", label="STAT", color=COLORS["green"], parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setStyleSheet(f"""
            QFrame[class="card"] {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border2']};
                border-radius: 12px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self.val_label = QLabel(str(value))
        self.val_label.setFont(QFont("JetBrains Mono", 20, QFont.Weight.Bold))
        self.val_label.setStyleSheet(f"color: {color};")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.txt_label = QLabel(label.upper())
        self.txt_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.txt_label.setStyleSheet(f"color: {COLORS['muted']}; letter-spacing: 0.5px;")
        self.txt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.val_label)
        layout.addWidget(self.txt_label)

    def set_value(self, value):
        self.val_label.setText(str(value))
