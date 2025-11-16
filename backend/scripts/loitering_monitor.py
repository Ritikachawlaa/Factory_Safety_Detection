# Real-Time Factory Loitering Monitor using YOLOv8 and ByteTrack

import cv2
import math
import time
from ultralytics import YOLO

# --- CONFIGURATION ---
# IMPORTANT: Use the same trained model weights from your successful run.
MODEL_WEIGHTS_PATH = 'best_helmet.pt' 

# Set the video source: 0 for default webcam, or provide a video file path/RTSP stream URL.
VIDEO_SOURCE = 0 

# LOITERING LOGIC PARAMETERS
# Max distance (in pixels) for two people to be considered "grouped." 
# This needs calibration based on your CCTV angle/resolution.
GROUPING_DISTANCE_THRESHOLD = 150 
# Time (in seconds) that a group must stand still before an alarm is triggered.
LOITERING_TIME_THRESHOLD = 10 

# --- INTERNAL STATE (DO NOT MODIFY) ---
# Stores {track_id: start_time} for individuals
person_loitering_timer = {}
# Stores a list of IDs currently involved in a loitering violation
active_loitering_groups = set()

# --- SETUP ---

try:
    # Load the custom trained model (using a base YOLO model for simplicity, but your best.pt is better)
    model = YOLO(MODEL_WEIGHTS_PATH)
    print(f"Model loaded from: {MODEL_WEIGHTS_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Please ensure 'best.pt' is in the correct path.")
    exit()

# Start video capture
cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}. Check your webcam/stream settings.")
    exit()

# --- HELPER FUNCTIONS ---

def get_person_center(box):
    """Calculates the center point (x, y) of a bounding box."""
    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    return (center_x, center_y)

def calculate_distance(p1, p2):
    """Calculates the Euclidean distance between two center points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# --- MAIN DETECTION LOOP ---

current_time = time.time()
print("\n--- Starting Real-Time Loitering Monitor (Press 'q' to exit) ---")

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of stream or cannot read frame.")
        break

    current_frame_time = time.time()
    
    # 1. RUN DETECTION & TRACKING
    # The 'tracker' argument enables ByteTrack. We only care about people for loitering.
    results = model.track(
        source=frame, 
        persist=True, 
        tracker="bytetrack.yaml", 
        classes=[0, 1], # Assuming 0=Head, 1=Hardhat, or Person classes if trained on COCO
        verbose=False
    )
    
    # Extract bounding boxes, IDs, and centers for processing
    person_data = [] # Stores: [(track_id, center_point, box_coords)]
    
    if results and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy()
        
        for box, track_id in zip(boxes, track_ids):
            box_coords = [int(x) for x in box]
            center_point = get_person_center(results[0].boxes.cpu()) # Need to calculate center from original box object
            person_data.append((track_id, center_point, box_coords))


    # 2. LOITERING LOGIC (Group Check)
    # Check every pair of people for proximity
    is_loitering_detected = False
    
    if len(person_data) >= 2:
        for i in range(len(person_data)):
            id_i, center_i, box_i = person_data[i]
            
            for j in range(i + 1, len(person_data)):
                id_j, center_j, box_j = person_data[j]
                
                distance = calculate_distance(center_i, center_j)
                
                if distance < GROUPING_DISTANCE_THRESHOLD:
                    # People i and j are close enough to be considered a group
                    
                    # Form a unique group key (e.g., "1-5" or "5-1")
                    group_key = tuple(sorted((id_i, id_j)))
                    
                    # Initialize timer if this is a new group proximity event
                    if group_key not in person_loitering_timer:
                        person_loitering_timer[group_key] = current_frame_time
                    
                    # Check if loitering time threshold has been exceeded
                    elapsed_time = current_frame_time - person_loitering_timer[group_key]
                    
                    if elapsed_time >= LOITERING_TIME_THRESHOLD:
                        # ALARM TRIGGERED: Add both IDs to the active violation set
                        active_loitering_groups.add(id_i)
                        active_loitering_groups.add(id_j)
                        is_loitering_detected = True
                        
                        # Draw a thick connecting line between loitering individuals
                        cv2.line(frame, center_i, center_j, (0, 165, 255), 3) 
                    else:
                        # They are close, but the time hasn't elapsed yet. 
                        # Optionally show a warning line or text.
                        pass
                
                else:
                    # If they move too far apart, reset any group timer involving them.
                    # This handles the case where a close pair breaks up.
                    group_key_ij = tuple(sorted((id_i, id_j)))
                    if group_key_ij in person_loitering_timer and group_key_ij not in active_loitering_groups:
                        del person_loitering_timer[group_key_ij]


    # 3. VISUALIZATION & RESET LOGIC
    # Draw boxes using the track ID and highlight violators
    for track_id, center_point, box_coords in person_data:
        x1, y1, x2, y2 = box_coords
        
        # Check if the person is part of an active loitering group
        if track_id in active_loitering_groups:
            color = (0, 0, 255) # Red for violation
            text = f"ID {track_id} - LOITERING!"
            
            # Draw a big violation text banner
            cv2.putText(frame, "LOITERING VIOLATION!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        else:
            # Check if this ID was previously marked as loitering but is now moving or alone
            if track_id in person_loitering_timer:
                 # Calculate time elapsed for pending groups they are in
                current_pairs = [k for k, v in person_loitering_timer.items() if track_id in k and v < current_frame_time]
                
                if current_pairs:
                    elapsed_time = current_frame_time - person_loitering_timer[current_pairs[0]]
                    color = (0, 255, 255) # Yellow for warning/pending loitering
                    text = f"ID {track_id} | Time: {int(elapsed_time)}s"
                else:
                    color = (255, 255, 0) # Cyan for normal tracking
                    text = f"ID {track_id}"
            else:
                 color = (255, 255, 0) # Cyan for normal tracking
                 text = f"ID {track_id}"

        # Draw the bounding box and ID label
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


    # Display the frame with detections
    cv2.imshow('Loitering Monitor (Press Q to Exit)', frame)

    # Exit loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---

cap.release()
cv2.destroyAllWindows()
print("\nDetection stopped. Exiting.")
