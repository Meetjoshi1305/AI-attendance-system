import sys
import os

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from config import APP_NAME
from models.download_models import ensure_models
from database.local_db import LocalDatabase
from database.cloud_sync import CloudSyncWorker
from vision.face_engine import FaceEngine
from vision.liveness_detector import LivenessDetector
from vision.mood_ai import MoodAI
from vision.camera_thread import CameraThread
from ui.theme import get_cyberpunk_stylesheet
from ui.main_window import MainWindow

def main():
    print(f"Starting {APP_NAME}...")

    # Ensure required deep learning models are in place
    ensure_models()

    # High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(get_cyberpunk_stylesheet())

    # Initialize subsystems
    db = LocalDatabase()

    # Auto-seed demo roster if database is fresh so user can test immediately
    students = db.get_all_students()
    if not students:
        print("Fresh database detected — seeding demo classroom roster...")
        db.seed_demo_roster()

    face_engine = FaceEngine()
    liveness_detector = LivenessDetector()

    gemini_key = db.get_setting("gemini_api_key", "")
    mood_ai = MoodAI(api_key=gemini_key)

    camera_index = int(db.get_setting("camera_index", "0"))
    camera_thread = CameraThread(camera_index=camera_index)

    cloud_sync = CloudSyncWorker(db)

    # Launch Main Window
    window = MainWindow(
        db=db,
        face_engine=face_engine,
        liveness_detector=liveness_detector,
        mood_ai=mood_ai,
        camera_thread=camera_thread,
        cloud_sync=cloud_sync
    )
    window.show()

    print(f"{APP_NAME} is running.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
