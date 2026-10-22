# FaceAttend PRO — Anti-Proxy AI Attendance Desktop Application

A production-grade Python desktop application built with **PyQt6**, **OpenCV**, **YuNet + SFace Deep Learning Biometrics**, and **Gemini Vision AI**. 

Engineered to eliminate buddy-punching, photo spoofing, and proxy attendance in schools, universities, and enterprise environments.

---

## 🌟 Key Features

### 1. 🛡 Multi-Factor Anti-Proxy Liveness Engine
- **EAR Blink Tracking**: Eye Aspect Ratio (EAR) temporal analysis ensures the subject is blinking naturally across real video frames.
- **Head Micro-Movement Tracking**: Tracks 3D nose coordinates and head tilt angle variance.
- **Laplacian Texture & Screen Depth Analysis**: Analyzes high-frequency texture gradient distributions to immediately identify and block static photos, phone displays, or tablet screen replays.
- **Instant Spoof Audit**: When a spoof attempt is detected, an audit snapshot is saved, corners flash red (`⛔ SPOOF DETECTED`), and a security record is registered in the database.

### 2. 🧠 Mood AI & Engagement Detection
- Powered by **Google Gemini Vision API** with automatic fallback to a local computer vision facial expression heuristic.
- Classifies 8 emotional states: `Happy`, `Focused`, `Neutral`, `Tired`, `Stressed`, `Sad`, `Confused`, `Excited`.
- Provides breakdown confidence percentages and diagnostic insights.

### 3. 👥 Biometric Face Roster & Enrollment
- **Deep Face Recognition**: Leverages OpenCV Zoo **YuNet** (detection) and **SFace** (128-dimensional biometric cosine embeddings).
- **Fast Enrollment**: Capture live webcam faces or generate synthetic biometric templates with one click.
- **Student Cards**: View streaks, attendance percentage bars, historical presence, and delete records with confirmation.
- **⚡ 1-Click Demo Roster**: Seeds 6 realistic students with 5 days of multi-lecture history for immediate out-of-the-box evaluation.

### 4. 📅 Attendance Register & Lecture Management
- **Multi-Lecture Support**: Manage separate lectures (`IoT`, `DM`, `Comp`, `DBMS`).
- **Date Navigation**: Previous/Next day shifts, date picker calendar popup, and quick "Today" jump.
- **Manual Overrides**: "✏ Mark Present" and "✕ Undo" for teacher exceptions.
- **1-Click CSV Export**: Download lecture attendance spreadsheets ready for administrative archiving.

### 5. 📈 Predictive Attendance Forecasting
- Statistical and AI trend analysis predicting next week's attendance rate based on current streak, past consistency, and risk categorization (`Good Standing`, `Moderate`, `High Risk`).

### 6. 📊 Intelligence & Security Analytics
- Embedded dark-mode Matplotlib charts:
  - Weekly attendance trends
  - Student engagement doughnut segmentation
  - Real-time mood distribution cards
  - Anti-proxy prevented spoof trajectory

### 7. ☁️ Cloud Database Sync & Offline SQLite Cache
- **Offline-First Architecture**: Uses local SQLite (`data/faceattend.db`) so attendance never fails even if offline.
- **Cloud Sync**: Background sync worker for **Firebase Firestore** and **Supabase** via REST APIs.

---

## 🚀 Quick Start

### 1. Run the Application
Double-click `run.bat` or run:
```bash
python app.py
```

### 2. Dependencies
If setting up on a new machine:
```bash
pip install -r requirements.txt
```

---

## 📂 Project Architecture

```
faceattend/
├── app.py                      # Application bootstrap & entry point
├── config.py                   # Constants, colors, paths, thresholds
├── requirements.txt            # Python dependencies
├── run.bat                     # Windows quick launcher
├── README.md                   # Documentation
├── database/
│   ├── __init__.py
│   ├── local_db.py             # SQLite persistence, queries, demo data seeder
│   └── cloud_sync.py           # Background sync worker for Firebase / Supabase
├── vision/
│   ├── __init__.py
│   ├── camera_thread.py        # QThread OpenCV webcam capture
│   ├── face_engine.py          # YuNet detector & SFace 128D recognizer
│   ├── liveness_detector.py    # Multi-factor Anti-Proxy (EAR, motion, Laplacian)
│   └── mood_ai.py              # Gemini Vision API + local expression classifier
├── ui/
│   ├── __init__.py
│   ├── theme.py                # Cyberpunk dark QSS stylesheet
│   ├── main_window.py          # Header, navigation, ticker, tab coordinator
│   ├── components/
│   │   ├── __init__.py
│   │   ├── camera_widget.py    # Custom HUD camera widget with corner brackets & laser beam
│   │   ├── stat_card.py        # Metric counters
│   │   └── student_card.py     # Student roster card with progress bars
│   └── tabs/
│       ├── __init__.py
│       ├── scan_tab.py         # Tab 1: Live HUD camera scan & liveness telemetry
│       ├── students_tab.py     # Tab 2: Enrolled student cards & webcam enrollment
│       ├── logs_tab.py         # Tab 3: Audit log table & snapshot inspection
│       ├── register_tab.py     # Tab 4: Lecture register, manual mark/undo, CSV export
│       ├── analytics_tab.py    # Tab 5: Embedded visual charts & mood statistics
│       └── settings_dialog.py  # Modal for Gemini key, Firebase / Supabase setup
├── models/
│   ├── download_models.py      # Automated model downloader
│   ├── face_detection_yunet_2023mar.onnx
│   ├── face_recognition_sface_2021dec.onnx
│   ├── haarcascade_frontalface_default.xml
│   └── haarcascade_eye.xml
└── data/
    ├── faceattend.db           # SQLite database
    └── snapshots/              # Audit event and enrollment images
```

---

## ⚙️ Configuration & API Keys

Click the **⚙️ Settings** button in the top navigation bar to configure:
1. **Google Gemini API Key**: Enables Gemini 2.5 Flash Vision for advanced multimodal student expression analysis.
2. **Cloud Database Provider**:
   - Choose **Firebase Firestore** (Enter Project ID)
   - Choose **Supabase** (Enter URL and API Key)
3. **Camera Device**: Select between integrated webcam (Camera 0) or external USB cameras (Camera 1/2).
