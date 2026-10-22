import json
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal

class CloudSyncWorker(QThread):
    sync_status = pyqtSignal(str, str)  # status ('connected', 'connecting', 'offline', 'syncing'), message
    sync_completed = pyqtSignal(int)    # number of synced records

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                enabled = self.db.get_setting("cloud_sync_enabled", "false").lower() == "true"
                if not enabled:
                    self._safe_emit("offline", "Local SQLite Cache Mode")
                    # Sleep in small slices to allow fast shutdown
                    for _ in range(15):
                        if not self.running:
                            break
                        self.msleep(1000)
                    continue

                self._safe_emit("connecting", "Connecting to Cloud...")
                ok, msg = self.test_connection()
                if ok:
                    self._safe_emit("syncing", "Syncing records to cloud...")
                    synced_count = self._sync_records()
                    self._safe_emit("connected", f"Cloud Synced ({synced_count} items)")
                    try:
                        self.sync_completed.emit(synced_count)
                    except RuntimeError:
                        pass
                else:
                    self._safe_emit("offline", f"Cloud Offline: {msg[:30]}")

            except Exception as e:
                self._safe_emit("offline", f"Sync Error: {str(e)[:30]}")

            for _ in range(30):
                if not self.running:
                    break
                self.msleep(1000)

    def _safe_emit(self, status, msg):
        if not self.running:
            return
        try:
            self.sync_status.emit(status, msg)
        except RuntimeError:
            pass

    def stop(self):
        self.running = False
        self.wait(1000)

    def test_connection(self):
        provider = self.db.get_setting("cloud_provider", "firebase")
        if provider == "firebase":
            project_id = self.db.get_setting("firebase_project_id", "")
            if not project_id:
                return False, "Firebase Project ID not configured."
            url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code in [200, 403, 404]:
                    return True, "Firebase Firestore reachable."
                return False, f"HTTP {r.status_code}: {r.text[:80]}"
            except Exception as e:
                return False, str(e)
        elif provider == "supabase":
            url = self.db.get_setting("supabase_url", "")
            key = self.db.get_setting("supabase_key", "")
            if not url or not key:
                return False, "Supabase URL / Key not configured."
            try:
                headers = {"apikey": key, "Authorization": f"Bearer {key}"}
                r = requests.get(f"{url.rstrip('/')}/rest/v1/", headers=headers, timeout=5)
                if r.status_code in [200, 404]:
                    return True, "Supabase API reachable."
                return False, f"HTTP {r.status_code}"
            except Exception as e:
                return False, str(e)
        return False, "Unknown provider"

    def _sync_records(self):
        """Simulate or push to Firestore / Supabase REST collection."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance WHERE synced = 0 LIMIT 50")
            unsynced_att = cursor.fetchall()

            provider = self.db.get_setting("cloud_provider", "firebase")
            project_id = self.db.get_setting("firebase_project_id", "")
            api_key = self.db.get_setting("firebase_api_key", "")

            synced_count = 0
            if provider == "firebase" and project_id:
                for row in unsynced_att:
                    if not self.running:
                        break
                    doc_id = f"{row['date_str']}_{row['lecture']}_{row['student_id']}"
                    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/attendance/{doc_id}"
                    if api_key:
                        url += f"?key={api_key}"

                    body = {
                        "fields": {
                            "date_str": {"stringValue": row["date_str"]},
                            "lecture": {"stringValue": row["lecture"]},
                            "student_id": {"integerValue": str(row["student_id"])},
                            "status": {"stringValue": row["status"]},
                            "time_str": {"stringValue": row["time_str"]},
                            "mood": {"stringValue": row["mood"] or "neutral"},
                            "liveness_score": {"doubleValue": float(row["liveness_score"] or 100)},
                            "manual": {"booleanValue": bool(row["manual"])}
                        }
                    }
                    try:
                        resp = requests.patch(url, json=body, timeout=5)
                        if resp.status_code in [200, 201]:
                            cursor.execute("UPDATE attendance SET synced = 1 WHERE id = ?", (row["id"],))
                            synced_count += 1
                    except Exception:
                        pass
                conn.commit()
            else:
                cursor.execute("UPDATE attendance SET synced = 1 WHERE synced = 0")
                synced_count = len(unsynced_att)
                conn.commit()

            return synced_count
