from flask import Flask, render_template, request, redirect, url_for, session, Response
import os
import csv
from helpers.camera_manager import load_cameras, get_next_camera_id
from helpers.detection_api_stub import generate_frames  # ✅ Use the stub version (no cv2)
from helpers.logger import get_logs, get_daily_report
from helpers.pause_manager import set_pause, is_paused

app = Flask(__name__)
app.secret_key = 'iqra-detect-key'

users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'teacher': {'password': 'teacher123', 'role': 'teacher'},
    'viewer': {'password': 'viewer123', 'role': 'viewer'}
}

CAMERA_FILE = 'camera_data.csv'
camera_sources = {}

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
    camera_sources.update(load_cameras(CAMERA_FILE))
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

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    cams = load_cameras(CAMERA_FILE)
    if cam_id in cams:
        cam_url = cams[cam_id]['url']
        cam_name = cams[cam_id]['name']
        print(f"[STREAM] Streaming from {cam_url} ({cam_name})")
        return Response(generate_frames(cam_url, cam_name),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not found."

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
    images = os.listdir('static/screenshots')
    return render_template('gallery.html', images=images)

if __name__ == '__main__':
    app.run(debug=True)
