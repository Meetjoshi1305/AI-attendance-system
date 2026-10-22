import time
import cv2
import numpy as np
from config import LIVENESS_CONFIG

class LivenessDetector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = None
        self.is_active = False
        self.blink_count = 0
        self.blink_in_progress = False
        self.last_ear = None
        self.head_positions = []
        self.texture_scores = []
        self.face_sizes = []
        self.frame_count = 0

    def start(self):
        self.reset()
        self.start_time = time.time()
        self.is_active = True

    def stop(self):
        self.is_active = False

    def process_frame(self, frame, detection):
        """
        Process a single video frame during liveness checking.
        detection: dict from FaceEngine.detect_faces()
        """
        if not self.is_active or detection is None:
            return None

        h, w = frame.shape[:2]
        now = time.time()
        self.frame_count += 1

        box = detection.get("box", (0, 0, w, h))
        bx, by, bw, bh = box
        landmarks = detection.get("landmarks", [])

        # 1. Blink Detection using Eye Region / Landmarks
        ear = 0.30
        if len(landmarks) >= 5:
            # 5 landmarks: right_eye, left_eye, nose, right_mouth, left_mouth
            re = landmarks[0]
            le = landmarks[1]
            nose = landmarks[2]

            # Track nose position for motion analysis
            nx = nose[0] / max(1, w)
            ny = nose[1] / max(1, h)
            self.head_positions.append((nx, ny, now))

            # Crop eye regions to calculate eye openness using thresholding/contours
            eye_dist = np.hypot(le[0] - re[0], le[1] - re[1])
            eye_radius = max(8, int(eye_dist * 0.22))

            ears = []
            for ep in [re, le]:
                ex, ey = ep
                x1, y1 = max(0, ex - eye_radius), max(0, ey - eye_radius)
                x2, y2 = min(w, ex + eye_radius), min(h, ey + eye_radius)
                eye_roi = frame[y1:y2, x1:x2]
                if eye_roi.size > 0:
                    gray_eye = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
                    # Contrast normalization
                    gray_eye = cv2.equalizeHist(gray_eye)
                    # Vertical gradient vs Horizontal gradient
                    sobel_y = cv2.Sobel(gray_eye, cv2.CV_64F, 0, 1, ksize=3)
                    sobel_x = cv2.Sobel(gray_eye, cv2.CV_64F, 1, 0, ksize=3)
                    vert_energy = np.mean(np.abs(sobel_y))
                    horiz_energy = np.mean(np.abs(sobel_x)) + 1e-4
                    ratio = vert_energy / horiz_energy
                    ears.append(ratio)

            if ears:
                ear = np.mean(ears)

        # Blink state machine
        blink_threshold = LIVENESS_CONFIG["blink_ear_threshold"]
        open_threshold = LIVENESS_CONFIG["blink_open_threshold"]

        if ear < blink_threshold and not self.blink_in_progress:
            self.blink_in_progress = True
        elif ear > open_threshold and self.blink_in_progress:
            self.blink_count += 1
            self.blink_in_progress = False

        self.last_ear = ear

        # 2. Depth / Texture via Laplacian Variance on Face Region
        face_roi = frame[by:by+bh, bx:bx+bw]
        if face_roi.size > 100:
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            # Resize to standardized 100x100 for consistent Laplacian evaluation
            small_face = cv2.resize(gray_face, (100, 100))
            lap_var = cv2.Laplacian(small_face, cv2.CV_64F).var()
            # Normalize score 0..100
            tex_score = min(100.0, lap_var * 0.8)
            self.texture_scores.append(tex_score)

        face_area_ratio = (bw * bh) / max(1, w * h)
        self.face_sizes.append(face_area_ratio)

        # Return instantaneous progress
        elapsed = now - (self.start_time or now)
        return self._compute_scores(elapsed)

    def _compute_scores(self, elapsed):
        # 1. Blink Score
        if self.blink_count == 0:
            blink_score = 15.0 if elapsed < 2.0 else 5.0
        elif self.blink_count == 1:
            blink_score = 75.0
        else:
            blink_score = min(100.0, 75.0 + (self.blink_count - 1) * 15.0)

        # 2. Head Motion Score
        if len(self.head_positions) >= 2:
            xs = [p[0] for p in self.head_positions]
            ys = [p[1] for p in self.head_positions]
            spread = max(max(xs) - min(xs), max(ys) - min(ys))
            motion_score = min(100.0, spread * 1400.0 + 10.0)
        else:
            motion_score = 10.0

        # 3. Depth & Texture Score
        avg_tex = np.mean(self.texture_scores) if self.texture_scores else 40.0
        depth_score = min(100.0, avg_tex * 0.7 + 15.0)

        # 4. Overall Weighted Score
        overall = int(round(0.40 * blink_score + 0.35 * motion_score + 0.25 * depth_score))

        # Pass condition
        passed = (blink_score >= 70.0 or motion_score >= 55.0) and depth_score >= 20.0 and overall >= LIVENESS_CONFIG["pass_score"]

        return {
            "blink": int(round(blink_score)),
            "motion": int(round(motion_score)),
            "depth": int(round(depth_score)),
            "overall": overall,
            "live": passed,
            "blink_count": self.blink_count,
            "elapsed": round(elapsed, 1)
        }

    def get_final_result(self):
        elapsed = time.time() - (self.start_time or time.time())
        res = self._compute_scores(elapsed)
        self.stop()

        if not res["live"]:
            if res["blink_count"] == 0 and res["motion"] < 30:
                res["reason"] = "Static photo or screen spoof detected (no blink or micro-movement)"
            elif res["depth"] < 25:
                res["reason"] = "Low depth texture / screen reflection detected"
            else:
                res["reason"] = "Insufficient biometric liveness signals"
        else:
            res["reason"] = "Biometric liveness confirmed (genuine live human)"

        return res
