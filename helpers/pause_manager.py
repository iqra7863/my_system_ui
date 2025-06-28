# helpers/pause_manager.py

# Global pause flag
pause_detection = False

def set_pause(state: bool):
    global pause_detection
    pause_detection = state

def is_paused():
    return pause_detection
