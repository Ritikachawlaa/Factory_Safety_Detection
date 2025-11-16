# Real-Time Hard Hat Detection using YOLOv8 and OpenCV

import cv2
import os
from ultralytics import YOLO

# --- CONFIGURATION ---
# IMPORTANT: Change this path to the location where you saved your downloaded 'best.pt' file.
# Example: If you saved it in the same directory as this script, just use the filename.
MODEL_WEIGHTS_PATH = 'best_helmet.pt' 

# Set the video source: 0 for default webcam, or provide a video file path/RTSP stream URL.
VIDEO_SOURCE = 0 

# Define the minimum confidence score required for a detection to be displayed.
CONFIDENCE_THRESHOLD = 0.5 

# Color definitions (BGR format: Blue, Green, Red)
COLOR_COMPLIANCE = (0, 255, 0) # Green for helmet (compliance)
COLOR_VIOLATION = (0, 0, 255)  # Red for head (violation)
COLOR_PERSON = (255, 255, 0)   # Cyan for general person detection

# --- SETUP ---

try:
    # Load the custom trained model
    model = YOLO(MODEL_WEIGHTS_PATH)
    print(f"Model loaded from: {MODEL_WEIGHTS_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Please ensure 'best.pt' is in the correct path as specified in MODEL_WEIGHTS_PATH.")
    exit()

# Start video capture
cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}.")
    exit()

print("\n--- Starting Real-Time Detection (Press 'q' to exit) ---")

# --- MAIN DETECTION LOOP ---

while True:
    # Read a frame from the video source
    ret, frame = cap.read()

    if not ret:
        print("End of stream or cannot read frame.")
        break
    
    # Run inference on the current frame
    # verbose=False suppresses prediction output in the console
    results = model.predict(source=frame, conf=CONFIDENCE_THRESHOLD, verbose=False, device='cpu')[0]

    # Process results and draw bounding boxes
    for box in results.boxes:
        # Get coordinates, confidence, and class index
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        confidence = round(box.conf[0].item(), 2)
        class_id = int(box.cls[0].item())
        
        # Get class name from model's internal map
        class_name = model.names[class_id]
        
        # Determine color based on class
        if class_name == 'hardhat':
            color = COLOR_COMPLIANCE
            label = f"HELMET: {confidence:.2f}"
        elif class_name == 'head':
            color = COLOR_VIOLATION
            label = f"NO HELMET: {confidence:.2f}"
        else: # For 'person' or any other detected class (if present)
            color = COLOR_PERSON
            label = f"{class_name}: {confidence:.2f}"
        
        # Draw the bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw the label text
        cv2.putText(
            frame, 
            label, 
            (x1, y1 - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            color, 
            2
        )

    # Display the frame with detections
    cv2.imshow('Real-Time Hard Hat Monitoring', frame)

    # Exit loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---

cap.release()
cv2.destroyAllWindows()
print("\nDetection stopped. Exiting.")
