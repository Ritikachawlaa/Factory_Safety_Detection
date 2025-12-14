import cv2
import math
import time
from ultralytics import YOLO
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_WEIGHTS_PATH = str(BASE_DIR / 'models' / 'best_helmet.pt')  # Using your helmet model

# --- CONFIGURATION ---
DEFAULT_LOITERING_TIME_THRESHOLD = 10  # Seconds
DEFAULT_GROUPING_DISTANCE_THRESHOLD = 150 # Pixels

def get_loitering_config():
    """Get loitering configuration from config file or use defaults"""
    # TODO: Load from JSON config file in the future
    return {
        'time_threshold': DEFAULT_LOITERING_TIME_THRESHOLD,
        'distance_threshold': DEFAULT_GROUPING_DISTANCE_THRESHOLD
    }

# Don't open camera on startup - it will block browser access!
# The frontend will send frames via API instead.

# --- GLOBAL OBJECTS (Loaded ONCE when the server starts) ---
print("Loading Loitering Model (YOLOv8)...")
try:
    model = YOLO(MODEL_WEIGHTS_PATH)
    print("Loitering model loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR: Could not load loitering model: {e}")
    model = None

# --- GLOBAL STATE (Persists in memory) ---
# Stores {group_key: start_time} where group_key is tuple(sorted(id_i, id_j))


def get_loitering_status(frame):
    """
    This function is called by the API on each request.
    It processes one frame and detects groups of people standing close together.
    Uses dynamic config for thresholds.
    """
    if model is None:
        return {"error": "Backend not initialized. Check model path."}
    if frame is None:
        return {"error": "No frame provided."}

    # Get config
    config = get_loitering_config()
    time_threshold = config['time_threshold']
    distance_threshold = config['distance_threshold']


    # 1. RUN DETECTION with optimized parameters
    results = model.predict(
        source=frame, 
        classes=[0, 1],  # Assuming 0=Head, 1=Hardhat (person detection)
        verbose=False,
        conf=0.5,
        imgsz=640,  # Optimal for accuracy/speed balance
        half=False,  # Set to True if using GPU
        max_det=30   # Limit detections for performance
    )

    # 2. EXTRACT PERSON DATA
    person_data = [] # Stores: [(center_point, box_coords)]
    if results and results[0].boxes:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        for box in boxes:
            box_coords = [int(x) for x in box]
            center_point = get_person_center(box_coords)
            person_data.append((center_point, box_coords))

    # 3. CHECK FOR GROUPS (people standing close together)
    active_groups = 0
    # Check all pairs for proximity
    if len(person_data) >= 2:
        checked_pairs = set()
        for i in range(len(person_data)):
            for j in range(i + 1, len(person_data)):
                if (i, j) not in checked_pairs:
                    center_i = person_data[i][0]
                    center_j = person_data[j][0]
                    distance = calculate_distance(center_i, center_j)
                    if distance < distance_threshold:
                        active_groups += 1
                        checked_pairs.add((i, j))
                        break  # Count this as one group

    # 4. RETURN STATUS
    return {
        "activeGroups": active_groups,
        "totalPeople": len(person_data),
        "config": config
    }
