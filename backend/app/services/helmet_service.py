import cv2
from ultralytics import YOLO
from pathlib import Path
import os

# --- CONFIGURATION ---
# Get absolute path to models directory
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_WEIGHTS_PATH = str(BASE_DIR / 'models' / 'best_helmet.pt') 

# Define the minimum confidence score required for a detection.
CONFIDENCE_THRESHOLD = 0.5 

# --- GLOBAL OBJECTS (Loaded ONCE when the server starts) ---
print("Loading Helmet Detection Model...")
try:
    model = YOLO(MODEL_WEIGHTS_PATH)
    print("Helmet model loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR: Could not load helmet model from {MODEL_WEIGHTS_PATH}: {e}")
    model = None

# Don't open camera on startup - it will block browser access!
# Camera will be accessed via frames sent from frontend

# --- API-Callable Function ---

def get_helmet_detection_status(frame=None):
    """
    This function is called by the API. 
    It processes a frame sent from the frontend and returns detection results.
    
    Args:
        frame: numpy array representing the image frame (from frontend webcam)
    """
    if model is None:
        return {"error": "Backend not initialized. Check model path."}
    
    if frame is None:
        return {"error": "No frame provided."}
    
    # Run inference with optimized parameters for speed
    results = model.predict(
        source=frame, 
        conf=CONFIDENCE_THRESHOLD, 
        verbose=False, 
        device='cpu',
        imgsz=640,  # Optimal for accuracy/speed balance
        half=False,  # Set to True if using GPU
        max_det=50   # Limit detections for performance
    )[0]

    # --- CHANGED LOGIC: Count detections instead of drawing ---
    
    violation_count = 0
    compliant_count = 0
    
    for box in results.boxes:
        class_id = int(box.cls[0].item())
        class_name = model.names[class_id]
        
        if class_name == 'hardhat':
            compliant_count += 1
        elif class_name == 'head':
            violation_count += 1
        # We ignore 'person' for this calculation to match your Angular UI
            
    # Calculate total people based on 'head' and 'hardhat' detections
    total_people = compliant_count + violation_count
    
    # Return data as a dictionary (FastAPI converts this to JSON)
    response_data = {
        "totalPeople": total_people,
        "compliantCount": compliant_count,
        "violationCount": violation_count
    }
    
    return response_data

# --- OLD CODE THAT WE REMOVED ---
# We removed the entire 'while True:' loop, cv2.rectangle, 
# cv2.putText, cv2.imshow, and cv2.waitKey.
# The server (main.py) handles the looping by being called repeatedly.