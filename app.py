from ultralytics import YOLO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import os
import csv
import cv2
import requests
from datetime import datetime

from helpers.camera_manager import load_cameras, get_next_camera_id
from helpers.logger import get_logs, get_daily_report, log_mobile_usage
from helpers.pause_manager import set_pause, is_paused

app = Flask(__name__)
app.secret_key = 'iqra-detect-key'

# ---------------- YOLO MODEL ---------------- #
model = YOLO("yolov8s.pt")

# ---------------- CONFIG ---------------- #
CAMERA_FILE = 'camera_data.csv'
SCREENSHOT_FOLDER = 'static/screenshots'
RENDER_UPLOAD_URL = "https://my_system_ui.onrender.com/api/upload"  # CHANGE if needed

os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

# ---------------- CAMERA CACHE ---------------- #
camera_streams = {}

# ---------------- USERS ---------------- #
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'teacher': {'password': 'teacher123', 'role': 'teacher'},
    'viewer': {'password': 'viewer123', 'role': 'viewer'}
}

# ---------------- LOGIN ---------------- #
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        user = users.get(uname)
        if user and user['password'] == pwd:
            session['user'] = uname
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        return "Invalid Credentials"

    return render_template('login.html')


# ---------------- DASHBOARD ---------------- #
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    cameras = load_cameras(CAMERA_FILE)

    return render_template(
        'dashboard.html',
        cameras=cameras,
        user=session['user'],
        role=session['role'],
        is_paused=is_paused()
    )


# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- ADD CAMERA ---------------- #
@app.route('/add_cameras', methods=['GET', 'POST'])
def add_cameras():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']

        cam_id = get_next_camera_id(CAMERA_FILE)

        with open(CAMERA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if os.path.getsize(CAMERA_FILE) == 0:
                writer.writerow(['camera_id', 'camera_name', 'camera_url'])
            writer.writerow([cam_id, name, url])

        return redirect(url_for('dashboard'))

    return render_template('add_cameras.html')


# ---------------- REMOVE CAMERA ---------------- #
@app.route('/remove_camera/<int:camera_id>')
def remove_camera(camera_id):
    cameras = load_cameras(CAMERA_FILE)

    updated = [c for c in cameras if int(c['camera_id']) != camera_id]

    with open(CAMERA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['camera_id', 'camera_name', 'camera_url'])
        for cam in updated:
            writer.writerow([cam['camera_id'], cam['camera_name'], cam['camera_url']])

    return redirect(url_for('dashboard'))


# ---------------- CAMERA INITIALIZER ---------------- #
def get_camera(camera_id):
    if camera_id in camera_streams:
        return camera_streams[camera_id]

    cameras = load_cameras(CAMERA_FILE)
    cam = next((c for c in cameras if int(c['camera_id']) == camera_id), None)

    if not cam:
        return None

    source = cam['camera_url']

    try:
        source = int(source)
    except:
        pass

    print(f"[INFO] Opening camera: {source}")

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"❌ Cannot open camera {source}")
        return None

    camera_streams[camera_id] = cap
    return cap


# ---------------- VIDEO STREAM ---------------- #
def generate_frames(camera_id):
    cameras = load_cameras(CAMERA_FILE)

    cam = next((c for c in cameras if int(c['camera_id']) == camera_id), None)

    if not cam:
        print("❌ Camera not found")
        return

    cap = get_camera(camera_id)

    if cap is None:
        return

    last_saved_time = 0

    while True:
        success, frame = cap.read()

        if not success:
            print(f"❌ Camera {camera_id} not reading")
            break

        # YOLO DETECTION
        if not is_paused():
            results = model(frame)

            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])

                    if cls == 67:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "Mobile Detected", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        current_time = datetime.now().timestamp()

                        if current_time - last_saved_time > 5:
                            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            filename = f"{cam['camera_name']}_{timestamp}.jpg"
                            filepath = os.path.join(SCREENSHOT_FOLDER, filename)

                            cv2.imwrite(filepath, frame)
                            log_mobile_usage(cam['camera_name'])

                            # SEND TO RENDER
                            try:
                                with open(filepath, 'rb') as f:
                                    files = {'screenshot': f}
                                    data = {'camera_name': cam['camera_name']}
                                    requests.post(RENDER_UPLOAD_URL, files=files, data=data)
                            except:
                                pass

                            last_saved_time = current_time

        # STREAM FRAME
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# ---------------- VIDEO ROUTE ---------------- #
@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    return Response(generate_frames(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------------- PAUSE / RESUME ---------------- #
@app.route('/pause')
def pause():
    set_pause(True)
    return redirect(url_for('dashboard'))

@app.route('/resume')
def resume():
    set_pause(False)
    return redirect(url_for('dashboard'))


# ---------------- LOGS ---------------- #
@app.route('/logs')
def logs():
    return render_template('logs.html', logs=get_logs())


# ---------------- REPORT ---------------- #
@app.route('/report')
def report():
    return render_template('report.html', report=get_daily_report())


# ---------------- GALLERY ---------------- #
@app.route('/gallery')
def gallery():
    images = []
    if os.path.exists(SCREENSHOT_FOLDER):
        images = os.listdir(SCREENSHOT_FOLDER)
        images.sort(reverse=True)
    return render_template('gallery.html', images=images)


# ---------------- API ---------------- #
@app.route('/api/cameras')
def api_cameras():
    return jsonify(load_cameras(CAMERA_FILE))

@app.route('/api/logs')
def api_logs():
    return jsonify(get_logs())

@app.route('/api/report')
def api_report():
    return jsonify(get_daily_report())


# ---------------- RECEIVE FROM LOCAL ---------------- #
@app.route('/api/upload', methods=['POST'])
def api_upload():
    try:
        camera_name = request.form.get('camera_name')
        image = request.files.get('screenshot')

        if not camera_name or not image:
            return "Invalid request", 400

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{camera_name}_{timestamp}.jpg"

        filepath = os.path.join(SCREENSHOT_FOLDER, filename)
        image.save(filepath)

        log_mobile_usage(camera_name)

        print(f"[RENDER] Received: {filename}")

        return "OK", 200

    except Exception as e:
        return str(e), 500


# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
