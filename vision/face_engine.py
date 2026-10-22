import os
import cv2
import numpy as np
from config import YUNET_MODEL_PATH, SFACE_MODEL_PATH, HAAR_FACE_PATH, HAAR_EYE_PATH

class FaceEngine:
    def __init__(self):
        self.yunet_detector = None
        self.sface_recognizer = None
        self.haar_face_cascade = None
        self.haar_eye_cascade = None
        self.last_det_size = (640, 480)
        self._init_models()

    def _init_models(self):
        # 1. Initialize YuNet
        if os.path.exists(YUNET_MODEL_PATH) and os.path.getsize(YUNET_MODEL_PATH) > 10000:
            try:
                self.yunet_detector = cv2.FaceDetectorYN.create(
                    model=YUNET_MODEL_PATH,
                    config="",
                    input_size=self.last_det_size,
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5000
                )
            except Exception as e:
                print(f"YuNet init failed: {e}")
                self.yunet_detector = None

        # 2. Initialize SFace Recognizer
        if os.path.exists(SFACE_MODEL_PATH) and os.path.getsize(SFACE_MODEL_PATH) > 100000:
            try:
                self.sface_recognizer = cv2.FaceRecognizerSF.create(
                    model=SFACE_MODEL_PATH,
                    config=""
                )
            except Exception as e:
                print(f"SFace init failed: {e}")
                self.sface_recognizer = None

        # 3. Haar Cascade fallbacks
        if os.path.exists(HAAR_FACE_PATH):
            self.haar_face_cascade = cv2.CascadeClassifier(HAAR_FACE_PATH)
        if os.path.exists(HAAR_EYE_PATH):
            self.haar_eye_cascade = cv2.CascadeClassifier(HAAR_EYE_PATH)

    def detect_faces(self, frame):
        """
        Detects faces in frame.
        Returns list of dicts:
        [{
            'box': (x, y, w, h),
            'confidence': float,
            'landmarks': [(x,y), ...], # 5 landmarks: right_eye, left_eye, nose, right_mouth, left_mouth
            'raw_yunet_face': np.ndarray
        }]
        """
        h, w = frame.shape[:2]
        results = []

        if self.yunet_detector is not None:
            if self.last_det_size != (w, h):
                self.yunet_detector.setInputSize((w, h))
                self.last_det_size = (w, h)

            _, faces = self.yunet_detector.detect(frame)
            if faces is not None:
                for face in faces:
                    box = [int(v) for v in face[0:4]]
                    # Clamp box to image bounds
                    bx, by, bw, bh = box
                    bx = max(0, bx)
                    by = max(0, by)
                    bw = min(w - bx, bw)
                    bh = min(h - by, bh)
                    box = (bx, by, bw, bh)

                    landmarks = []
                    for i in range(5):
                        lx = int(face[4 + 2 * i])
                        ly = int(face[4 + 2 * i + 1])
                        landmarks.append((lx, ly))

                    score = float(face[-1])
                    results.append({
                        "box": box,
                        "confidence": score,
                        "landmarks": landmarks,
                        "raw_yunet_face": face
                    })
                return results

        # Fallback to Haar Cascade
        if self.haar_face_cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.haar_face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            for (x, y, bw, bh) in faces:
                # Approximate 5 landmarks based on face geometry
                re = (int(x + bw * 0.3), int(y + bh * 0.35))
                le = (int(x + bw * 0.7), int(y + bh * 0.35))
                no = (int(x + bw * 0.5), int(y + bh * 0.55))
                rm = (int(x + bw * 0.35), int(y + bh * 0.75))
                lm = (int(x + bw * 0.65), int(y + bh * 0.75))

                synthetic_raw = np.array([x, y, bw, bh, re[0], re[1], le[0], le[1], no[0], no[1], rm[0], rm[1], lm[0], lm[1], 0.85], dtype=np.float32)
                results.append({
                    "box": (x, y, bw, bh),
                    "confidence": 0.85,
                    "landmarks": [re, le, no, rm, lm],
                    "raw_yunet_face": synthetic_raw
                })

        return results

    def extract_features(self, frame, detection):
        """Extract 128D embedding vector using SFace recognizer."""
        if self.sface_recognizer is None or "raw_yunet_face" not in detection:
            return None

        try:
            raw_face = detection["raw_yunet_face"]
            aligned_face = self.sface_recognizer.alignCrop(frame, raw_face)
            feature = self.sface_recognizer.feature(aligned_face)
            # Flatten to 1D float32
            feature = feature.flatten().astype(np.float32)
            # Normalize
            norm = np.linalg.norm(feature)
            if norm > 0:
                feature /= norm
            return feature
        except Exception as e:
            print(f"Feature extraction failed: {e}")
            return None

    def match_student(self, embedding, enrolled_students, threshold=0.36):
        """
        Compare embedding against enrolled students with cosine similarity.
        SFace cosine distance: threshold ~0.363 for 1:1 verification.
        Returns: (matched_student_dict, similarity_score, confidence_str)
        """
        if embedding is None or not enrolled_students:
            return None, 0.0, "low"

        best_student = None
        best_score = -1.0

        for student in enrolled_students:
            s_emb = student.get("embedding")
            if s_emb is None:
                continue

            # Cosine similarity
            dot = np.dot(embedding, s_emb)
            score = float(dot)

            if score > best_score:
                best_score = score
                best_student = student

        if best_student and best_score >= threshold:
            confidence = "high" if best_score >= 0.55 else "medium"
            return best_student, best_score, confidence

        return None, best_score, "low"
