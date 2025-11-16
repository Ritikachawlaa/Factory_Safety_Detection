import cv2
import os
import time
from deepface import DeepFace
import numpy as np

# --- CONFIGURATION ---

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the folder containing known employee images
# This script will build the database from this folder
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'database', 'employees')

# The model used for face recognition
# 'VGG-Face' is fast and reliable.
RECOGNITION_MODEL = "VGG-Face"

# The model used for just finding faces in the frame
# 'opencv' is the fastest detector. 'ssd' or 'mtcnn' are more accurate.
DETECTOR_BACKEND = "opencv" 

# How often (in seconds) to run the expensive recognition step
RECOGNITION_INTERVAL = 2 # 2 seconds

# ---
# NOTE: This script does not use your YOLO models.
# It uses 'deepface' which has its own built-in models.
# ---

def verify_employee_db(db_path):
    """Checks if the database path is valid and contains images."""
    if not os.path.exists(db_path):
        print(f"--- !!! DATABASE NOT FOUND !!! ---")
        print(f"Error: Database folder not found at: {db_path}")
        print("Please create the 'database/employees' folder and add images.")
        return False

    image_files = [f for f in os.listdir(db_path) if f.endswith(('.jpg', '.png'))]
    if not image_files:
        print(f"--- !!! NO EMPLOYEES FOUND !!! ---")
        print(f"Error: No .jpg or .png images found in: {db_path}")
        print("Please add employee images to the database folder.")
        return False
        
    print(f"Database verified. Found {len(image_files)} employee images.")
    return True

def main():
    
    # --- 1. VERIFY DATABASE ---
    if not verify_employee_db(DB_PATH):
        return # Stop if database is not set up

    # --- 2. INITIALIZE VIDEO CAPTURE ---
    cap = cv2.VideoCapture(0) # 0 for webcam
    if not cap.isOpened():
        print("Error: Could not open video source '0' (webcam)")
        return

    print("--- Starting Real-Time Attendance System (Press 'q' to exit) ---")
    
    # Timer to prevent checking every single frame (saves resources)
    last_check_time = 0
    
    # This dictionary will store the results to display between checks
    # Key: (x, y, w, h) bounding box
    # Value: "Name" or "Unknown"
    current_face_identities = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from webcam.")
            break
            
        # Create a copy to draw on, so we can pass the clean frame to deepface
        draw_frame = frame.copy()
        
        current_time = time.time()
        
        # --- 3. DETECT & RECOGNIZE FACES (Only every 2 seconds) ---
        if current_time - last_check_time > RECOGNITION_INTERVAL:
            last_check_time = current_time
            current_face_identities = {} # Clear old identities
            
            try:
                # This is the main DeepFace function.
                # It finds all faces in 'frame' and compares them to the 'DB_PATH'
                # Returns a list of DataFrames. Each DataFrame = 1 face found.
                dfs = DeepFace.find(
                    img_path=frame,
                    db_path=DB_PATH,
                    model_name=RECOGNITION_MODEL,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False, # Don't crash if no face is found
                    silent=True # Suppress console logs
                )
                
                # 'dfs' is a list of dataframes, one for each face found in the frame
                for df in dfs:
                    if not df.empty:
                        # --- A. FACE IS VERIFIED ---
                        # Get the best match (first row, lowest distance)
                        best_match = df.iloc[0]
                        
                        # Get the name from the file path
                        # e.g., ".../database/employees/anudip.jpg" -> "anudip"
                        match_name = os.path.splitext(os.path.basename(best_match['identity']))[0]
                        
                        # Get the bounding box
                        x = int(best_match['source_x'])
                        y = int(best_match['source_y'])
                        w = int(best_match['source_w'])
                        h = int(best_match['source_h'])
                        
                        current_face_identities[(x, y, w, h)] = match_name
                        
                    # Note: The 'dfs' list from DeepFace.find() may not include
                    # faces that had ZERO matches. We can only reliably draw
                    # boxes for verified faces with this method.
                    # For a full "Unknown" system, a 2-step (detect then verify)
                    # process is needed, but this is much simpler.

            except Exception as e:
                # This often happens if no faces are in the frame
                # Or on the first frame as the model loads
                pass 

        # --- 4. DRAW ANNOTATIONS (This happens every frame) ---
        
        # We draw the boxes from the last successful check
        # This makes the video feed feel smooth
        for (x, y, w, h), name in current_face_identities.items():
            color = (0, 255, 0) # GREEN for Verified
            text = name.capitalize()
            
            # Log attendance (in a real app, you'd save this to a file/database)
            # We add a simple check to only log it once when they appear
            if name not in getattr(main, "logged_today", set()):
                print(f"ATTENDANCE LOGGED: {text}")
                if not hasattr(main, "logged_today"):
                    main.logged_today = set()
                main.logged_today.add(name)

            # Draw the box and name
            cv2.rectangle(draw_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(draw_frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
        # Display the frame
        cv2.imshow("Attendance System (Press 'q' to exit)", draw_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("--- Attendance System stopped. ---")

if __name__ == "__main__":
    main()

