"""
Face Detection and Recognition Model Wrapper
Reuses existing DeepFace implementation
"""
import cv2
import numpy as np
import pickle
from pathlib import Path
import os
from scipy.spatial.distance import cosine

class FaceRecognizer:
    """Wrapper for face detection and recognition using DeepFace"""
    
    def __init__(self):
        self.deepface = None
        self.database_path = None
        self.embeddings_cache = {}
        self.embeddings_cache_file = None
        self.initialized = False
        self.face_distance_threshold = 0.6  # Cosine distance threshold for face matching (lowered for better accuracy)
        
    def load(self):
        """Lazy load DeepFace and employee database"""
        try:
            BASE_DIR = Path(__file__).parent.parent
            self.database_path = BASE_DIR / 'database' / 'employees'
            self.embeddings_cache_file = BASE_DIR / 'database' / 'employee_embeddings.pkl'
            
            # Don't import DeepFace until first use (lazy loading)
            print("✅ Face Recognition System Ready (lazy loading)")
            return True
        except Exception as e:
            print(f"❌ Face recognition setup failed: {e}")
            return False
    
    def _ensure_deepface(self):
        """Initialize DeepFace on first use"""
        if not self.initialized:
            try:
                from deepface import DeepFace
                self.deepface = DeepFace
                self.reload_embeddings()
                self.initialized = True
                print("✅ DeepFace loaded")
            except Exception as e:
                print(f"DeepFace import failed: {e}")
                self.deepface = None
    
    def reload_embeddings(self):
        """
        Reload face embeddings from employee database.
        This should be called:
        - At startup
        - After a new employee is registered
        """
        print("\n🔄 DEBUG: reload_embeddings() starting...")
        self.embeddings_cache = {}
        
        # First try to load from cache file
        if self.embeddings_cache_file and os.path.exists(self.embeddings_cache_file):
            try:
                print(f"🔄 DEBUG: Loading cache from {self.embeddings_cache_file}")
                with open(self.embeddings_cache_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                
                # Validate embedding dimensions (Facenet512 = 512 dimensions)
                if self.embeddings_cache:
                    first_embedding = next(iter(self.embeddings_cache.values()))
                    embedding_dim = len(first_embedding)
                    print(f"🔍 Cache embedding dimension: {embedding_dim}")
                    
                    if embedding_dim != 512:
                        print(f"⚠️ DIMENSION MISMATCH! Expected 512, got {embedding_dim}")
                        print(f"🔄 Deleting old cache and regenerating with Facenet512...")
                        os.remove(self.embeddings_cache_file)
                        self.embeddings_cache = {}
                        # Continue to regeneration below
                    else:
                        print(f"✅ Cache loaded: {len(self.embeddings_cache)} faces")
                        print(f"📊 KNOWN FACES COUNT: {len(self.embeddings_cache)}")
                        print(f"📝 KNOWN NAMES: {list(self.embeddings_cache.keys())}")
                        for name in self.embeddings_cache.keys():
                            print(f"   ✓ {name}")
                        return
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
                self.embeddings_cache = {}
        
        # If cache doesn't exist or is empty, generate from employee images
        if self.database_path and os.path.exists(self.database_path):
            print(f"🔄 DEBUG: Generating embeddings from {self.database_path}")
            self._generate_embeddings_from_images()
        else:
            print(f"🔄 DEBUG: Database path missing: {self.database_path}")
    
    def _generate_embeddings_from_images(self):
        """Generate embeddings from employee images"""
        print(f"🔄 DEBUG: _generate_embeddings_from_images() called")
        if not self.deepface:
            print(f"🔄 DEBUG: DeepFace not initialized, skipping")
            return
        if not self.database_path:
            print(f"🔄 DEBUG: No database path set")
            return
        
        try:
            print(f"🔄 DEBUG: Scanning {self.database_path}...")
            employee_images = list(self.database_path.glob('*.jpg')) + list(self.database_path.glob('*.png'))
            print(f"🔄 DEBUG: Found {len(employee_images)} images: {[img.name for img in employee_images]}")
            
            if not employee_images:
                print("📊 KNOWN FACES COUNT: 0")
                return
            
            for image_path in employee_images:
                employee_name = image_path.stem
                print(f"🔄 DEBUG: Processing {employee_name}...")
                try:
                    # Generate embedding for employee image
                    print(f"🔄 DEBUG: Calling DeepFace on {image_path}")
                    result = self.deepface.represent(
                        str(image_path),
                        model_name='Facenet512',
                        enforce_detection=False
                    )
                    print(f"🔄 DEBUG: DeepFace returned {len(result)} results")
                    embedding = result[0]['embedding']
                    print(f"🔄 DEBUG: Embedding shape: {len(embedding)}")
                    
                    self.embeddings_cache[employee_name] = embedding
                    print(f"✅ {employee_name}: embedding generated and cached")
                except Exception as e:
                    print(f"❌ {employee_name}: failed - {e}")
                    import traceback
                    traceback.print_exc()
            
            # Save embeddings cache
            if self.embeddings_cache_file:
                try:
                    print(f"🔄 DEBUG: Saving cache to {self.embeddings_cache_file}")
                    with open(self.embeddings_cache_file, 'wb') as f:
                        pickle.dump(self.embeddings_cache, f)
                    print(f"✅ Cache saved")
                except Exception as e:
                    print(f"❌ Cache save failed: {e}")
            
            print(f"📊 KNOWN FACES COUNT: {len(self.embeddings_cache)}")
            if self.embeddings_cache:
                print(f"📝 KNOWN NAMES: {list(self.embeddings_cache.keys())}")
                for name in self.embeddings_cache.keys():
                    print(f"   ✓ {name}")
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            import traceback
            traceback.print_exc()
    
    def detect_faces(self, frame):
        """
        Detect faces in frame using OpenCV (faster than DeepFace)
        
        Returns:
            {
                'face_count': int,
                'faces': list of face bounding boxes
            }
        """
        try:
            print(f"🔍 DEBUG: detect_faces() called, frame shape: {frame.shape}")
            
            # Use OpenCV Haar Cascade for fast detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            print(f"🔍 DEBUG: Loading cascade from {cascade_path}")
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if face_cascade.empty():
                print(f"❌ ERROR: Cascade classifier is empty!")
                return {'face_count': 0, 'faces': []}
            
            print(f"✅ Cascade loaded successfully")
            
            # Convert to grayscale
            print(f"🔍 DEBUG: Converting frame to grayscale...")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            print(f"🔍 DEBUG: Gray frame shape: {gray.shape}")
            
            # Detect faces with multiple scale factors for robustness
            # Try aggressive detection first (lower minNeighbors = more detections)
            print(f"🔍 DEBUG: Running detectMultiScale with aggressive settings...")
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,  # More granular scale steps
                minNeighbors=3,    # Lower threshold for more detections
                minSize=(20, 20)   # Detect smaller faces
            )
            print(f"🔍 DEBUG: detectMultiScale (aggressive) returned {len(faces)} faces")
            
            # If no faces found, try with standard settings
            if len(faces) == 0:
                print(f"🔍 DEBUG: No faces with aggressive settings, trying standard...")
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(30, 30)
                )
                print(f"🔍 DEBUG: detectMultiScale (standard) returned {len(faces)} faces")
            
            # If still no faces, try DeepFace detection as fallback
            if len(faces) == 0 and self.deepface:
                print(f"🔍 DEBUG: No faces with cascade, trying DeepFace...")
                try:
                    df_results = self.deepface.extract_faces(frame, enforce_detection=False)
                    print(f"🔍 DEBUG: DeepFace found {len(df_results)} faces")
                    for face_data in df_results:
                        # Convert DeepFace format to our format
                        x, y, w, h = (
                            int(face_data['x']),
                            int(face_data['y']),
                            int(face_data['w']),
                            int(face_data['h'])
                        )
                        faces = np.append(faces, [[x, y, w, h]], axis=0)
                    print(f"🔍 DEBUG: Total faces after DeepFace: {len(faces)}")
                except Exception as e:
                    print(f"⚠️ DeepFace fallback failed: {e}")
            
            face_boxes = []
            for idx, (x, y, w, h) in enumerate(faces):
                print(f"🔍 DEBUG: Face {idx}: x={x}, y={y}, w={w}, h={h}")
                face_boxes.append({
                    'x1': int(x),
                    'y1': int(y),
                    'x2': int(x + w),
                    'y2': int(y + h),
                    'center_x': int(x + w/2),
                    'center_y': int(y + h/2)
                })
            
            print(f"✅ DETECT_FACES: Found {len(face_boxes)} faces")
            return {
                'face_count': len(face_boxes),
                'faces': face_boxes
            }
        except Exception as e:
            print(f"❌ FACE DETECTION ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'face_count': 0, 'faces': []}
    
    def _preprocess_face(self, face_crop):
        """Preprocess face image to handle lighting and size variations"""
        try:
            # Ensure the image is in the right format for DeepFace
            if len(face_crop.shape) == 2:  # Grayscale
                face_crop = cv2.cvtColor(face_crop, cv2.COLOR_GRAY2BGR)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for lighting normalization
            lab = cv2.cvtColor(face_crop, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge([l, a, b])
            face_crop = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Normalize pixel values
            face_crop = face_crop.astype('float32') / 255.0
            face_crop = (face_crop - 0.5) * 2.0  # Normalize to [-1, 1]
            
            # Convert back to uint8 for DeepFace
            face_crop = ((face_crop + 1.0) * 127.5).astype('uint8')
            
            return face_crop
        except Exception as e:
            print(f"⚠️  Preprocessing failed: {e}, using original crop")
            return face_crop
    
    def recognize_faces(self, frame):
        """
        Recognize faces in frame using embeddings with cosine distance threshold
        
        Returns:
            {
                'recognized': list of names,
                'unknown_count': int,
                'registered_faces_count': int
            }
        """
        print("\n🔍 DEBUG: recognize_faces() called")
        self._ensure_deepface()
        print(f"🔍 DEBUG: Cache size={len(self.embeddings_cache)}, Names={list(self.embeddings_cache.keys())}")
        
        # If no registered faces, skip recognition
        if not self.embeddings_cache:
            print("🔍 DEBUG: No registered faces!")
            face_count = self.detect_faces(frame)['face_count']
            print(f"🔍 DEBUG: Detected {face_count} faces but no registered faces to match against")
            return {
                'recognized': [],
                'unknown_count': face_count,
                'registered_faces_count': 0
            }
        
        try:
            # Detect faces in current frame
            print(f"🔍 DEBUG: Detecting faces...")
            face_detections = self.detect_faces(frame)
            face_boxes = face_detections['faces']
            print(f"🔍 DEBUG: Found {len(face_boxes)} faces")
            
            if not face_boxes:
                print(f"🔍 DEBUG: No faces detected")
                return {
                    'recognized': [],
                    'unknown_count': 0,
                    'registered_faces_count': len(self.embeddings_cache)
                }
            
            recognized = []
            
            # Generate embeddings for detected faces
            for idx, face_box in enumerate(face_boxes):
                print(f"\n🔍 DEBUG: Face {idx+1}/{len(face_boxes)}")
                try:
                    # Crop face region
                    x1 = max(0, face_box['x1'])
                    y1 = max(0, face_box['y1'])
                    x2 = min(frame.shape[1], face_box['x2'])
                    y2 = min(frame.shape[0], face_box['y2'])
                    print(f"🔍 DEBUG: Box=({x1},{y1})-({x2},{y2}), Size={x2-x1}x{y2-y1}")
                    
                    # Skip if face region is too small
                    if (x2 - x1) < 20 or (y2 - y1) < 20:
                        print(f"🔍 DEBUG: Face too small, skipping")
                        continue
                    
                    face_crop = frame[y1:y2, x1:x2]
                    print(f"🔍 DEBUG: Generating embedding...")
                    
                    # Preprocess face crop for better recognition
                    face_crop = self._preprocess_face(face_crop)
                    
                    # Generate embedding for this face
                    face_embedding = self.deepface.represent(
                        face_crop,
                        model_name='Facenet512',
                        enforce_detection=False
                    )[0]['embedding']
                    
                    # Normalize embedding to unit vector for better cosine distance
                    face_embedding = np.array(face_embedding)
                    face_embedding = face_embedding / (np.linalg.norm(face_embedding) + 1e-8)
                    
                    print(f"🔍 DEBUG: Embedding shape={len(face_embedding)}")
                    
                    # Find best match in registered embeddings
                    best_match = None
                    best_distance = float('inf')
                    
                    print(f"🔍 DEBUG: Comparing to {len(self.embeddings_cache)} registered faces...")
                    for employee_name, registered_embedding in self.embeddings_cache.items():
                        # Ensure embeddings have same dimensions
                        reg_emb = np.array(registered_embedding)
                        
                        # Normalize registered embedding if not already normalized
                        if np.linalg.norm(reg_emb) > 1.1:  # Check if normalized
                            reg_emb = reg_emb / (np.linalg.norm(reg_emb) + 1e-8)
                        
                        # Calculate cosine distance
                        distance = cosine(face_embedding, reg_emb)
                        print(f"🔍 DEBUG: vs {employee_name}: distance={distance:.4f}")
                        
                        if distance < best_distance:
                            best_distance = distance
                            best_match = employee_name
                    
                    print(f"🔍 DEBUG: Best={best_match} (distance={best_distance:.4f}, threshold={self.face_distance_threshold})")
                    
                    # Check if distance is below threshold
                    if best_distance <= self.face_distance_threshold and best_match:
                        recognized.append(best_match)
                        print(f"✅ RECOGNIZED: {best_match}")
                    else:
                        print(f"❓ UNKNOWN FACE (distance={best_distance:.4f} > threshold={self.face_distance_threshold})")
                        
                except Exception as e:
                    print(f"❌ ERROR processing face: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            result = {
                'recognized': recognized,
                'unknown_count': max(0, len(face_boxes) - len(recognized)),
                'registered_faces_count': len(self.embeddings_cache)
            }
            print(f"\n✅ RECOGNITION RESULT: recognized={result['recognized']}, unknown={result['unknown_count']}")
            return result
        except Exception as e:
            print(f"❌ FACE RECOGNITION ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'recognized': [],
                'unknown_count': self.detect_faces(frame)['face_count'],
                'registered_faces_count': len(self.embeddings_cache)
            }
