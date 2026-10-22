import os
import requests

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILES = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "haarcascade_frontalface_default.xml": "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
    "haarcascade_eye.xml": "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml"
}

def ensure_models():
    """Ensure all required OpenCV Zoo deep learning and Haar cascade models are present."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    for filename, url in MODEL_FILES.items():
        dest = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
            print(f"Downloading {filename}...")
            try:
                r = requests.get(url, allow_redirects=True, timeout=60)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    print(f"Successfully downloaded {filename} ({os.path.getsize(dest)} bytes)")
                else:
                    print(f"Failed to download {filename}: HTTP {r.status_code}")
            except Exception as e:
                print(f"Warning: could not download {filename} from {url}: {e}")

if __name__ == "__main__":
    ensure_models()
