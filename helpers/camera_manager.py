import csv
import os

def load_cameras(camera_file='camera_data.csv'):
    cameras = []

    if not os.path.exists(camera_file):
        return cameras

    with open(camera_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cameras.append({
                'camera_id': int(row['camera_id']),
                'camera_name': row['camera_name'],
                'camera_url': row['camera_url']
            })

    return cameras


def get_next_camera_id(camera_file='camera_data.csv'):
    if not os.path.exists(camera_file):
        return 0

    ids = []
    with open(camera_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(int(row['camera_id']))

    return max(ids) + 1 if ids else 0
