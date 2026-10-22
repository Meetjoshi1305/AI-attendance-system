import time
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex

class CameraThread(QThread):
    frame_received = pyqtSignal(np.ndarray)
    camera_error = pyqtSignal(str)
    camera_started = pyqtSignal()
    camera_stopped = pyqtSignal()

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        self.mutex = QMutex()
        self.latest_frame = None

    def run(self):
        # On Windows, try cv2.CAP_DSHOW first for faster initialization
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            self.camera_error.emit(f"Could not open camera index {self.camera_index}. Check device connection.")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.running = True
        self.camera_started.emit()

        while self.running:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            # Mirror horizontally for natural webcam interaction
            frame = cv2.flip(frame, 1)

            self.mutex.lock()
            self.latest_frame = frame.copy()
            self.mutex.unlock()

            self.frame_received.emit(frame)
            time.sleep(0.025)  # ~40 FPS target

        if self.cap:
            self.cap.release()
            self.cap = None

        self.camera_stopped.emit()

    def stop(self):
        self.running = False
        self.wait(1500)

    def get_latest_frame(self):
        self.mutex.lock()
        frame = self.latest_frame.copy() if self.latest_frame is not None else None
        self.mutex.unlock()
        return frame

    def set_camera_index(self, index):
        was_running = self.running
        if was_running:
            self.stop()
        self.camera_index = index
        if was_running:
            self.start()
