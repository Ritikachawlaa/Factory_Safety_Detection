_deepface_loaded = False

def _ensure_deepface():
    """Lazy load DeepFace only when first attendance check is made."""
    global DeepFace, _deepface_loaded
    if not _deepface_loaded:
        _deepface_loaded = True
        try:
            from deepface import DeepFace as DF
            DeepFace = DF
            print("✅ DeepFace library loaded successfully")
            return True
        except Exception as e:
            print(f"❌ DeepFace library not available: {type(e).__name__}: {str(e)[:100]}")
            print("Attendance service will not be available.")
            DeepFace = None
            return False
    return DeepFace is not None

# --- CONFIGURATION ---
# This path is relative to your ROOT folder (where you run uvicorn)
DB_PATH = 'database/employees'
RECOGNITION_MODEL = "Facenet"  # 3x faster than VGG-Face
DETECTOR_BACKEND = "opencv"  # Using opencv instead of retinaface (more compatible)
RECOGNITION_INTERVAL = 0.5  # Check every 0.5 seconds (walk-by capable)
EMBEDDINGS_CACHE_FILE = 'database/employee_embeddings.pkl'
CONFIDENCE_THRESHOLD = 0.6  # Lower = more strict matching

def cosine_distance(a, b):
    """
    Calculate cosine distance without scipy (numpy-only implementation).
    Returns distance between 0 (identical) and 2 (opposite).
    """
    # Cosine similarity = dot(a,b) / (norm(a) * norm(b))
    # Cosine distance = 1 - cosine_similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 2.0  # Maximum distance if zero vector
    
    cosine_similarity = dot_product / (norm_a * norm_b)
    return 1.0 - cosine_similarity  # Distance (0 = same, 1 = orthogonal, 2 = opposite)

# Don't open camera on startup - it will block browser access!
# The frontend will send frames via API instead.

# --- GLOBAL OBJECTS (Loaded ONCE when the server starts) ---
print("Initializing Attendance System...")

# Store pre-computed embeddings: {employee_name: embedding_vector}
employee_embeddings = {}
_embeddings_initialized = False

if True:  # Changed from if DeepFace: - initialization happens on first use instead
    # --- 1. VERIFY DATABASE ---
    def verify_employee_db(db_path):
        if not os.path.exists(db_path):
            print(f"--- !!! DATABASE NOT FOUND !!! ---")
            print(f"Error: Database folder not found at: {db_path}")
            return False
        image_files = [f for f in os.listdir(db_path) if f.endswith(('.jpg', '.png'))]
        if not image_files:
            print(f"--- !!! NO EMPLOYEES FOUND !!! ---")
            print(f"Error: No .jpg or .png images found in: {db_path}")
            return False
        print(f"Attendance DB verified. Found {len(image_files)} employee images.")
        return True
    
    def load_or_create_embeddings():
        """Load cached embeddings or compute them fresh (10x performance boost)"""
        global employee_embeddings
        
        if not _ensure_deepface():
            return False
        
        # Try to load cached embeddings
        if os.path.exists(EMBEDDINGS_CACHE_FILE):
            try:
                with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
                    employee_embeddings = pickle.load(f)
                print(f"✅ Loaded {len(employee_embeddings)} cached embeddings")
                return True
            except Exception as e:
                print(f"⚠️ Cache load failed: {e}. Regenerating...")
        
        # Compute embeddings for all employees
        print("⏳ Pre-computing face embeddings (one-time operation)...")
        employee_embeddings = {}
        image_files = [f for f in os.listdir(DB_PATH) if f.endswith(('.jpg', '.png'))]
        
        for img_file in image_files:
            try:
                img_path = os.path.join(DB_PATH, img_file)
                embedding_objs = DeepFace.represent(
                    img_path=img_path,
                    model_name=RECOGNITION_MODEL,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False
                )
                if embedding_objs:
                    employee_name = os.path.splitext(img_file)[0]
                    employee_embeddings[employee_name] = np.array(embedding_objs[0]["embedding"])
                    print(f"  ✓ {employee_name}")
            except Exception as e:
                print(f"  ✗ Failed to process {img_file}: {e}")
        
        # Cache the embeddings for next startup
        try:
            os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_FILE), exist_ok=True)
            with open(EMBEDDINGS_CACHE_FILE, 'wb') as f:
                pickle.dump(employee_embeddings, f)
            print(f"💾 Cached {len(employee_embeddings)} embeddings")
        except Exception as e:
            print(f"⚠️ Failed to cache embeddings: {e}")
        
        return len(employee_embeddings) > 0

    # Skip initialization at module load - will initialize on first use
    print("⏳ Attendance service will initialize on first use (lazy loading)")

