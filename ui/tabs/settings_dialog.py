from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QFrame, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import requests

from config import COLORS

class SettingsDialog(QDialog):
    def __init__(self, db, mood_ai, cloud_sync, parent=None):
        super().__init__(parent)
        self.db = db
        self.mood_ai = mood_ai
        self.cloud_sync = cloud_sync

        self.setWindowTitle("FaceAttend PRO — System Settings & Cloud Sync")
        self.setFixedSize(540, 560)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
            }}
            QFrame[class="card"] {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border2']};
                border-radius: 12px;
                padding: 14px;
            }}
        """)

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("System Settings")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")

        sub = QLabel("Configure Gemini Vision AI, Cloud Database, and Camera Hardware")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet(f"color: {COLORS['muted']};")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # 1. Gemini AI Card
        ai_card = QFrame()
        ai_card.setProperty("class", "card")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(8)

        ai_hdr = QLabel("🧠 GEMINI VISION AI CONFIGURATION")
        ai_hdr.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        ai_hdr.setStyleSheet(f"color: {COLORS['cyan']};")
        ai_layout.addWidget(ai_hdr)

        ai_form = QFormLayout()
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setPlaceholderText("Enter Google Gemini API Key...")

        test_ai_btn = QPushButton("Test API Key")
        test_ai_btn.clicked.connect(self._test_gemini_key)

        ai_row = QHBoxLayout()
        ai_row.addWidget(self.gemini_key_input, 1)
        ai_row.addWidget(test_ai_btn)

        self.ai_status_lbl = QLabel("Leave blank to use local computer vision expression heuristic.")
        self.ai_status_lbl.setFont(QFont("Segoe UI", 8))
        self.ai_status_lbl.setStyleSheet(f"color: {COLORS['muted']};")

        ai_form.addRow("API Key:", ai_row)
        ai_layout.addLayout(ai_form)
        ai_layout.addWidget(self.ai_status_lbl)
        main_layout.addWidget(ai_card)

        # 2. Cloud Database Sync Card
        cloud_card = QFrame()
        cloud_card.setProperty("class", "card")
        cloud_layout = QVBoxLayout(cloud_card)
        cloud_layout.setSpacing(8)

        cloud_hdr = QLabel("☁️ CLOUD DATABASE SYNCHRONIZATION")
        cloud_hdr.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        cloud_hdr.setStyleSheet(f"color: {COLORS['purple']};")
        cloud_layout.addWidget(cloud_hdr)

        self.cloud_enabled_cb = QCheckBox("Enable Multi-Device Cloud Sync")
        self.cloud_enabled_cb.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")
        cloud_layout.addWidget(self.cloud_enabled_cb)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Firebase Firestore", "Supabase"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        self.fb_project_input = QLineEdit()
        self.fb_project_input.setPlaceholderText("e.g. faceattend-pro-123")

        self.supabase_url_input = QLineEdit()
        self.supabase_url_input.setPlaceholderText("https://xyzcompany.supabase.co")

        self.supabase_key_input = QLineEdit()
        self.supabase_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.supabase_key_input.setPlaceholderText("Anon / Service API key")

        cloud_form = QFormLayout()
        cloud_form.addRow("Provider:", self.provider_combo)
        self.fb_label = QLabel("Project ID:")
        cloud_form.addRow(self.fb_label, self.fb_project_input)
        self.sb_url_label = QLabel("URL:")
        cloud_form.addRow(self.sb_url_label, self.supabase_url_input)
        self.sb_key_label = QLabel("API Key:")
        cloud_form.addRow(self.sb_key_label, self.supabase_key_input)
        cloud_layout.addLayout(cloud_form)

        test_cloud_btn = QPushButton("Test Cloud Connection")
        test_cloud_btn.clicked.connect(self._test_cloud)

        self.cloud_status_lbl = QLabel("Offline local SQLite mode is always active as cache.")
        self.cloud_status_lbl.setFont(QFont("Segoe UI", 8))
        self.cloud_status_lbl.setStyleSheet(f"color: {COLORS['muted']};")

        cloud_btn_row = QHBoxLayout()
        cloud_btn_row.addWidget(test_cloud_btn)
        cloud_btn_row.addWidget(self.cloud_status_lbl, 1)
        cloud_layout.addLayout(cloud_btn_row)

        main_layout.addWidget(cloud_card)

        # 3. Camera Selector Card
        cam_card = QFrame()
        cam_card.setProperty("class", "card")
        cam_layout = QHBoxLayout(cam_card)
        cam_layout.setSpacing(10)

        cam_lbl = QLabel("Webcam Device Index:")
        cam_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.cam_combo = QComboBox()
        self.cam_combo.addItems(["Camera 0 (Default)", "Camera 1 (External USB)", "Camera 2"])

        cam_layout.addWidget(cam_lbl)
        cam_layout.addWidget(self.cam_combo, 1)
        main_layout.addWidget(cam_card)

        # 4. Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Settings")
        btn_save.setProperty("class", "btn-primary")
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._save_settings)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        main_layout.addLayout(btn_box)

    def _load_values(self):
        # Gemini
        key = self.db.get_setting("gemini_api_key", "")
        self.gemini_key_input.setText(key)

        # Cloud
        enabled = self.db.get_setting("cloud_sync_enabled", "false").lower() == "true"
        self.cloud_enabled_cb.setChecked(enabled)

        prov = self.db.get_setting("cloud_provider", "firebase")
        if prov == "supabase":
            self.provider_combo.setCurrentIndex(1)
        else:
            self.provider_combo.setCurrentIndex(0)

        self.fb_project_input.setText(self.db.get_setting("firebase_project_id", ""))
        self.supabase_url_input.setText(self.db.get_setting("supabase_url", ""))
        self.supabase_key_input.setText(self.db.get_setting("supabase_key", ""))

        cam_idx = int(self.db.get_setting("camera_index", "0"))
        if cam_idx < self.cam_combo.count():
            self.cam_combo.setCurrentIndex(cam_idx)

        self._on_provider_changed()

    def _on_provider_changed(self):
        is_fb = self.provider_combo.currentIndex() == 0
        self.fb_label.setVisible(is_fb)
        self.fb_project_input.setVisible(is_fb)
        self.sb_url_label.setVisible(not is_fb)
        self.supabase_url_input.setVisible(not is_fb)
        self.sb_key_label.setVisible(not is_fb)
        self.supabase_key_input.setVisible(not is_fb)

    def _test_gemini_key(self):
        key = self.gemini_key_input.text().strip()
        if not key:
            self.ai_status_lbl.setText("Please enter an API key to test.")
            self.ai_status_lbl.setStyleSheet(f"color: {COLORS['amber']};")
            return

        self.ai_status_lbl.setText("Testing key...")
        self.ai_status_lbl.setStyleSheet(f"color: {COLORS['cyan']};")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
        try:
            r = requests.post(url, json=payload, timeout=6)
            if r.status_code == 200:
                self.ai_status_lbl.setText("✅ Gemini API Key valid and working!")
                self.ai_status_lbl.setStyleSheet(f"color: {COLORS['green']};")
            else:
                self.ai_status_lbl.setText(f"❌ HTTP {r.status_code}: Check key permissions.")
                self.ai_status_lbl.setStyleSheet(f"color: {COLORS['red']};")
        except Exception as e:
            self.ai_status_lbl.setText(f"Connection error: {str(e)[:30]}")
            self.ai_status_lbl.setStyleSheet(f"color: {COLORS['red']};")

    def _test_cloud(self):
        # Save temporary in DB for test
        self.db.set_setting("cloud_provider", "firebase" if self.provider_combo.currentIndex() == 0 else "supabase")
        self.db.set_setting("firebase_project_id", self.fb_project_input.text().strip())
        self.db.set_setting("supabase_url", self.supabase_url_input.text().strip())
        self.db.set_setting("supabase_key", self.supabase_key_input.text().strip())

        ok, msg = self.cloud_sync.test_connection()
        if ok:
            self.cloud_status_lbl.setText("✅ Cloud connection verified!")
            self.cloud_status_lbl.setStyleSheet(f"color: {COLORS['green']};")
        else:
            self.cloud_status_lbl.setText(f"❌ {msg[:40]}")
            self.cloud_status_lbl.setStyleSheet(f"color: {COLORS['red']};")

    def _save_settings(self):
        gemini_key = self.gemini_key_input.text().strip()
        self.db.set_setting("gemini_api_key", gemini_key)
        self.mood_ai.set_api_key(gemini_key)

        self.db.set_setting("cloud_sync_enabled", str(self.cloud_enabled_cb.isChecked()))
        self.db.set_setting("cloud_provider", "firebase" if self.provider_combo.currentIndex() == 0 else "supabase")
        self.db.set_setting("firebase_project_id", self.fb_project_input.text().strip())
        self.db.set_setting("supabase_url", self.supabase_url_input.text().strip())
        self.db.set_setting("supabase_key", self.supabase_key_input.text().strip())

        cam_idx = self.cam_combo.currentIndex()
        self.db.set_setting("camera_index", str(cam_idx))

        QMessageBox.information(self, "Settings Saved", "System configuration updated successfully!")
        self.accept()
