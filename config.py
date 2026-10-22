import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Database
DB_PATH = os.path.join(DATA_DIR, "faceattend.db")

# Models
YUNET_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")
HAAR_FACE_PATH = os.path.join(MODELS_DIR, "haarcascade_frontalface_default.xml")
HAAR_EYE_PATH = os.path.join(MODELS_DIR, "haarcascade_eye.xml")

# App Metadata
APP_NAME = "FaceAttend PRO"
APP_SUBTITLE = "ANTI-PROXY · MOOD AI · PREDICTION"
APP_VERSION = "2.0.0 Pro"

# Color Palette (Dark Cyberpunk Theme)
COLORS = {
    "bg": "#04080f",
    "surface": "#080e1a",
    "card": "#0c1524",
    "card2": "#101c2e",
    "border": "#152030",
    "border2": "#1a2d45",
    "cyan": "#00e5ff",
    "green": "#00ff88",
    "amber": "#ffb800",
    "red": "#ff3d5a",
    "purple": "#b066ff",
    "pink": "#ff4db8",
    "blue": "#4d8cff",
    "text": "#dde8f5",
    "muted": "#3d5570",
    "dim": "#7a9abf"
}

PALETTE_AVATAR = [
    '#00e5ff', '#b066ff', '#ff4db8', '#00ff88',
    '#ff8c00', '#ffb800', '#4d8cff', '#ff3d5a'
]

MOOD_MAP = {
    "happy":    {"e": "😄", "c": "#00ff88", "desc": "Positive & engaged"},
    "focused":  {"e": "🎯", "c": "#00e5ff", "desc": "Attentive & ready to learn"},
    "neutral":  {"e": "😐", "c": "#7a9abf", "desc": "Calm and composed"},
    "tired":    {"e": "😴", "c": "#b066ff", "desc": "May need a break"},
    "stressed": {"e": "😰", "c": "#ffb800", "desc": "Appears anxious or stressed"},
    "sad":      {"e": "😢", "c": "#4d8cff", "desc": "Seems down or unmotivated"},
    "confused": {"e": "😕", "c": "#ff8c00", "desc": "May need extra guidance"},
    "excited":  {"e": "🤩", "c": "#ff4db8", "desc": "High energy & enthusiastic"}
}

DEFAULT_LECTURES = ["IoT", "DM", "Comp", "DBMS"]

# Anti-Proxy Liveness Thresholds
LIVENESS_CONFIG = {
    "sample_duration_sec": 3.5,
    "blink_ear_threshold": 0.21,
    "blink_open_threshold": 0.28,
    "min_blinks": 1,
    "min_motion_spread": 0.015,
    "min_texture_variance": 18.0,
    "pass_score": 50.0
}
