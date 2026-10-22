from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer

from config import APP_NAME, APP_SUBTITLE, APP_VERSION, COLORS
from ui.tabs import ScanTab, StudentsTab, LogsTab, RegisterTab, AnalyticsTab, SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self, db, face_engine, liveness_detector, mood_ai, camera_thread, cloud_sync):
        super().__init__()
        self.db = db
        self.face_engine = face_engine
        self.liveness_detector = liveness_detector
        self.mood_ai = mood_ai
        self.camera_thread = camera_thread
        self.cloud_sync = cloud_sync

        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE} (v{APP_VERSION})")
        self.setMinimumSize(1260, 820)
        self.resize(1340, 880)

        self.ticker_messages = [
            "🛡 <b>Anti-Proxy Active</b> — Multi-Factor Biometric Liveness Enabled",
            "🧠 <b>Mood AI</b> — Gemini Vision Analyzing Student Expressions",
            "📈 <b>AI Prediction</b> — Attendance Trajectory Forecasting Live",
            "⚡ <b>Blink Detection</b> — Real-Time EAR Biometric Analysis Active",
            "🎯 <b>Depth Analysis</b> — Laplacian Anti-Spoof Screen Protection On"
        ]
        self.ticker_index = 0

        self._init_ui()
        self._connect_sync()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ══════════════ 1. TOP BAR ══════════════
        top_bar = QFrame()
        top_bar.setFixedHeight(64)
        top_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #04080f, stop:0.5 #080e1a, stop:1 #04080f);
            border-bottom: 1px solid {COLORS['border2']};
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(16)

        # Logo
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(10)
        logo_icon = QLabel("👁")
        logo_icon.setFixedSize(38, 38)
        logo_icon.setFont(QFont("Segoe UI", 16))
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['cyan']}, stop:1 {COLORS['purple']});
            color: #04080f;
            border-radius: 10px;
        """)

        logo_text_box = QVBoxLayout()
        logo_text_box.setSpacing(0)
        logo_text = QLabel(f"FaceAttend <span style='color:{COLORS['cyan']}'>PRO</span>")
        logo_text.setFont(QFont("Segoe UI", 13, QFont.Weight.ExtraBold))
        logo_text.setStyleSheet(f"color: {COLORS['text']};")

        logo_sub = QLabel(APP_SUBTITLE)
        logo_sub.setFont(QFont("JetBrains Mono", 7, QFont.Weight.Bold))
        logo_sub.setStyleSheet(f"color: {COLORS['cyan']}; letter-spacing: 0.8px;")

        logo_text_box.addWidget(logo_text)
        logo_text_box.addWidget(logo_sub)
        logo_layout.addWidget(logo_icon)
        logo_layout.addLayout(logo_text_box)
        top_layout.addLayout(logo_layout)

        top_layout.addSpacing(20)

        # Navigation Tabs
        self.nav_buttons = []
        tabs_info = [
            ("📸 Live Scan", 0),
            ("👥 Students", 1),
            ("📋 Logs", 2),
            ("📅 Register", 3),
            ("📊 Analytics", 4)
        ]

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)
        for label, idx in tabs_info:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setProperty("class", "nav-btn-active" if idx == 0 else "nav-btn")
            btn.clicked.connect(lambda ch, i=idx: self.switch_tab(i))
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        top_layout.addLayout(nav_layout)

        top_layout.addStretch()

        # Top Bar Quick Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.ts_present = self._create_top_stat("0", "PRESENT", COLORS["green"])
        self.ts_absent = self._create_top_stat("0", "ABSENT", COLORS["red"])
        self.ts_spoofs = self._create_top_stat("0", "SPOOFS", COLORS["amber"])
        self.ts_rate = self._create_top_stat("0%", "RATE", COLORS["cyan"])

        stats_layout.addLayout(self.ts_present)
        stats_layout.addLayout(self.ts_absent)
        stats_layout.addLayout(self.ts_spoofs)
        stats_layout.addLayout(self.ts_rate)
        top_layout.addLayout(stats_layout)

        top_layout.addSpacing(16)

        # Settings Button
        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.setFixedHeight(34)
        btn_settings.clicked.connect(self._open_settings)
        top_layout.addWidget(btn_settings)

        root_layout.addWidget(top_bar)

        # ══════════════ 2. TICKER BAR ══════════════
        ticker_bar = QFrame()
        ticker_bar.setFixedHeight(32)
        ticker_bar.setStyleSheet(f"""
            background-color: rgba(0, 229, 255, 0.04);
            border-bottom: 1px solid {COLORS['border']};
        """)
        ticker_layout = QHBoxLayout(ticker_bar)
        ticker_layout.setContentsMargins(20, 0, 20, 0)

        self.ticker_label = QLabel(self.ticker_messages[0])
        self.ticker_label.setFont(QFont("Segoe UI", 9))
        self.ticker_label.setStyleSheet(f"color: {COLORS['dim']};")

        self.cloud_status_badge = QLabel("⚡ SQLite Local Cache")
        self.cloud_status_badge.setFont(QFont("JetBrains Mono", 8, QFont.Weight.Bold))
        self.cloud_status_badge.setStyleSheet(f"color: {COLORS['green']};")

        ticker_layout.addWidget(self.ticker_label)
        ticker_layout.addStretch()
        ticker_layout.addWidget(self.cloud_status_badge)
        root_layout.addWidget(ticker_bar)

        # Timer to cycle ticker messages smoothly
        self.ticker_timer = QTimer(self)
        self.ticker_timer.timeout.connect(self._cycle_ticker)
        self.ticker_timer.start(4500)

        # ══════════════ 3. STACKED TAB PAGES ══════════════
        self.stack = QStackedWidget()

        self.scan_tab = ScanTab(self.db, self.face_engine, self.liveness_detector, self.mood_ai, self.camera_thread)
        self.students_tab = StudentsTab(self.db, self.face_engine, self.camera_thread)
        self.logs_tab = LogsTab(self.db)
        self.register_tab = RegisterTab(self.db)
        self.analytics_tab = AnalyticsTab(self.db)

        self.stack.addWidget(self.scan_tab)
        self.stack.addWidget(self.students_tab)
        self.stack.addWidget(self.logs_tab)
        self.stack.addWidget(self.register_tab)
        self.stack.addWidget(self.analytics_tab)

        root_layout.addWidget(self.stack, 1)

        # Cross-Tab Signal Connections
        self.scan_tab.attendance_updated.connect(self._on_data_updated)
        self.students_tab.students_changed.connect(self._on_data_updated)
        self.register_tab.register_changed.connect(self._on_data_updated)

        self._update_top_stats()

    def _create_top_stat(self, value, label, color):
        layout = QVBoxLayout()
        layout.setSpacing(0)

        val = QLabel(value)
        val.setFont(QFont("JetBrains Mono", 12, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {color};")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['muted']}; letter-spacing: 0.5px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(val)
        layout.addWidget(lbl)
        return layout

    def _cycle_ticker(self):
        self.ticker_index = (self.ticker_index + 1) % len(self.ticker_messages)
        self.ticker_label.setText(self.ticker_messages[self.ticker_index])

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("class", "nav-btn-active" if i == index else "nav-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh tab contents on open
        if index == 0:
            self.scan_tab.refresh_roster_list()
        elif index == 1:
            self.students_tab.refresh_students()
        elif index == 2:
            self.logs_tab.refresh_logs()
        elif index == 3:
            self.register_tab.refresh_register()
        elif index == 4:
            self.analytics_tab.refresh_analytics()

        self._update_top_stats()

    def _on_data_updated(self):
        self._update_top_stats()
        # Refresh current tab
        idx = self.stack.currentIndex()
        if idx == 0:
            self.scan_tab.refresh_roster_list()
        elif idx == 1:
            self.students_tab.refresh_students()
        elif idx == 2:
            self.logs_tab.refresh_logs()
        elif idx == 3:
            self.register_tab.refresh_register()
        elif idx == 4:
            self.analytics_tab.refresh_analytics()

    def _update_top_stats(self):
        students = self.db.get_all_students()
        today_str = datetime.now().strftime("%Y-%m-%d")
        lecture = "IoT"
        att = self.db.get_attendance_for_lecture(today_str, lecture)

        p = sum(1 for a in att if a["status"] == "present")
        t = len(students)
        a = max(0, t - p)
        r = int(round((p / t * 100))) if t > 0 else 0

        logs = self.db.get_recent_logs(200)
        s = sum(1 for l in logs if l.get("is_spoof") and today_str in l.get("timestamp", ""))

        self.ts_present.itemAt(0).widget().setText(str(p))
        self.ts_absent.itemAt(0).widget().setText(str(a))
        self.ts_spoofs.itemAt(0).widget().setText(str(s))
        self.ts_rate.itemAt(0).widget().setText(f"{r}%")

    def _connect_sync(self):
        self.cloud_sync.sync_status.connect(self._on_sync_status)
        self.cloud_sync.start()

    def _on_sync_status(self, state, msg):
        if state == "connected":
            self.cloud_status_badge.setText(f"🔥 {msg}")
            self.cloud_status_badge.setStyleSheet(f"color: {COLORS['green']};")
        elif state == "connecting" or state == "syncing":
            self.cloud_status_badge.setText(f"🔄 {msg}")
            self.cloud_status_badge.setStyleSheet(f"color: {COLORS['amber']};")
        else:
            self.cloud_status_badge.setText(f"⚡ {msg}")
            self.cloud_status_badge.setStyleSheet(f"color: {COLORS['cyan']};")

    def _open_settings(self):
        dialog = SettingsDialog(self.db, self.mood_ai, self.cloud_sync, self)
        if dialog.exec():
            # Refresh camera index if changed
            cam_idx = int(self.db.get_setting("camera_index", "0"))
            if self.camera_thread.camera_index != cam_idx:
                self.camera_thread.set_camera_index(cam_idx)

    def closeEvent(self, event):
        self.camera_thread.stop()
        self.cloud_sync.stop()
        event.accept()
