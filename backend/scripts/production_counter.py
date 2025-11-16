import cv2
import os
from ultralytics import YOLO
import supervision as sv
import numpy as np

# --- CONFIGURATION ---

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to your NEWLY trained product counting model
MODEL_WEIGHTS_PATH = os.path.join(SCRIPT_DIR, 'best_product.pt')

# --- VIDEO SOURCE ---
# Path to your test video (or '0' for webcam)
VIDEO_SOURCE = 0 # Using your webcam

# ---
# NOTE: These coordinates are for a standard 640x480 webcam frame.
# They are inset from the edges to make room for the 'In'/'Out' text.
# ---
LINE_START = sv.Point(100, 240)
LINE_END = sv.Point(540, 240)

# --- NEW: Define window size ---
WINDOW_NAME = "Production Counter (Press 'q' to exit)"
TARGET_WINDOW_WIDTH = 1280
TARGET_WINDOW_HEIGHT = 720


def main():
    print(f"Loading production counter model from: {MODEL_WEIGHTS_PATH}")
    
    # Check if model file exists
    if not os.path.exists(MODEL_WEIGHTS_PATH):
        print(f"--- !!! MODEL NOT FOUND !!! ---")
        print(f"Error: Could not find model weights at: {MODEL_WEIGHTS_PATH}")
        print("Please check that 'best_product.pt' is in the 'scripts/' folder.")
        return

    # Load the trained YOLOv8 model
    model = YOLO(MODEL_WEIGHTS_PATH)
    
    # Get class names from the model
    class_names = model.model.names
    print(f"Model classes: {class_names}")

    # Setup Supervision annotators and line counter
    line_counter = sv.LineZone(start=LINE_START, end=LINE_END)
    
    box_annotator = sv.BoxAnnotator(
        thickness=2
    )
    
    label_annotator = sv.LabelAnnotator(
        text_thickness=1,
        text_scale=0.5,
        text_color=sv.Color.WHITE 
    )
    
    line_annotator = sv.LineZoneAnnotator(
        thickness=4, 
        color=sv.Color.GREEN
    )

    print(f"--- Starting Production Counter on '{VIDEO_SOURCE}' (Press 'q' to exit) ---")
    
    # Open the video source
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"Error: Could not open video source '{VIDEO_SOURCE}'")
        return

    # --- NEW: Create a resizable window ---
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, TARGET_WINDOW_WIDTH, TARGET_WINDOW_HEIGHT)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video stream ended or failed to read frame.")
            break 

        # Run YOLOv8 tracking on the frame
        # conf=0.2 makes it easier to detect items (lower confidence)
        # imgsz=320 makes it run MUCH faster on your CPU
        results = model.track(frame, persist=True, verbose=False, conf=0.2, imgsz=320)
        
        # Convert YOLO results to Supervision Detections format
        detections = sv.Detections.from_ultralytics(results[0])

        # --- Filter to include ALL box types from your dataset ---
        target_class_names = [
            'big_close_box', 'big_damaged_box', 'big_open_box', 
            'small_close_box', 'small_damaged_box', 'small_open_box'
        ]
        
        target_class_ids = []
        for class_id, name in class_names.items():
            if name in target_class_names:
                target_class_ids.append(class_id)
        
        mask = np.isin(detections.class_id, target_class_ids)
        detections = detections[mask]
        
        # Update the line counter with the filtered detections
        line_counter.trigger(detections=detections)

        # Get labels for the detections
        if detections.tracker_id is not None:
            labels = [
                f"ID:{tracker_id} {class_names[class_id]} {confidence:0.2f}"
                for confidence, class_id, tracker_id
                in zip(detections.confidence, detections.class_id, detections.tracker_id)
            ]
        else:
            labels = [
                f"{class_names[class_id]} {confidence:0.2f}"
                for confidence, class_id
                in zip(detections.confidence, detections.class_id)
            ]
        
        # --- ANNOTATE FRAME ---
        annotated_frame = box_annotator.annotate(
            scene=frame.copy(), 
            detections=detections
        )
        annotated_frame = label_annotator.annotate(
            scene=annotated_frame,
            detections=detections,
            labels=labels
        )
        line_annotator.annotate(
            frame=annotated_frame, 
            line_counter=line_counter
        )
        
        # --- NEW: Resize the small annotated frame to our target window size ---
        display_frame = cv2.resize(annotated_frame, (TARGET_WINDOW_WIDTH, TARGET_WINDOW_HEIGHT))
        
        # Show the annotated frame
        cv2.imshow(WINDOW_NAME, display_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("--- Production Counter stopped. ---")
    print(f"Total items counted (IN): {line_counter.in_count}")

if __name__ == "__main__":
    main()



