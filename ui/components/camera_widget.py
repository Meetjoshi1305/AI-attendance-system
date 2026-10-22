import time
import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QImage, QPainterPath
from PyQt6.QtCore import Qt, QRect, QRectF, QTimer, pyqtSignal
from config import COLORS

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 360)

        self.current_frame = None
        self.detected_faces = []
        self.hud_mode = "idle"  # "idle", "live", "scanning", "success", "spoof"
        self.status_text = ""
        self.status_subtext = ""
        self.scan_beam_y = 0
        self.scan_direction = 1

        # Timer for scanning beam animation
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(30)

    def set_frame(self, frame_bgr):
        self.current_frame = frame_bgr
        self.update()

    def set_detected_faces(self, faces):
        self.detected_faces = faces
        self.update()

    def set_hud_mode(self, mode, text="", subtext=""):
        self.hud_mode = mode
        self.status_text = text
        self.status_subtext = subtext
        self.update()

    def clear(self):
        self.current_frame = None
        self.detected_faces = []
        self.hud_mode = "idle"
        self.status_text = ""
        self.status_subtext = ""
        self.update()

    def _update_animation(self):
        if self.hud_mode == "scanning":
            self.scan_beam_y += 6 * self.scan_direction
            if self.scan_beam_y > self.height():
                self.scan_beam_y = 0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 1. Background
        painter.fillRect(0, 0, w, h, QColor(COLORS["bg"]))

        # 2. Draw Video Frame if available
        if self.current_frame is not None:
            fh, fw = self.current_frame.shape[:2]
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = 3 * fw
            qimg = QImage(rgb_frame.data, fw, fh, bytes_per_line, QImage.Format.Format_RGB888)

            # Fit proportionally
            scale = min(w / fw, h / fh)
            dw, dh = int(fw * scale), int(fh * scale)
            dx, dy = (w - dw) // 2, (h - dh) // 2

            painter.drawImage(QRect(dx, dy, dw, dh), qimg)

            # Draw HUD Overlays on top of frame
            self._draw_hud(painter, dx, dy, dw, dh, fw, fh)
        else:
            self._draw_idle_screen(painter, w, h)

    def _draw_idle_screen(self, painter, w, h):
        # Grid lines background
        painter.setPen(QPen(QColor(COLORS["border"]), 1, Qt.PenStyle.DotLine))
        for x in range(0, w, 40):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 40):
            painter.drawLine(0, y, w, y)

        # Idle Icon & Text
        painter.setPen(QColor(COLORS["muted"]))
        font = QFont("Segoe UI", 42)
        painter.setFont(font)
        painter.drawText(QRectF(0, h * 0.3, w, 60), Qt.AlignmentFlag.AlignCenter, "📷")

        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(COLORS["dim"]))
        painter.drawText(QRectF(0, h * 0.48, w, 30), Qt.AlignmentFlag.AlignCenter, "Camera Offline")

        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(QRectF(0, h * 0.55, w, 30), Qt.AlignmentFlag.AlignCenter, "Click 'Start Camera' to initiate attendance scanning")

    def _draw_hud(self, painter, dx, dy, dw, dh, fw, fh):
        scale_x = dw / fw
        scale_y = dh / fh

        # Determine HUD theme color
        if self.hud_mode == "success":
            hud_color = QColor(COLORS["green"])
        elif self.hud_mode == "spoof":
            hud_color = QColor(COLORS["red"])
        elif self.hud_mode == "scanning":
            hud_color = QColor(COLORS["cyan"])
        else:
            hud_color = QColor(COLORS["cyan"])

        # 1. Four Sci-Fi Corner Brackets
        pen = QPen(hud_color, 3)
        painter.setPen(pen)
        margin = 16
        c_len = 28

        # Top-Left
        painter.drawLine(dx + margin, dy + margin, dx + margin + c_len, dy + margin)
        painter.drawLine(dx + margin, dy + margin, dx + margin, dy + margin + c_len)

        # Top-Right
        painter.drawLine(dx + dw - margin, dy + margin, dx + dw - margin - c_len, dy + margin)
        painter.drawLine(dx + dw - margin, dy + margin, dx + dw - margin, dy + margin + c_len)

        # Bottom-Left
        painter.drawLine(dx + margin, dy + dh - margin, dx + margin + c_len, dy + dh - margin)
        painter.drawLine(dx + margin, dy + dh - margin, dx + margin, dy + dh - margin - c_len)

        # Bottom-Right
        painter.drawLine(dx + dw - margin, dy + dh - margin, dx + dw - margin - c_len, dy + dh - margin)
        painter.drawLine(dx + dw - margin, dy + dh - margin, dx + dw - margin, dy + dh - margin - c_len)

        # 2. Scanning Laser Beam
        if self.hud_mode == "scanning":
            beam_pen = QPen(QColor(0, 229, 255, 200), 2)
            painter.setPen(beam_pen)
            sy = dy + (self.scan_beam_y % dh)
            painter.drawLine(dx + margin, sy, dx + dw - margin, sy)

            glow_brush = QColor(0, 229, 255, 30)
            painter.fillRect(dx + margin, max(dy, sy - 8), dw - 2 * margin, 16, glow_brush)

        # 3. Detected Faces Bounding Box & Landmarks
        for face in self.detected_faces:
            bx, by, bw_box, bh_box = face["box"]
            rx = int(dx + bx * scale_x)
            ry = int(dy + by * scale_y)
            rw = int(bw_box * scale_x)
            rh = int(bh_box * scale_y)

            # Face Box
            painter.setPen(QPen(hud_color, 2, Qt.PenStyle.SolidLine))
            painter.setBrush(QBrush(QColor(hud_color.red(), hud_color.green(), hud_color.blue(), 18)))
            painter.drawRoundedRect(rx, ry, rw, rh, 10, 10)

            # Landmarks (Eyes, Nose, Mouth)
            painter.setBrush(QBrush(hud_color))
            painter.setPen(Qt.PenStyle.NoPen)
            for lx, ly in face.get("landmarks", []):
                plx = int(dx + lx * scale_x)
                ply = int(dy + ly * scale_y)
                painter.drawEllipse(plx - 3, ply - 3, 6, 6)

            # Tag Label on Face Frame
            tag_text = self.status_text or ("SCANNING" if self.hud_mode == "scanning" else "FACE DETECTED")
            painter.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            painter.setBrush(QBrush(QColor(4, 8, 15, 230)))
            painter.setPen(QPen(hud_color, 1))

            metrics = painter.fontMetrics()
            t_w = metrics.horizontalAdvance(tag_text) + 16
            t_h = 24
            painter.drawRoundedRect(rx, max(dy + 5, ry - t_h - 4), t_w, t_h, 5, 5)

            painter.setPen(hud_color)
            painter.drawText(rx + 8, max(dy + 5, ry - t_h - 4) + 16, tag_text)

        # 4. Bottom Status Pill Banner
        if self.status_text and not self.detected_faces:
            banner_rect = QRect(dx + 30, dy + dh - 56, dw - 60, 40)
            painter.setBrush(QBrush(QColor(4, 8, 15, 220)))
            painter.setPen(QPen(hud_color, 1))
            painter.drawRoundedRect(banner_rect, 20, 20)

            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            painter.setPen(hud_color)
            painter.drawText(banner_rect, Qt.AlignmentFlag.AlignCenter, self.status_text)
