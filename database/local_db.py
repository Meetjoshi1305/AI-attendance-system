import sqlite3
import json
import os
import time
from datetime import datetime, timedelta
import numpy as np
from config import DB_PATH, DEFAULT_LECTURES, PALETTE_AVATAR

class LocalDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Students Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                roll_no TEXT,
                avatar_initials TEXT,
                color TEXT,
                enrolled INTEGER DEFAULT 1,
                present_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                face_photo_path TEXT,
                embedding BLOB,
                created_at TEXT
            )
            """)

            # Attendance Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str TEXT NOT NULL,
                lecture TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                time_str TEXT NOT NULL,
                mood TEXT,
                liveness_score REAL,
                confidence TEXT,
                manual INTEGER DEFAULT 0,
                synced INTEGER DEFAULT 0,
                UNIQUE(date_str, lecture, student_id)
            )
            """)

            # Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                is_spoof INTEGER DEFAULT 0,
                student_id INTEGER,
                student_name TEXT,
                mood TEXT,
                mood_scores_json TEXT,
                liveness_json TEXT,
                confidence TEXT,
                description TEXT,
                snapshot_path TEXT,
                synced INTEGER DEFAULT 0
            )
            """)

            # Settings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            conn.commit()

    # ──────────────── Students ────────────────

    def get_all_students(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students ORDER BY name ASC")
            rows = cursor.fetchall()
            students = []
            for r in rows:
                s = dict(r)
                if s.get("embedding"):
                    s["embedding"] = np.frombuffer(s["embedding"], dtype=np.float32)
                students.append(s)
            return students

    def get_student_by_id(self, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            r = cursor.fetchone()
            if not r:
                return None
            s = dict(r)
            if s.get("embedding"):
                s["embedding"] = np.frombuffer(s["embedding"], dtype=np.float32)
            return s

    def add_or_update_student(self, student_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            embedding_bytes = None
            if "embedding" in student_data and student_data["embedding"] is not None:
                if isinstance(student_data["embedding"], np.ndarray):
                    embedding_bytes = student_data["embedding"].astype(np.float32).tobytes()
                elif isinstance(student_data["embedding"], bytes):
                    embedding_bytes = student_data["embedding"]

            cursor.execute("""
            INSERT INTO students (
                id, name, roll_no, avatar_initials, color, enrolled,
                present_count, total_count, streak, face_photo_path, embedding, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                roll_no=excluded.roll_no,
                avatar_initials=excluded.avatar_initials,
                color=excluded.color,
                enrolled=excluded.enrolled,
                present_count=excluded.present_count,
                total_count=excluded.total_count,
                streak=excluded.streak,
                face_photo_path=excluded.face_photo_path,
                embedding=coalesce(excluded.embedding, students.embedding)
            """, (
                student_data.get("id", int(time.time() * 1000)),
                student_data["name"],
                student_data.get("roll_no", ""),
                student_data.get("avatar_initials", student_data["name"][:2].upper()),
                student_data.get("color", PALETTE_AVATAR[0]),
                student_data.get("enrolled", 1),
                student_data.get("present_count", 0),
                student_data.get("total_count", 0),
                student_data.get("streak", 0),
                student_data.get("face_photo_path", ""),
                embedding_bytes,
                student_data.get("created_at", datetime.now().isoformat())
            ))
            conn.commit()

    def delete_student(self, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
            conn.commit()

    # ──────────────── Attendance ────────────────

    def mark_attendance(self, date_str, lecture, student_id, status='present', mood='neutral', liveness_score=100.0, confidence='high', manual=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_time = datetime.now().strftime("%I:%M:%S %p")
            cursor.execute("""
            INSERT INTO attendance (
                date_str, lecture, student_id, status, time_str, mood, liveness_score, confidence, manual
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date_str, lecture, student_id) DO UPDATE SET
                status=excluded.status,
                time_str=excluded.time_str,
                mood=excluded.mood,
                liveness_score=excluded.liveness_score,
                confidence=excluded.confidence,
                manual=excluded.manual
            """, (date_str, lecture, student_id, status, now_time, mood, liveness_score, confidence, manual))

            # Update student counters if marking present
            if status == 'present':
                cursor.execute("""
                UPDATE students
                SET present_count = present_count + 1,
                    total_count = total_count + 1,
                    streak = streak + 1
                WHERE id = ?
                """, (student_id,))
            conn.commit()

    def unmark_attendance(self, date_str, lecture, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM attendance WHERE date_str = ? AND lecture = ? AND student_id = ?", (date_str, lecture, student_id))
            row = cursor.fetchone()
            if row and row["status"] == "present":
                cursor.execute("""
                UPDATE students
                SET present_count = max(0, present_count - 1),
                    total_count = max(0, total_count - 1),
                    streak = max(0, streak - 1)
                WHERE id = ?
                """, (student_id,))
            cursor.execute("DELETE FROM attendance WHERE date_str = ? AND lecture = ? AND student_id = ?", (date_str, lecture, student_id))
            conn.commit()

    def get_attendance_for_lecture(self, date_str, lecture):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT a.*, s.name, s.avatar_initials, s.color, s.streak
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date_str = ? AND a.lecture = ?
            ORDER BY a.time_str DESC
            """, (date_str, lecture))
            return [dict(r) for r in cursor.fetchall()]

    def get_attendance_history_all(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance ORDER BY date_str DESC, time_str DESC")
            return [dict(r) for r in cursor.fetchall()]

    # ──────────────── Logs ────────────────

    def add_log(self, is_spoof, student_id, student_name, mood, mood_scores, liveness_dict, confidence, description, snapshot_path):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO logs (
                timestamp, is_spoof, student_id, student_name, mood,
                mood_scores_json, liveness_json, confidence, description, snapshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                1 if is_spoof else 0,
                student_id,
                student_name,
                mood,
                json.dumps(mood_scores or {}),
                json.dumps(liveness_dict or {}),
                confidence,
                description,
                snapshot_path
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_logs(self, limit=100):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                item = dict(r)
                item["mood_scores"] = json.loads(item["mood_scores_json"] or "{}")
                item["liveness"] = json.loads(item["liveness_json"] or "{}")
                logs.append(item)
            return logs

    # ──────────────── Settings ────────────────

    def get_setting(self, key, default=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    # ──────────────── Demo Seeder ────────────────

    def seed_demo_roster(self):
        demo_students = [
            {"name": "Aarav Sharma", "roll": "CS-101", "present": 28, "total": 30, "streak": 9, "color": PALETTE_AVATAR[0]},
            {"name": "Priya Patel", "roll": "CS-102", "present": 29, "total": 30, "streak": 14, "color": PALETTE_AVATAR[1]},
            {"name": "Rohan Mehta", "roll": "CS-103", "present": 24, "total": 30, "streak": 3, "color": PALETTE_AVATAR[2]},
            {"name": "Ananya Iyer", "roll": "CS-104", "present": 27, "total": 30, "streak": 7, "color": PALETTE_AVATAR[3]},
            {"name": "Vikram Singh", "roll": "CS-105", "present": 20, "total": 30, "streak": 0, "color": PALETTE_AVATAR[4]},
            {"name": "Neha Desai", "roll": "CS-106", "present": 26, "total": 30, "streak": 5, "color": PALETTE_AVATAR[5]},
        ]

        base_id = 1001
        created_ids = []
        for idx, d in enumerate(demo_students):
            stu_id = base_id + idx
            created_ids.append(stu_id)
            initials = "".join([w[0] for w in d["name"].split()[:2]]).upper()

            # Generate synthetic face embedding for recognition
            np.random.seed(stu_id)
            synthetic_embedding = np.random.randn(128).astype(np.float32)
            synthetic_embedding /= np.linalg.norm(synthetic_embedding)

            self.add_or_update_student({
                "id": stu_id,
                "name": d["name"],
                "roll_no": d["roll"],
                "avatar_initials": initials,
                "color": d["color"],
                "enrolled": 1,
                "present_count": d["present"],
                "total_count": d["total"],
                "streak": d["streak"],
                "embedding": synthetic_embedding,
                "face_photo_path": ""
            })

        # Seed past 5 days of attendance across default lectures
        today = datetime.now()
        mood_samples = ["focused", "happy", "focused", "neutral", "excited"]

        for offset in range(1, 6):
            dt = today - timedelta(days=offset)
            date_str = dt.strftime("%Y-%m-%d")
            for lec in DEFAULT_LECTURES:
                for idx, stu_id in enumerate(created_ids):
                    # 85% attendance
                    if (idx + offset) % 5 != 0:
                        mood = mood_samples[(idx + offset) % len(mood_samples)]
                        self.mark_attendance(
                            date_str=date_str,
                            lecture=lec,
                            student_id=stu_id,
                            status="present",
                            mood=mood,
                            liveness_score=round(82.0 + (idx % 12), 1),
                            confidence="high",
                            manual=0
                        )

        # Seed 2 spoof logs for demonstration
        self.add_log(
            is_spoof=True,
            student_id=None,
            student_name="Unknown / Photo Spoof",
            mood=None,
            mood_scores={},
            liveness_dict={"blink": 0, "motion": 8, "depth": 14, "overall": 7, "live": False},
            confidence="low",
            description="Anti-Proxy Triggered: Static photo detected, 0 blinks registered.",
            snapshot_path=""
        )

        return len(demo_students)
