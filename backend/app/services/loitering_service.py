import cv2
import math
import time
from ultralytics import YOLO

# --- CONFIGURATION ---
MODEL_WEIGHTS_PATH = 'models/best_helmet.pt' # Using your helmet model
LOITERING_TIME_THRESHOLD = 10  # Seconds
GROUPING_DISTANCE_THRESHOLD = 150 # Pixels

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
person_loitering_timer = {}
# Stores {track_id} for individuals currently in violation
active_loitering_groups = set()

# --- HELPER FUNCTIONS ---

def get_person_center(box_coords):
    """Calculates the center point (x, y) of a bounding box."""
    x1, y1, x2, y2 = box_coords
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    return (center_x, center_y)

def calculate_distance(p1, p2):
    """Calculates the Euclidean distance between two center points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# --- API-Callable Function ---

def get_loitering_status(frame=None):
    """
    This function is called by the API on each request.
    It processes one frame and detects groups of people standing close together.
    
    NOTE: Simplified version without tracking (scipy dependency removed).
    Uses simple proximity detection instead of persistent tracking.
    
    Args:
        frame: numpy array representing the image frame (from frontend webcam)
    """
    global person_loitering_timer, active_loitering_groups

    if model is None:
        return {"error": "Backend not initialized. Check model path."}
    
    if frame is None:
        return {"error": "No frame provided."}

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
                    
                    if distance < GROUPING_DISTANCE_THRESHOLD:
                        active_groups += 1
                        checked_pairs.add((i, j))
                        break  # Count this as one group

    # 4. RETURN STATUS
    return {
        "activeGroups": active_groups,
        "totalPeople": len(person_data)
    }
