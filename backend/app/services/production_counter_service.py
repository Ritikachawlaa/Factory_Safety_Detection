import cv2
import os
from ultralytics import YOLO
import numpy as np

# --- CONFIGURATION ---
MODEL_WEIGHTS_PATH = 'models/best_product.pt'
TRACKER_CONFIG = 'bytetrack.yaml'  # Use ByteTrack for object tracking
LINE_Y_POSITION = 0.5  # Line position (50% of frame height)
CONFIDENCE_THRESHOLD = 0.25

# Don't open camera on startup - it will block browser access!
# The frontend will send frames via API instead.

# --- GLOBAL OBJECTS (Loaded ONCE when the server starts) ---
print("Loading Production Counter Model...")
try:
    model = YOLO(MODEL_WEIGHTS_PATH)
    class_names = model.model.names
    print("Production model loaded successfully.")
    
    # Pre-calculate the target class IDs one time
    target_class_names = [
        'big_close_box', 'big_damaged_box', 'big_open_box', 
        'small_close_box', 'small_damaged_box', 'small_open_box'
    ]
    TARGET_CLASS_IDS = []
    for class_id, name in class_names.items():
        if name in target_class_names:
            TARGET_CLASS_IDS.append(class_id)
    print(f"Tracking {len(TARGET_CLASS_IDS)} target classes.")
    
except Exception as e:
    print(f"FATAL ERROR: Could not load production model: {e}")
    model = None
    TARGET_CLASS_IDS = []

# --- GLOBAL STATE (Persists in memory) ---
# Track which object IDs have crossed the line
crossed_ids = set()  # Stores tracker IDs that have crossed
production_count = 0  # Total count of items that crossed
line_y = None  # Will be set based on frame height

# --- API-Callable Function ---

def get_production_count(frame=None):
    """
    OPTIMIZED: Uses ByteTrack for proper line-crossing detection.
    Only counts objects when they cross the virtual line.
    
    Args:
        frame: numpy array representing the image frame (from frontend webcam)
    """
    global production_count, crossed_ids, line_y
    
    if model is None or not TARGET_CLASS_IDS:
        return {"error": "Backend not initialized. Check model."}
    
    if frame is None:
        return {"error": "No frame provided."}
    
    # Set line position on first frame
    if line_y is None:
        frame_height = frame.shape[0]
        line_y = int(frame_height * LINE_Y_POSITION)
        print(f"📍 Line crossing detection at Y={line_y} (frame height: {frame_height})")
    
    try:
        # Run YOLO with tracking (ByteTrack doesn't require scipy when using built-in tracker)
        results = model.track(
            source=frame,
            persist=True,  # Persist tracks across frames
            tracker=TRACKER_CONFIG,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
            imgsz=640,
            half=False,
            classes=TARGET_CLASS_IDS  # Only track target classes
        )
        
        # Check for line crossings
        if results and results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes
            class_ids = boxes.cls.cpu().numpy().astype(int)
            tracker_ids = boxes.id.cpu().numpy().astype(int)
            xyxy = boxes.xyxy.cpu().numpy()
            
            for i, (class_id, tracker_id, box) in enumerate(zip(class_ids, tracker_ids, xyxy)):
                if class_id in TARGET_CLASS_IDS:
                    # Get box center Y coordinate
                    box_center_y = (box[1] + box[3]) / 2
                    
                    # Check if object crossed the line (and hasn't been counted yet)
                    if box_center_y > line_y and tracker_id not in crossed_ids:
                        crossed_ids.add(tracker_id)
                        production_count += 1
                        print(f"✅ Item #{production_count} crossed (ID: {tracker_id})")
    
    except Exception as e:
        print(f"⚠️ Tracking error: {e}. Falling back to simple counting.")
        # Fallback to simple detection if tracking fails
        results = model.predict(frame, verbose=False, conf=CONFIDENCE_THRESHOLD, imgsz=640)
        if results and results[0].boxes:
            boxes = results[0].boxes
            class_ids = boxes.cls.cpu().numpy().astype(int)
            current_count = sum(1 for cid in class_ids if cid in TARGET_CLASS_IDS)
            production_count += current_count
    
    return {
        "itemCount": production_count
    }

def reset_production_count():
    """Reset the production counter and tracking state."""
    global production_count, crossed_ids, line_y
    production_count = 0
    crossed_ids.clear()
    line_y = None  # Will be recalculated on next frame
    print("🔄 Production counter reset")
    return {"itemCount": 0, "message": "Counter reset successfully"}
