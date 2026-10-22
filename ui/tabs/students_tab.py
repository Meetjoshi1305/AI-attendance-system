import os
import time
import random
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QGridLayout, QFrame, QMessageBox
)
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from config import COLORS, PALETTE_AVATAR, SNAPSHOTS_DIR
from ui.components.student_card import StudentCard

class StudentsTab(QWidget):
    students_changed = pyqtSignal()

    def __init__(self, db, face_engine, camera_thread, parent=None):
        super().__init__(parent)
        self.db = db
        self.face_engine = face_engine
        self.camera_thread = camera_thread

        self.captured_frame = None
        self.captured_embedding = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header Row
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Students Roster")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")

        self.sub_title = QLabel("0 enrolled students")
        self.sub_title.setFont(QFont("Segoe UI", 10))
        self.sub_title.setStyleSheet(f"color: {COLORS['muted']};")

        title_box.addWidget(title)
        title_box.addWidget(self.sub_title)
        header.addLayout(title_box)
        header.addStretch()

        self.btn_toggle_enroll = QPushButton("+ Enroll New Face")
        self.btn_toggle_enroll.setProperty("class", "btn-primary")
        self.btn_toggle_enroll.setFixedHeight(36)
        self.btn_toggle_enroll.clicked.connect(self._toggle_enroll_box)

        self.btn_seed = QPushButton("⚡ Load Demo Roster")
        self.btn_seed.setProperty("class", "btn-purple")
        self.btn_seed.setFixedHeight(36)
        self.btn_seed.clicked.connect(self._seed_demo_roster)

        header.addWidget(self.btn_toggle_enroll)
        header.addWidget(self.btn_seed)
        layout.addLayout(header)

        # 2. Enrollment Form Drawer (Hidden by default)
        self.enroll_box = QFrame()
        self.enroll_box.setProperty("class", "card")
        self.enroll_box.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border: 1px solid rgba(0, 229, 255, 0.35);
            border-radius: 14px;
            padding: 16px;
        """)
        self.enroll_box.setVisible(False)

        eb_layout = QHBoxLayout(self.enroll_box)
        eb_layout.setSpacing(20)

        # Form Inputs (Left)
        inputs_layout = QVBoxLayout()
        inputs_layout.setSpacing(10)

        eb_title = QLabel("📸 ENROLL NEW STUDENT FACE")
        eb_title.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        eb_title.setStyleSheet(f"color: {COLORS['cyan']};")

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Full Name (e.g. Maya Patel)")

        self.input_roll = QLineEdit()
        self.input_roll.setPlaceholderText("Roll / Enrollment No (e.g. CS-2024-04)")

        # Enrollment Action Buttons
        btn_capture_row = QHBoxLayout()
        self.btn_cap_cam = QPushButton("📷 Capture from Webcam")
        self.btn_cap_cam.clicked.connect(self._capture_webcam_face)

        self.btn_synth = QPushButton("🎨 Synth Biometric Template")
        self.btn_synth.clicked.connect(self._generate_synthetic_face)

        btn_capture_row.addWidget(self.btn_cap_cam)
        btn_capture_row.addWidget(self.btn_synth)

        self.btn_save_student = QPushButton("💾 Save & Enroll Student")
        self.btn_save_student.setProperty("class", "btn-success")
        self.btn_save_student.setFixedHeight(38)
        self.btn_save_student.clicked.connect(self._save_student)

        inputs_layout.addWidget(eb_title)
        inputs_layout.addWidget(self.input_name)
        inputs_layout.addWidget(self.input_roll)
        inputs_layout.addLayout(btn_capture_row)
        inputs_layout.addWidget(self.btn_save_student)

        # Face Preview (Right)
        preview_box = QVBoxLayout()
        self.preview_lbl = QLabel("No Face Captured")
        self.preview_lbl.setFixedSize(140, 140)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet(f"""
            background-color: {COLORS['card2']};
            border: 1px dashed {COLORS['border2']};
            border-radius: 10px;
            color: {COLORS['muted']};
        """)

        preview_box.addWidget(self.preview_lbl)
        preview_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        eb_layout.addLayout(inputs_layout, 2)
        eb_layout.addLayout(preview_box, 1)

        layout.addWidget(self.enroll_box)

        # 3. Students Grid (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area, 1)

        self.refresh_students()

    def _toggle_enroll_box(self):
        is_vis = self.enroll_box.isVisible()
        self.enroll_box.setVisible(not is_vis)
        self.btn_toggle_enroll.setText("+ Enroll New Face" if is_vis else "✕ Close Enrollment")

    def _capture_webcam_face(self):
        frame = self.camera_thread.get_latest_frame()
        if frame is None:
            QMessageBox.warning(self, "Camera Inactive", "Please start the camera on the Live Scan tab first, or use 'Synth Biometric Template'.")
            return

        faces = self.face_engine.detect_faces(frame)
        if not faces:
            QMessageBox.warning(self, "No Face Detected", "Please position your face in the camera frame and try again.")
            return

        self.captured_frame = frame
        face = faces[0]
        self.captured_embedding = self.face_engine.extract_features(frame, face)

        # Show preview
        bx, by, bw, bh = face["box"]
        crop = frame[by:by+bh, bx:bx+bw]
        if crop.size > 0:
            rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_lbl.setPixmap(pixmap)
            self.preview_lbl.setStyleSheet(f"border: 2px solid {COLORS['green']}; border-radius: 10px;")

    def _generate_synthetic_face(self):
        name = self.input_name.text().strip() or "Student"
        initials = "".join([w[0] for w in name.split()[:2]]).upper() or "ST"
        color = random.choice(PALETTE_AVATAR)

        # Generate synthetic 128D normalized embedding
        seed = int(time.time() * 1000) % 100000
        np.random.seed(seed)
        emb = np.random.randn(128).astype(np.float32)
        emb /= np.linalg.norm(emb)
        self.captured_embedding = emb
        self.captured_frame = None

        # Display preview label
        self.preview_lbl.setText(f"{initials}\n\n🎨 Synthetic\nBiometric")
        self.preview_lbl.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        self.preview_lbl.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            border: 2px solid {color};
            border-radius: 10px;
        """)

    def _save_student(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter the student's full name.")
            return

        if self.captured_embedding is None:
            # Auto-generate synthetic template if not captured
            self._generate_synthetic_face()

        roll = self.input_roll.text().strip() or f"ROLL-{random.randint(100, 999)}"
        initials = "".join([w[0] for w in name.split()[:2]]).upper() or "ST"
        color = random.choice(PALETTE_AVATAR)

        photo_path = ""
        if self.captured_frame is not None:
            photo_path = os.path.join(SNAPSHOTS_DIR, f"stu_{int(time.time()*1000)}.jpg")
            cv2.imwrite(photo_path, self.captured_frame)

        new_student = {
            "id": int(time.time() * 1000),
            "name": name,
            "roll_no": roll,
            "avatar_initials": initials,
            "color": color,
            "enrolled": 1,
            "present_count": 1,
            "total_count": 1,
            "streak": 1,
            "face_photo_path": photo_path,
            "embedding": self.captured_embedding
        }

        self.db.add_or_update_student(new_student)
        self.input_name.clear()
        self.input_roll.clear()
        self.captured_frame = None
        self.captured_embedding = None
        self.preview_lbl.clear()
        self.preview_lbl.setText("No Face Captured")
        self.preview_lbl.setStyleSheet(f"background-color: {COLORS['card2']}; border: 1px dashed {COLORS['border2']}; border-radius: 10px; color: {COLORS['muted']};")

        self._toggle_enroll_box()
        self.refresh_students()
        self.students_changed.emit()

    def _seed_demo_roster(self):
        reply = QMessageBox.question(
            self,
            "Load Demo Roster",
            "This will seed 6 realistic sample students with past attendance records and streaks. Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.seed_demo_roster()
            self.refresh_students()
            self.students_changed.emit()

    def refresh_students(self):
        # Clear existing grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        students = self.db.get_all_students()
        self.sub_title.setText(f"{len(students)} enrolled students")

        if not students:
            empty = QLabel("No students enrolled yet. Click '+ Enroll New Face' or 'Load Demo Roster' above.")
            empty.setFont(QFont("Segoe UI", 12))
            empty.setStyleSheet(f"color: {COLORS['muted']}; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty, 0, 0, 1, 3)
            return

        cols = 3
        for idx, student in enumerate(students):
            card = StudentCard(student)
            card.delete_requested.connect(self._on_student_deleted)
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(card, r, c)

    def _on_student_deleted(self, student_id):
        self.db.delete_student(student_id)
        self.refresh_students()
        self.students_changed.emit()
