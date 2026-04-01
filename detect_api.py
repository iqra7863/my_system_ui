# detect_api.py
from flask import Flask, request
import os
from datetime import datetime
import cv2

app = Flask(__name__)
SCREENSHOT_FOLDER = 'screenshots'
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

@app.route('/detect', methods=['POST'])
def detect():
    ip = request.form.get('ip')
    classroom = request.form.get('classroom')

    cap = cv2.VideoCapture(ip)
    ret, frame = cap.read()
    if not ret:
        return 'Camera feed failed', 400

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{classroom}_{timestamp}.jpg"
    filepath = os.path.join(SCREENSHOT_FOLDER, filename)
    cv2.imwrite(filepath, frame)
    cap.release()

    print(f"[✔] Saved {filename}")
    return "Detection success", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
