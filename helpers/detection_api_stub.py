 # helpers/detection_api_stub.py

def generate_frames(source, camera_name):
    """
    Dummy function for Render - does not run actual detection.
    Used only to keep UI from crashing.
    """
    print("[INFO] Detection disabled on Render. Using external detect_api.py.")
    while True:
        # You could optionally stream a static image
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')

