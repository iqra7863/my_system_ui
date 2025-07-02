from flask import Flask, render_template, request, redirect, url_for, session, Response
import os
import csv
import cv2
from datetime import datetime
from helpers.camera_manager import load_cameras, get_next_camera_id
from helpers.logger import get_logs, get_daily_report, log_mobile_usage
from helpers.pause_manager import set_pause, is_paused

app = Flask(__name__)
app.secret_key = 'iqra-detect-key'

users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'teacher': {'password': 'teacher123', 'role': 'teacher'},
    'viewer': {'password': 'viewer123', 'role': 'viewer'}
}

CAMERA_FILE = 'camera_data.csv'
SCREENSHOT_FOLDER = 'static/screenshots'
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

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

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    camera_sources = load_cameras(CAMERA_FILE)
    return render_template('dashboard.html', cameras=camera_sources, user=session['user'], role=session['role'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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

@app.route('/pause')
def pause():
    set_pause(True)
    return redirect(url_for('dashboard'))

@app.route('/resume')
def resume():
    set_pause(False)
    return redirect(url_for('dashboard'))

@app.route('/logs')
def logs():
    return render_template('logs.html', logs=get_logs())

@app.route('/report')
def report():
    return render_template('report.html', report=get_daily_report())

@app.route('/gallery')
def gallery():
    images = os.listdir(SCREENSHOT_FOLDER)
    images.sort(reverse=True)
    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        camera_name = request.form.get('camera_name')
        image = request.files.get('screenshot')

        if not camera_name or not image:
            return "Invalid request", 400

        # Save screenshot
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{camera_name}_{timestamp}.jpg"
        filepath = os.path.join(SCREENSHOT_FOLDER, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath)

        # Log usage
        log_mobile_usage(camera_name)
        print(f"[UPLOAD] Screenshot saved: {filename}")
        return "OK", 200

    except Exception as e:
        return f"Upload error: {e}", 500

# ✅ Video Feed Route for Each IP Camera
def generate_stream(url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        yield b"--frame\r\nContent-Type: text/plain\r\n\r\n[ERROR] Could not open stream.\r\n\r\n"
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    camera_sources = load_cameras(CAMERA_FILE)
    for cam in camera_sources:
        if int(cam['camera_id']) == cam_id:
            return Response(generate_stream(cam['camera_url']),
                            mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not found", 404

if __name__ == '__main__':
    app.run(debug=True)
