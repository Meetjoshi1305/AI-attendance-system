from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from config import COLORS, MOOD_MAP

class StudentCard(QFrame):
    delete_requested = pyqtSignal(int)

    def __init__(self, student_data, parent=None):
        super().__init__(parent)
        self.student = student_data
        self.setProperty("class", "card")
        self.setStyleSheet(f"""
            QFrame[class="card"] {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border2']};
                border-radius: 14px;
            }}
            QFrame[class="card"]:hover {{
                border-color: {COLORS['cyan']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Header (Avatar + Name + Roll)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        color = student_data.get("color", COLORS["cyan"])
        initials = student_data.get("avatar_initials", "ST")

        self.avatar_lbl = QLabel(initials)
        self.avatar_lbl.setFixedSize(42, 42)
        self.avatar_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            border: 2px solid {color}44;
            border-radius: 10px;
        """)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        name_lbl = QLabel(student_data.get("name", "Unknown"))
        name_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {COLORS['text']};")

        roll_lbl = QLabel(f"Roll: {student_data.get('roll_no', 'N/A')} · {'✅ Enrolled' if student_data.get('enrolled') else '⚠️ Not Enrolled'}")
        roll_lbl.setFont(QFont("Segoe UI", 9))
        roll_lbl.setStyleSheet(f"color: {COLORS['green'] if student_data.get('enrolled') else COLORS['muted']};")

        name_layout.addWidget(name_lbl)
        name_layout.addWidget(roll_lbl)

        header_layout.addWidget(self.avatar_lbl)
        header_layout.addLayout(name_layout)
        header_layout.addStretch()

        # 2. Mini Stats Grid (Present, Absent, Streak)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(6)

        present = student_data.get("present_count", 0)
        total = student_data.get("total_count", 0)
        absent = max(0, total - present)
        streak = student_data.get("streak", 0)

        for val, lbl, c, bg in [
            (str(present), "Present", COLORS["green"], "rgba(0, 255, 136, 0.08)"),
            (str(absent), "Absent", COLORS["red"], "rgba(255, 61, 90, 0.08)"),
            (f"{streak}d 🔥", "Streak", COLORS["amber"], "rgba(255, 184, 0, 0.08)")
        ]:
            cell = QFrame()
            cell.setStyleSheet(f"background-color: {bg}; border-radius: 8px; padding: 4px;")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(4, 4, 4, 4)
            cl.setSpacing(1)

            vl = QLabel(val)
            vl.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
            vl.setStyleSheet(f"color: {c};")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            tl = QLabel(lbl.upper())
            tl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            tl.setStyleSheet(f"color: {COLORS['dim']};")
            tl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            cl.addWidget(vl)
            cl.addWidget(tl)
            stats_layout.addWidget(cell)

        # 3. Attendance Rate Bar
        rate = int(round((present / total * 100))) if total > 0 else 100
        rate_color = COLORS["green"] if rate >= 90 else COLORS["amber"] if rate >= 75 else COLORS["red"]

        pbar_layout = QVBoxLayout()
        pbar_layout.setSpacing(3)

        pbar_header = QHBoxLayout()
        pbar_lbl = QLabel("ATTENDANCE RATE")
        pbar_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        pbar_lbl.setStyleSheet(f"color: {COLORS['muted']};")

        rate_val = QLabel(f"{rate}%")
        rate_val.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        rate_val.setStyleSheet(f"color: {rate_color};")

        pbar_header.addWidget(pbar_lbl)
        pbar_header.addStretch()
        pbar_header.addWidget(rate_val)

        pbar = QProgressBar()
        pbar.setValue(rate)
        pbar.setFixedHeight(5)
        pbar.setTextVisible(False)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['border']};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {rate_color};
                border-radius: 2px;
            }}
        """)

        pbar_layout.addLayout(pbar_header)
        pbar_layout.addWidget(pbar)

        # 4. Delete Action Button
        del_btn = QPushButton("🗑 Remove Student")
        del_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 61, 90, 0.08);
                border: 1px solid rgba(255, 61, 90, 0.25);
                color: {COLORS['red']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 61, 90, 0.2);
                border-color: {COLORS['red']};
            }}
        """)
        del_btn.clicked.connect(self._on_delete)

        layout.addLayout(header_layout)
        layout.addLayout(stats_layout)
        layout.addLayout(pbar_layout)
        layout.addWidget(del_btn)

    def _on_delete(self):
        reply = QMessageBox.question(
            self,
            "Remove Student",
            f"Are you sure you want to remove {self.student.get('name')} from the roster?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.student["id"])
