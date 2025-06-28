import os
import cv2
from ultralytics import YOLO
from datetime import datetime
from helpers.logger import log_mobile_usage
from helpers.pause_manager import is_paused

# Load the YOLO model
model = YOLO("yolov8s.pt")  # Make sure this file is in your root folder

def generate_frames(source, camera_name):
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera: {source}")
        return

    while True:
        if is_paused():
            continue  # Skip detection if paused

        success, frame = cap.read()
        if not success:
            break

        # YOLO Detection
        results = model(frame)

        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == 'cell phone':
                    # Save screenshot
                    save_screenshot(frame, camera_name)
                    # Log detection
                    log_mobile_usage(camera_name)

        # Show detections
        frame = results[0].plot()

        # Convert for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield for browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


def save_screenshot(frame, camera_name="classroom"):
    folder = 'static/screenshots'
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{folder}/{camera_name}_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"[INFO] Screenshot saved: {filename}")
