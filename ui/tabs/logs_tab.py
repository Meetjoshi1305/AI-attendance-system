import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt
from config import COLORS, MOOD_MAP

class LogsTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_log_id = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        # ══════════════ LEFT COLUMN: LOGS TABLE ══════════════
        left_frame = QFrame()
        left_frame.setProperty("class", "card")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        title = QLabel("Audit & Anti-Proxy Logs")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")

        self.sub_title = QLabel("0 recognized, 0 spoof attempts")
        self.sub_title.setFont(QFont("Segoe UI", 10))
        self.sub_title.setStyleSheet(f"color: {COLORS['muted']};")

        header_layout.addWidget(title)
        header_layout.addWidget(self.sub_title)
        left_layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Student / Event", "Timestamp", "Liveness", "Mood", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._on_row_clicked)

        left_layout.addWidget(self.table)
        main_layout.addWidget(left_frame, 6)

        # ══════════════ RIGHT COLUMN: LOG DETAIL INSPECTOR ══════════════
        self.right_frame = QFrame()
        self.right_frame.setProperty("class", "card")
        self.right_frame.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border2']};
            border-radius: 14px;
        """)
        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(16, 16, 16, 16)
        self.right_layout.setSpacing(12)

        # Detail Header
        detail_title = QLabel("EVENT INSPECTION")
        detail_title.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        detail_title.setStyleSheet(f"color: {COLORS['muted']}; letter-spacing: 0.5px;")
        self.right_layout.addWidget(detail_title)

        # Scroll area for detail content
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setStyleSheet("background: transparent; border: none;")

        self.detail_container = QWidget()
        self.detail_content_layout = QVBoxLayout(self.detail_container)
        self.detail_content_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_content_layout.setSpacing(10)
        self.detail_scroll.setWidget(self.detail_container)

        self.right_layout.addWidget(self.detail_scroll)
        main_layout.addWidget(self.right_frame, 4)

        self.refresh_logs()

    def refresh_logs(self):
        logs = self.db.get_recent_logs(limit=100)
        real_count = sum(1 for l in logs if not l.get("is_spoof"))
        spoof_count = sum(1 for l in logs if l.get("is_spoof"))
        self.sub_title.setText(f"{real_count} recognized, {spoof_count} spoof attempts")

        self.table.setRowCount(len(logs))
        for row, l in enumerate(logs):
            is_spoof = bool(l.get("is_spoof"))

            # Column 0: Name / Event
            name_text = "⛔ SPOOF ATTEMPT" if is_spoof else l.get("student_name", "Student")
            name_item = QTableWidgetItem(name_text)
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if is_spoof:
                name_item.setForeground(Qt.GlobalColor.red)
            name_item.setData(Qt.ItemDataRole.UserRole, l["id"])
            self.table.setItem(row, 0, name_item)

            # Column 1: Time
            time_item = QTableWidgetItem(l.get("timestamp", ""))
            time_item.setFont(QFont("JetBrains Mono", 9))
            self.table.setItem(row, 1, time_item)

            # Column 2: Liveness
            live_dict = l.get("liveness", {})
            score = live_dict.get("overall", "—")
            live_item = QTableWidgetItem(f"{score}%" if score != "—" else "—")
            live_item.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            if is_spoof:
                live_item.setForeground(Qt.GlobalColor.red)
            else:
                live_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 2, live_item)

            # Column 3: Mood
            mood_key = l.get("mood")
            mood_info = MOOD_MAP.get(mood_key, None)
            mood_text = mood_info["e"] if mood_info else "—"
            mood_item = QTableWidgetItem(mood_text)
            mood_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, mood_item)

            # Column 4: Status Badge
            status_text = "⛔ BLOCKED" if is_spoof else "✅ OK"
            status_item = QTableWidgetItem(status_text)
            status_item.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            status_item.setForeground(Qt.GlobalColor.red if is_spoof else Qt.GlobalColor.green)
            self.table.setItem(row, 4, status_item)

        if logs and self.selected_log_id is None:
            self._render_detail(logs[0])

    def _on_row_clicked(self, row, col):
        item = self.table.item(row, 0)
        if not item:
            return
        log_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_log_id = log_id
        logs = self.db.get_recent_logs(limit=100)
        target = next((l for l in logs if l["id"] == log_id), None)
        if target:
            self._render_detail(target)

    def _render_detail(self, log):
        # Clear existing layout
        while self.detail_content_layout.count():
            item = self.detail_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        is_spoof = bool(log.get("is_spoof"))
        live = log.get("liveness", {})
        snap_path = log.get("snapshot_path", "")

        # Snapshot Preview
        snap_lbl = QLabel()
        snap_lbl.setFixedHeight(180)
        snap_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        snap_lbl.setStyleSheet(f"background-color: {COLORS['card2']}; border: 1px solid {COLORS['border2']}; border-radius: 10px;")

        if snap_path and os.path.exists(snap_path):
            pix = QPixmap(snap_path).scaled(280, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            snap_lbl.setPixmap(pix)
        else:
            snap_lbl.setText("📷 Snapshot Stored")
            snap_lbl.setStyleSheet(f"color: {COLORS['muted']};")

        self.detail_content_layout.addWidget(snap_lbl)

        # Status Banner
        status_banner = QLabel("⛔ ANTI-PROXY BLOCKED" if is_spoof else "✅ VERIFIED ATTENDANCE")
        status_banner.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
        status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_banner.setStyleSheet(f"""
            background: {'rgba(255,61,90,0.1)' if is_spoof else 'rgba(0,255,136,0.1)'};
            color: {COLORS['red'] if is_spoof else COLORS['green']};
            border: 1px solid {'rgba(255,61,90,0.3)' if is_spoof else 'rgba(0,255,136,0.3)'};
            border-radius: 8px;
            padding: 8px;
        """)
        self.detail_content_layout.addWidget(status_banner)

        # Biometric Breakdown Rows
        details_box = QFrame()
        details_box.setProperty("class", "card2")
        db_layout = QVBoxLayout(details_box)
        db_layout.setContentsMargins(10, 8, 10, 8)
        db_layout.setSpacing(6)

        rows = [
            ("Timestamp", log.get("timestamp", "—"), COLORS["dim"]),
            ("Student", log.get("student_name") or "Unknown", COLORS["cyan"] if not is_spoof else COLORS["red"]),
            ("Blink Score", f"{live.get('blink', 0)}%", COLORS["green"] if live.get("blink", 0) > 50 else COLORS["red"]),
            ("Motion Score", f"{live.get('motion', 0)}%", COLORS["green"] if live.get("motion", 0) > 40 else COLORS["red"]),
            ("Depth / Texture", f"{live.get('depth', 0)}%", COLORS["green"] if live.get("depth", 0) > 30 else COLORS["red"]),
            ("Overall Score", f"{live.get('overall', 0)}% ({'PASS' if not is_spoof else 'FAIL'})", COLORS["green"] if not is_spoof else COLORS["red"]),
            ("Mood", log.get("mood", "—").capitalize() if log.get("mood") else "—", COLORS["purple"]),
            ("Confidence", log.get("confidence", "—").capitalize() if log.get("confidence") else "—", COLORS["dim"]),
        ]

        for lbl, val, color in rows:
            r_layout = QHBoxLayout()
            l_lbl = QLabel(lbl)
            l_lbl.setFont(QFont("Segoe UI", 9))
            l_lbl.setStyleSheet(f"color: {COLORS['muted']};")

            v_lbl = QLabel(val)
            v_lbl.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            v_lbl.setStyleSheet(f"color: {color};")

            r_layout.addWidget(l_lbl)
            r_layout.addStretch()
            r_layout.addWidget(v_lbl)
            db_layout.addLayout(r_layout)

        self.detail_content_layout.addWidget(details_box)

        # AI Notes
        notes = log.get("description", "")
        if notes:
            notes_lbl = QLabel(f"<b>AI Diagnosis:</b> {notes}")
            notes_lbl.setFont(QFont("Segoe UI", 9))
            notes_lbl.setWordWrap(True)
            notes_lbl.setStyleSheet(f"""
                background: rgba(0, 229, 255, 0.05);
                border: 1px solid rgba(0, 229, 255, 0.15);
                border-radius: 8px;
                padding: 8px;
                color: {COLORS['dim']};
            """)
            self.detail_content_layout.addWidget(notes_lbl)

        self.detail_content_layout.addStretch()
