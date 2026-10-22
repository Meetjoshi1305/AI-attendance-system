import csv
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from config import COLORS, DEFAULT_LECTURES, MOOD_MAP

class RegisterTab(QWidget):
    register_changed = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_lecture = DEFAULT_LECTURES[0]
        self.selected_date = QDate.currentDate()

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Top Controls Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Lecture Buttons
        self.lec_buttons = []
        for lec in DEFAULT_LECTURES:
            btn = QPushButton(lec)
            btn.setFixedHeight(34)
            btn.setCheckable(True)
            if lec == self.selected_lecture:
                btn.setChecked(True)
                btn.setProperty("class", "nav-btn-active")
            else:
                btn.setProperty("class", "nav-btn")
            btn.clicked.connect(lambda checked, l=lec: self._on_lecture_changed(l))
            self.lec_buttons.append(btn)
            top_bar.addWidget(btn)

        top_bar.addSpacing(16)

        # Date Navigator (< DatePicker > Today)
        btn_prev = QPushButton("◀")
        btn_prev.setFixedSize(34, 34)
        btn_prev.clicked.connect(lambda: self._shift_date(-1))

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(self.selected_date)
        self.date_picker.setMaximumDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self._on_date_changed)
        self.date_picker.setFixedHeight(34)

        btn_next = QPushButton("▶")
        btn_next.setFixedSize(34, 34)
        btn_next.clicked.connect(lambda: self._shift_date(1))

        btn_today = QPushButton("Today")
        btn_today.setFixedHeight(34)
        btn_today.clicked.connect(lambda: self.date_picker.setDate(QDate.currentDate()))

        top_bar.addWidget(btn_prev)
        top_bar.addWidget(self.date_picker)
        top_bar.addWidget(btn_next)
        top_bar.addWidget(btn_today)

        top_bar.addStretch()

        # CSV Export
        btn_export = QPushButton("📥 Export CSV")
        btn_export.setProperty("class", "btn-success")
        btn_export.setFixedHeight(34)
        btn_export.clicked.connect(self._export_csv)
        top_bar.addWidget(btn_export)

        main_layout.addLayout(top_bar)

        # 2. Metric Cards Row
        metric_bar = QHBoxLayout()
        metric_bar.setSpacing(12)

        self.card_present = self._create_metric_card("0", "PRESENT", COLORS["green"])
        self.card_absent = self._create_metric_card("0", "ABSENT", COLORS["red"])
        self.card_rate = self._create_metric_card("0%", "ATTENDANCE RATE", COLORS["cyan"])
        self.card_spoofs = self._create_metric_card("0", "BLOCKED SPOOFS", COLORS["amber"])

        metric_bar.addWidget(self.card_present)
        metric_bar.addWidget(self.card_absent)
        metric_bar.addWidget(self.card_rate)
        metric_bar.addWidget(self.card_spoofs)
        main_layout.addLayout(metric_bar)

        # 3. Main Attendance Table
        table_frame = QFrame()
        table_frame.setProperty("class", "card")
        tf_layout = QVBoxLayout(table_frame)
        tf_layout.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Student Name", "Roll / ID", "Status", "Time Marked", "Mood", "Liveness", "Manual Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        tf_layout.addWidget(self.table)
        main_layout.addWidget(table_frame, 1)

        self.refresh_register()

    def _create_metric_card(self, value, label, color):
        frame = QFrame()
        frame.setProperty("class", "card")
        frame.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border2']};
            border-radius: 12px;
            padding: 8px;
        """)
        l = QVBoxLayout(frame)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(2)

        v = QLabel(value)
        v.setFont(QFont("JetBrains Mono", 18, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {color};")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t = QLabel(label)
        t.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {COLORS['muted']}; letter-spacing: 0.5px;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l.addWidget(v)
        l.addWidget(t)
        frame.val_label = v
        return frame

    def _on_lecture_changed(self, lecture):
        self.selected_lecture = lecture
        for btn in self.lec_buttons:
            if btn.text() == lecture:
                btn.setChecked(True)
                btn.setProperty("class", "nav-btn-active")
            else:
                btn.setChecked(False)
                btn.setProperty("class", "nav-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.refresh_register()

    def _on_date_changed(self, qdate):
        self.selected_date = qdate
        self.refresh_register()

    def _shift_date(self, delta_days):
        new_date = self.selected_date.addDays(delta_days)
        if new_date <= QDate.currentDate():
            self.date_picker.setDate(new_date)

    def refresh_register(self):
        date_str = self.selected_date.toString("yyyy-MM-dd")
        students = self.db.get_all_students()
        att_rows = self.db.get_attendance_for_lecture(date_str, self.selected_lecture)
        att_map = {a["student_id"]: a for a in att_rows}

        present_count = sum(1 for a in att_rows if a["status"] == "present")
        total_count = len(students)
        absent_count = max(0, total_count - present_count)
        rate = int(round((present_count / total_count * 100))) if total_count > 0 else 0

        # Blocked spoofs count from logs on that date
        logs = self.db.get_recent_logs(200)
        spoof_count = sum(1 for l in logs if l.get("is_spoof") and date_str in l.get("timestamp", ""))

        self.card_present.val_label.setText(str(present_count))
        self.card_absent.val_label.setText(str(absent_count))
        self.card_rate.val_label.setText(f"{rate}%")
        self.card_spoofs.val_label.setText(str(spoof_count))

        self.table.setRowCount(len(students))

        for row, s in enumerate(students):
            stu_id = s["id"]
            rec = att_map.get(stu_id)
            is_present = rec and rec["status"] == "present"

            # Column 0: Name
            name_item = QTableWidgetItem(s["name"])
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 0, name_item)

            # Column 1: Roll No
            roll_item = QTableWidgetItem(s.get("roll_no", "—"))
            roll_item.setFont(QFont("JetBrains Mono", 9))
            self.table.setItem(row, 1, roll_item)

            # Column 2: Status
            status_item = QTableWidgetItem("✅ Present" if is_present else "❌ Absent")
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setForeground(Qt.GlobalColor.green if is_present else Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)

            # Column 3: Time
            time_str = rec.get("time_str", "—") if is_present else "—"
            time_item = QTableWidgetItem(time_str)
            time_item.setFont(QFont("JetBrains Mono", 9))
            self.table.setItem(row, 3, time_item)

            # Column 4: Mood
            mood_key = rec.get("mood") if is_present else None
            mood_info = MOOD_MAP.get(mood_key, None)
            mood_item = QTableWidgetItem(f"{mood_info['e']} {mood_key.capitalize()}" if mood_info else "—")
            self.table.setItem(row, 4, mood_item)

            # Column 5: Liveness Score
            liveness_score = rec.get("liveness_score") if is_present else None
            live_item = QTableWidgetItem(f"{int(liveness_score)}%" if liveness_score is not None else "—")
            live_item.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            if is_present:
                live_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 5, live_item)

            # Column 6: Action Button (Manual Mark / Undo)
            btn_action = QPushButton("✕ Undo" if is_present else "✏ Mark Present")
            if is_present:
                btn_action.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255, 61, 90, 0.1);
                        color: {COLORS['red']};
                        border: 1px solid rgba(255, 61, 90, 0.3);
                        border-radius: 6px;
                        padding: 3px 8px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{ background: rgba(255, 61, 90, 0.25); }}
                """)
                btn_action.clicked.connect(lambda ch, sid=stu_id: self._undo_attendance(sid))
            else:
                btn_action.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(0, 229, 255, 0.1);
                        color: {COLORS['cyan']};
                        border: 1px solid rgba(0, 229, 255, 0.3);
                        border-radius: 6px;
                        padding: 3px 8px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{ background: rgba(0, 229, 255, 0.25); }}
                """)
                btn_action.clicked.connect(lambda ch, sid=stu_id: self._manual_mark(sid))

            self.table.setCellWidget(row, 6, btn_action)

    def _manual_mark(self, student_id):
        date_str = self.selected_date.toString("yyyy-MM-dd")
        self.db.mark_attendance(
            date_str=date_str,
            lecture=self.selected_lecture,
            student_id=student_id,
            status="present",
            mood="neutral",
            liveness_score=100.0,
            confidence="high",
            manual=1
        )
        self.refresh_register()
        self.register_changed.emit()

    def _undo_attendance(self, student_id):
        date_str = self.selected_date.toString("yyyy-MM-dd")
        self.db.unmark_attendance(date_str, self.selected_lecture, student_id)
        self.refresh_register()
        self.register_changed.emit()

    def _export_csv(self):
        date_str = self.selected_date.toString("yyyy-MM-dd")
        default_name = f"attendance_{date_str}_{self.selected_lecture}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Attendance CSV", default_name, "CSV Files (*.csv)")
        if not path:
            return

        students = self.db.get_all_students()
        att_rows = self.db.get_attendance_for_lecture(date_str, self.selected_lecture)
        att_map = {a["student_id"]: a for a in att_rows}

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Student Name", "Roll No", "Lecture", "Date", "Status", "Time Marked", "Mood", "Liveness Score", "Manual Override"])
            for s in students:
                rec = att_map.get(s["id"])
                is_p = rec and rec["status"] == "present"
                writer.writerow([
                    s["name"],
                    s.get("roll_no", ""),
                    self.selected_lecture,
                    date_str,
                    "Present" if is_p else "Absent",
                    rec.get("time_str", "—") if is_p else "—",
                    rec.get("mood", "—") if is_p else "—",
                    f"{rec.get('liveness_score', '—')}%" if is_p else "—",
                    "Yes" if (rec and rec.get("manual")) else "No"
                ])

        QMessageBox.information(self, "Export Complete", f"Attendance successfully exported to:\n{path}")