# --- GLOBAL STATE (Persists in memory) ---
last_check_time = 0
# These store the data for the API
logged_today = set()       # Stores unique names: {"anudip", "ritika"}
attendance_log = []        # Stores log strings: ["9:30: Ritika verified."]
last_person_seen = "---"


# --- API-Callable Function ---

def get_attendance_status(frame=None):
    """
    OPTIMIZED: Uses pre-computed embeddings for 10x faster recognition.
    Walk-by capable with 0.5s response time.
    
    Args:
        frame: numpy array representing the image frame (from frontend webcam)
    """
    global last_check_time, logged_today, attendance_log, last_person_seen, _embeddings_initialized

    # Lazy initialization on first call
    if not _embeddings_initialized:
        _embeddings_initialized = True
        if not _ensure_deepface():
            return {"error": "DeepFace library failed to load."}
        if not verify_employee_db(DB_PATH):
            return {"error": "Employee database not found or invalid."}
        if not load_or_create_embeddings():
            return {"error": "Failed to load employee embeddings."}
        print(f"✅ Attendance service initialized with {len(employee_embeddings)} employees")

    if frame is None:
        return {"error": "No frame provided."}

    current_time = time.time()

    # --- 1. RUN OPTIMIZED CHECK (Only if interval has passed) ---
    if current_time - last_check_time > RECOGNITION_INTERVAL:
        last_check_time = current_time
        
        try:
            # Extract embedding from current frame (FAST: ~0.2-0.3s)
            frame_embeddings = DeepFace.represent(
                img_path=frame,
                model_name=RECOGNITION_MODEL,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=False
            )
            
            # Process all faces detected in the frame
            for face_obj in frame_embeddings:
                frame_embedding = np.array(face_obj["embedding"])
                
                # Compare with all pre-computed employee embeddings (FAST: ~0.01s)
                best_match_name = None
                min_distance = float('inf')
                
                for employee_name, employee_embedding in employee_embeddings.items():
                    # Calculate cosine distance (0 = identical, 1 = orthogonal)
                    distance = cosine_distance(frame_embedding, employee_embedding)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match_name = employee_name
                
                # If match is confident enough, log attendance
                if min_distance < CONFIDENCE_THRESHOLD and best_match_name:
                    if best_match_name not in logged_today:
                        name_capitalized = best_match_name.capitalize()
                        print(f"✅ ATTENDANCE LOGGED: {name_capitalized} (confidence: {1-min_distance:.2%})")
                        
                        # Update global state
                        logged_today.add(best_match_name)
                        last_person_seen = name_capitalized
                        
                        # Add to the log list
                        log_time = datetime.now().strftime("%I:%M:%S %p")
                        log_entry = f"{log_time}: {name_capitalized} verified."
                        attendance_log.insert(0, log_entry)
                        
                        # Keep log from getting too big
                        if len(attendance_log) > 20:
                            attendance_log.pop()
                            
        except Exception as e:
            # This often happens if no faces are in the frame
            pass 

    # --- 2. ALWAYS RETURN THE CURRENT STATE ---
    return {
        "verifiedCount": len(logged_today),
        "lastPersonSeen": last_person_seen,
        "attendanceLog": attendance_log
    }