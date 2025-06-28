import csv
import os
from collections import defaultdict
from datetime import datetime

LOG_FILE = 'static/logs/detection_log.csv'

def log_mobile_usage(camera_name):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = [now, camera_name]

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Camera'])

    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(entry)

    print(f"[LOG] {entry}")


def get_logs():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        return list(reader)


def get_daily_report():
    report = defaultdict(int)

    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            date = row[0].split(" ")[0]  # Extract date from timestamp
            report[date] += 1

    return sorted(report.items())
