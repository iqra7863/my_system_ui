import csv
import os

def load_cameras(camera_file='camera_data.csv'):
    sources = {}
    if not os.path.exists(camera_file):
        return sources

    with open(camera_file, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 3:
                continue
            cam_id = int(row[0])
            sources[cam_id] = {'name': row[1], 'url': row[2]}
    return sources


def get_next_camera_id(camera_file='camera_data.csv'):
    if not os.path.exists(camera_file):
        return 0

    with open(camera_file, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        ids = []
        for row in reader:
            if len(row) > 0 and row[0].isdigit():
                ids.append(int(row[0]))
        return max(ids) + 1 if ids else 0
