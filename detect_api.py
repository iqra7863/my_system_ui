import cv2
import os
import requests
from datetime import datetime
from ultralytics import YOLO

# 💡 Replace this with your actual dashboard URL
UPLOAD_URL = "https://your-render-app-name.onrender.com/upload"

# Camera source (0 = built-in webcam, or use IP stream URL)
CAMERA_SOURCE = 0
CAMERA_NAME = "Lab_PC_1"

# Load model (you can also use a path to your custom model)
model = YOLO("yolov8s.pt")

def detect_and_upload():
    cap = cv2.VideoCapture(CAMERA_SOURCE)

    if not cap.isOpened():
        print("[ERROR] Camera could not be opened.")
        return

    print("[INFO] Detection started... Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == 'cell phone':
                    print("[ALERT] Mobile phone detected!")
                    send_screenshot(frame)
                    break  # avoid sending multiple times per frame

        # Show frame locally (optional)
        cv2.imshow("Live Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def send_screenshot(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{CAMERA_NAME}_{timestamp}.jpg"
    filepath = os.path.join("screenshots", filename)

    os.makedirs("screenshots", exist_ok=True)
    cv2.imwrite(filepath, frame)

    # Send via POST request
    try:
        with open(filepath, 'rb') as f:
            response = requests.post(UPLOAD_URL, files={'screenshot': f}, data={'camera_name': CAMERA_NAME})
        if response.status_code == 200:
            print(f"[UPLOAD] Screenshot sent successfully: {filename}")
        else:
            print(f"[ERROR] Upload failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send screenshot: {e}")


if __name__ == "__main__":
    detect_and_upload()
