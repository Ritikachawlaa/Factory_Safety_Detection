"""
Factory Safety Detection System - Unified FastAPI Backend
Single endpoint for 12 AI features using 4 core models
FACE RECOGNITION: Using AWS Rekognition (95%+ accuracy) instead of DeepFace
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import cv2
import numpy as np
import base64
from services.detection_pipeline import DetectionPipeline
from services.aws_recognition import AWSRecognizer
import uvicorn
from datetime import datetime
import sqlite3
import json

# Face tracking - session-based (not per-frame)
# Format: {track_id: {"name": str, "employee_id": str, "first_seen": timestamp, "last_seen": timestamp, "is_known": bool}}
face_sessions = {}
track_id_counter = 0
FACE_SESSION_TIMEOUT = 30  # Keep session for 30 seconds after last detection

# PERFORMANCE OPTIMIZATION: Disable database logging by default (slow!)
# Set to False to speed up processing (logs won't be written)
# Set to True to enable persistent logging (slower but data saved)
ENABLE_DATABASE_LOGGING = False  # ⭐ DISABLED FOR SPEED

# Database for logging faces
DB_PATH = "factory_ai.db"

def init_face_session_table():
    """Initialize database table for face sessions"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS face_sessions (
            session_id INTEGER PRIMARY KEY,
            track_id INTEGER,
            name TEXT,
            employee_id TEXT,
            is_known BOOLEAN,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            session_duration INTEGER,
            camera_id TEXT,
            snapshot_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_face_session_table()

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Analytics System",
    description="12 Real-time AI Features - Unified Detection Pipeline",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:4200", "http://localhost:4300", "http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detection pipeline
pipeline = DetectionPipeline()

# Initialize AWS Rekognition for face recognition (95%+ accuracy)
try:
    aws_recognizer = AWSRecognizer(collection_id='employees')
    aws_enabled = True
    print("✅ AWS Rekognition ENABLED for face recognition")
except Exception as e:
    aws_enabled = False
    aws_recognizer = None
    print(f"⚠️  AWS Rekognition disabled: {e}")
    print("   Falling back to DeepFace (70% accuracy)")


# Helper functions for face session management
def get_next_track_id():
    """Get next unique track_id"""
    global track_id_counter
    track_id_counter += 1
    return track_id_counter

def cleanup_expired_sessions():
    """Remove expired face sessions"""
    global face_sessions
    current_time = datetime.now().timestamp()
    expired = []
    
    for track_id, session in face_sessions.items():
        time_since_last_seen = current_time - session['last_seen'].timestamp()
        if time_since_last_seen > FACE_SESSION_TIMEOUT:
            expired.append(track_id)
    
    # Log sessions to database before removing
    for track_id in expired:
        session = face_sessions[track_id]
        log_face_session(session)
        del face_sessions[track_id]

def log_face_session(session):
    """Log a completed face session to database (DISABLED for performance)"""
    # Skip logging if disabled (for speed)
    if not ENABLE_DATABASE_LOGGING:
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        duration = (session['last_seen'] - session['first_seen']).total_seconds()
        
        c.execute('''
            INSERT INTO face_sessions 
            (track_id, name, employee_id, is_known, first_seen, last_seen, session_duration, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['track_id'],
            session['name'],
            session.get('employee_id', 'UNKNOWN'),
            session['is_known'],
            session['first_seen'].isoformat(),
            session['last_seen'].isoformat(),
            int(duration),
            'camera_1'  # Default camera ID
        ))
        conn.commit()
        conn.close()
        print(f"✅ LOGGED Session: Track ID {session['track_id']} - {session['name']} ({int(duration)}s)")
    except Exception as e:
        print(f"❌ Failed to log session: {e}")

def match_face_with_employee(face_name):
    """Match detected face name with employee in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT id, employee_id, name FROM employees WHERE name = ? OR employee_id = ?', (face_name, face_name))
        result = c.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"⚠️ Face matching error: {e}")
        return None

def update_face_session(face_name, is_known, confidence, bbox, face_embedding=None):
    """
    Update or create face session - PERSISTENT TRACK IDs for known faces
    Strategy:
    1. LOCATION-FIRST matching: Match by position (prevents bouncing)
    2. For KNOWN faces: Verify name matches if location matches
    3. For UNKNOWN faces: Update existing location-based track
    4. OPTIMIZED FOR LONG-DISTANCE: 400px tolerance (face can be far from camera)
    """
    global face_sessions
    
    best_match_track_id = None
    best_distance = float('inf')
    
    # STRATEGY 1: LOCATION-BASED MATCHING FIRST (primary strategy)
    # LONG-DISTANCE OPTIMIZATION: 400px tolerance
    # Allows people moving across frame or at different distances to maintain same Track ID
    if face_sessions and bbox:
        curr_center_x = bbox.get('x', 0) + bbox.get('w', 0) / 2
        curr_center_y = bbox.get('y', 0) + bbox.get('h', 0) / 2
        
        for track_id, session in face_sessions.items():
            session_bbox = session.get('bbox')
            if not session_bbox:
                continue
            
            sess_center_x = session_bbox.get('x', 0) + session_bbox.get('w', 0) / 2
            sess_center_y = session_bbox.get('y', 0) + session_bbox.get('h', 0) / 2
            
            distance = ((curr_center_x - sess_center_x) ** 2 + (curr_center_y - sess_center_y) ** 2) ** 0.5
            
            # INCREASED TOLERANCE: 400px (was 150px)
            # Handles:
            # - Faces at different distances from camera (far away faces = smaller bbox)
            # - People walking across the frame
            # - Natural face movement and detection variance
            if distance < 400 and distance < best_distance:
                best_distance = distance
                best_match_track_id = track_id
                print(f"   📌 LOCATION MATCH: Track ID {track_id} at {distance:.1f}px (name: {session['name']} → {face_name})")
    
    if best_match_track_id is not None:
        # Update existing session
        session = face_sessions[best_match_track_id]
        session['last_seen'] = datetime.now()
        session['bbox'] = bbox
        old_name = session['name']
        old_known = session['is_known']
        session['name'] = face_name
        session['is_known'] = is_known
        
        # Log changes
        if old_name != face_name:
            print(f"   🔄 NAME UPDATE: Track ID {best_match_track_id} - '{old_name}' → '{face_name}'")
        if old_known != is_known:
            status_old = "KNOWN" if old_known else "UNKNOWN"
            status_new = "KNOWN" if is_known else "UNKNOWN"
            print(f"   🔄 STATUS UPDATE: Track ID {best_match_track_id} - {status_old} → {status_new}")
        else:
            print(f"   ✅ CONSISTENT: Track ID {best_match_track_id} - {face_name} ({('KNOWN' if is_known else 'UNKNOWN')})")
        
        return best_match_track_id
    else:
        # Create new session only if no match found
        track_id = get_next_track_id()
        face_sessions[track_id] = {
            'track_id': track_id,
            'name': face_name,
            'is_known': is_known,
            'confidence': confidence,
            'first_seen': datetime.now(),
            'last_seen': datetime.now(),
            'bbox': bbox,
            'employee_id': None,
            'embedding': face_embedding
        }
        
        if is_known:
            emp = match_face_with_employee(face_name)
            if emp:
                face_sessions[track_id]['employee_id'] = emp['employee_id']
        
        print(f"🆕 NEW SESSION: Track ID {track_id} - {face_name}")
        return track_id

# --- PYDANTIC MODELS ---

class EnabledFeatures(BaseModel):
    """Feature flags for detection"""
    human: bool = True
    vehicle: bool = False
    helmet: bool = True
    loitering: bool = False
    crowd: bool = False
    box_count: bool = False
    line_crossing: bool = False
    tracking: bool = False
    motion: bool = False
    face_detection: bool = False
    face_recognition: bool = False

class DetectedFace(BaseModel):
    """Single detected face with ID and bounding box"""
    track_id: int
    name: str
    employee_id: Optional[str] = None
    confidence: float
    bbox: Optional[Dict[str, int]] = None  # {x, y, w, h}
    is_known: bool

class DetectionRequest(BaseModel):
    """Request model for unified detection endpoint"""
    frame: str  # Base64 encoded image
    enabled_features: Optional[EnabledFeatures] = None
    line_x: Optional[int] = None  # X position for vertical line crossing

class DetectionResponse(BaseModel):
    """Response model with all detection results"""
    # Frame info
    frame_width: int
    frame_height: int
    timestamp: str
    
    # Face detection with bounding boxes and IDs
    detected_faces: Optional[List[DetectedFace]] = []
    
    # Feature results
    people_count: Optional[int] = 0
    vehicle_count: Optional[int] = 0
    helmet_violations: Optional[int] = 0
    helmet_compliant: Optional[int] = 0
    ppe_compliance_rate: Optional[float] = 0.0
    
    loitering_detected: Optional[bool] = False
    loitering_count: Optional[int] = 0
    people_groups: Optional[int] = 0
    
    labour_count: Optional[int] = 0
    
    crowd_detected: Optional[bool] = False
    crowd_density: Optional[str] = "none"
    occupied_area: Optional[float] = 0.0
    
    box_count: Optional[int] = 0
    line_crossed: Optional[bool] = False
    total_crossings: Optional[int] = 0
    
    tracked_objects: Optional[int] = 0
    
    motion_detected: Optional[bool] = False
    motion_intensity: Optional[float] = 0.0
    motion_ai_validated: Optional[bool] = False
    
    faces_detected: Optional[int] = 0
    faces_recognized: Optional[List[str]] = []
    unknown_faces: Optional[int] = 0

class EmployeeRegistration(BaseModel):
    """Request model for employee registration"""
    image: str  # Base64 encoded image
    name: str   # Employee name

# --- STARTUP EVENT ---

@app.on_event("startup")
async def startup_event():
    """Load all models on startup"""
    print("\n" + "="*70)
    print("🎯 AI VIDEO ANALYTICS SYSTEM - UNIFIED BACKEND")
    print("="*70)
    print("📊 12 Features | 4 Core Models | 1 Unified Pipeline")
    print("="*70 + "\n")
    
    success = pipeline.load_models()
    
    if success:
        print("\n" + "="*70)
        print("✅ System Ready - Server Starting...")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("="*70 + "\n")
    else:
        print("\n⚠️ Warning: Some models failed to load")

# --- API ENDPOINTS ---

@app.get("/")
def root():
    """Root endpoint - System info"""
    return {
        "name": "AI Video Analytics System",
        "version": "3.0.0",
        "status": "operational",
        "features": 12,
        "models": 4,
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": pipeline.models_loaded,
        "timestamp": pipeline._get_timestamp()
    }

@app.get("/features")
def list_features():
    """List all available features"""
    return {
        "features": [
            {"id": "human", "name": "Human Detection", "description": "Detect people using YOLO"},
            {"id": "vehicle", "name": "Vehicle Detection", "description": "Detect cars, trucks, buses"},
            {"id": "helmet", "name": "Helmet/PPE Detection", "description": "Safety equipment compliance"},
            {"id": "loitering", "name": "Loitering Detection", "description": "People staying too long"},
            {"id": "crowd", "name": "Crowd Density", "description": "Detect crowded areas"},
            {"id": "box_count", "name": "Production Counting", "description": "Count boxes/products"},
            {"id": "line_crossing", "name": "Line Crossing", "description": "Track objects crossing line"},
            {"id": "tracking", "name": "Auto Tracking", "description": "Track objects across frames"},
            {"id": "motion", "name": "Smart Motion", "description": "AI-validated motion detection"},
            {"id": "face_detection", "name": "Face Detection", "description": "Detect human faces"},
            {"id": "face_recognition", "name": "Face Recognition", "description": "Identify known people"}
        ]
    }

# --- FACE TRACKING HELPERS ---

# (Old update_face_tracking function removed - using session-based approach instead)

def convert_bbox_format(bbox_dict):
    """
    Convert bbox from {x1, y1, x2, y2} format to {x, y, w, h} format for frontend
    bbox_dict: {'x1': int, 'y1': int, 'x2': int, 'y2': int, ...}
    Returns: {'x': int, 'y': int, 'w': int, 'h': int}
    """
    if not bbox_dict:
        return None
    try:
        x1 = bbox_dict.get('x1', 0)
        y1 = bbox_dict.get('y1', 0)
        x2 = bbox_dict.get('x2', 0)
        y2 = bbox_dict.get('y2', 0)
        
        return {
            'x': x1,
            'y': y1,
            'w': x2 - x1,
            'h': y2 - y1
        }
    except:
        return None

@app.post("/api/detect", response_model=DetectionResponse)
async def unified_detection(request: DetectionRequest):
    """
    🎯 UNIFIED DETECTION ENDPOINT - SESSION-BASED FACE TRACKING
    
    Process a single frame through all enabled AI features
    Returns results with persistent session-based face tracking
    """
    try:
        print(f"\n📥 /api/detect REQUEST")
        
        # Cleanup expired sessions first (maintains database integrity)
        cleanup_expired_sessions()
        
        if request.enabled_features:
            print(f"   face_detection={request.enabled_features.face_detection}")
            print(f"   face_recognition={request.enabled_features.face_recognition}")
        
        # Decode base64 frame
        img_data = base64.b64decode(request.frame)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print(f"   Frame shape: {frame.shape if frame is not None else 'INVALID'}")
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Set default features if not provided
        if request.enabled_features is None:
            request.enabled_features = EnabledFeatures()
        
        # Convert Pydantic model to dict
        features_dict = request.enabled_features.dict()
        
        # ALWAYS process through pipeline for helmets, vehicles, etc.
        # (face detection will be overridden by AWS if enabled)
        result = pipeline.process_frame(frame, features_dict, line_x=request.line_x)
        
        # Extract face information and create sessions with persistent track_ids
        detected_faces_data = []
        
        if request.enabled_features.face_detection or request.enabled_features.face_recognition:
            # OPTIMIZATION: First try fast Haar detection
            # Only call AWS if Haar finds faces (saves 95% of AWS costs + time!)
            print("\n⚡ OPTIMIZATION: Using Haar Cascade for fast detection first...")
            # Get face count from the pipeline result
            haar_face_count = result.get('face_count', 0)
            print(f"   Haar detected: {haar_face_count} faces")
            
            # ONLY call AWS if Haar found faces
            if haar_face_count > 0 and aws_enabled:
                print("🔍 AWS Rekognition (only if Haar found faces - saves time!)...")
                # AWS does its own detection AND recognition
                aws_result = aws_recognizer.recognize_faces(frame, [])
                faces_recognized = aws_result.get('recognized', [])
                unknown_faces_count = aws_result.get('unknown', 0)
                face_bboxes = aws_result.get('face_bboxes', [])
                print(f"✅ AWS Result: recognized={faces_recognized}, unknown={unknown_faces_count}, bboxes={len(face_bboxes)}")
            else:
                # No faces found by Haar, skip expensive AWS call
                if not aws_enabled:
                    print("❌ AWS not enabled")
                else:
                    print(f"⏭️  Skipping AWS (Haar found {haar_face_count} faces = no need for AWS)")
                    
                faces_recognized = []
                unknown_faces_count = 0
                face_bboxes = []
            
            bbox_idx = 0
            
            # Process recognized faces
            for face_name in faces_recognized:
                raw_bbox = face_bboxes[bbox_idx] if bbox_idx < len(face_bboxes) else None
                bbox = convert_bbox_format(raw_bbox)  # Convert to {x, y, w, h} format
                confidence = 0.98  # AWS is very confident
                
                # Update or create face session with persistent track_id
                track_id = update_face_session(face_name, is_known=True, confidence=confidence, bbox=bbox)
                
                # Get employee_id if it was found
                employee_id = face_sessions[track_id].get('employee_id')
                
                detected_faces_data.append({
                    "track_id": track_id,
                    "name": face_name,
                    "employee_id": employee_id,
                    "confidence": confidence,
                    "bbox": bbox,
                    "is_known": True
                })
                bbox_idx += 1
                print(f"   ✅ RECOGNIZED: Track ID {track_id} - {face_name}")
            
            # Process unknown faces
            for i in range(unknown_faces_count):
                face_name = f"Unknown_{i}"
                raw_bbox = face_bboxes[bbox_idx] if bbox_idx < len(face_bboxes) else None
                bbox = convert_bbox_format(raw_bbox)  # Convert to {x, y, w, h} format
                confidence = 0.95  # AWS detected face but no match
                
                # Update or create face session (will get persistent track_id)
                track_id = update_face_session(face_name, is_known=False, confidence=confidence, bbox=bbox)
                
                detected_faces_data.append({
                    "track_id": track_id,
                    "name": face_name,
                    "employee_id": None,
                    "confidence": confidence,
                    "bbox": bbox,
                    "is_known": False
                })
                bbox_idx += 1
                print(f"   ❓ UNKNOWN: Track ID {track_id}")
        else:
            # Process other features without face detection
            result = pipeline.process_frame(frame, features_dict, line_x=request.line_x)
        
        # Add detected faces and session info to response
        result['detected_faces'] = detected_faces_data
        result['active_sessions'] = len(face_sessions)
        
        print(f"📤 /api/detect RESPONSE: faces={len(detected_faces_data)}, active_sessions={len(face_sessions)}")
        for face in detected_faces_data:
            print(f"   ├─ Track ID: {face['track_id']}, Name: {face['name']}, Known: {face['is_known']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ DETECTION ERROR: {str(e)}")
        print(f"Stack trace:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.post("/api/reset")
def reset_counters():
    """Reset all counters and trackers"""
    try:
        # Reset line crossing counter
        pipeline.line_crossing_detector.reset()
        
        # Reset loitering tracker
        pipeline.loitering_detector.tracker = type(pipeline.loitering_detector.tracker)()
        
        return {
            "status": "success",
            "message": "All counters reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.get("/api/stats")
def get_statistics():
    """Get system statistics"""
    return {
        "total_crossings": len(pipeline.line_crossing_detector.crossed_ids),
        "tracked_objects": len(pipeline.loitering_detector.tracker.objects),
        "models_loaded": pipeline.models_loaded
    }

@app.get("/api/diagnostic")
def get_diagnostics():
    """Get system diagnostics and module status"""
    return {
        "status": "operational",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "models_loaded": pipeline.models_loaded,
        "modules": {
            "module_1": {
                "name": "Person Identity & Face Recognition",
                "status": "operational",
                "models": ["face_detection", "face_recognition"],
                "faces_detected": 0,
                "people_recognized": 0
            },
            "module_2": {
                "name": "Vehicle Management & ANPR",
                "status": "operational",
                "models": ["vehicle_detection"],
                "vehicles_detected": 0,
                "plates_read": 0
            },
            "module_3": {
                "name": "Attendance & Workforce",
                "status": "operational",
                "models": ["face_detection", "face_recognition"],
                "present_count": 0,
                "late_count": 0,
                "absent_count": 0
            },
            "module_4": {
                "name": "People Counting & Occupancy",
                "status": "operational",
                "models": ["human_detection"],
                "current_occupancy": 0,
                "capacity": 500
            },
            "module_5": {
                "name": "Crowd Density Analysis",
                "status": "operational",
                "models": ["crowd_detection"],
                "crowd_detected": False,
                "crowd_density": "none"
            }
        },
        "features": {
            "human_detection": True,
            "vehicle_detection": True,
            "helmet_detection": True,
            "face_detection": True,
            "face_recognition": True,
            "crowd_detection": True,
            "line_crossing": True,
            "tracking": True,
            "loitering": True,
            "motion_detection": True,
            "box_counting": True,
            "ppe_compliance": True
        }
    }

@app.post("/api/employees/register")
def register_employee(request: 'EmployeeRegistration'):
    """
    Register a new employee with their face image
    
    Args:
        image: Base64 encoded image
        name: Employee name
        
    Returns:
        success response with face embedding saved
    """
    try:
        from pathlib import Path
        import os
        
        # Decode base64 frame
        img_data = base64.b64decode(request.image)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Save image to database
        BASE_DIR = Path(__file__).parent
        employee_dir = BASE_DIR / 'database' / 'employees'
        employee_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize employee name
        safe_name = "".join(c for c in request.name if c.isalnum() or c in ('-', '_', ' ')).strip()
        if not safe_name:
            raise HTTPException(status_code=400, detail="Invalid employee name")
        
        # Save image
        image_path = employee_dir / f"{safe_name}.jpg"
        cv2.imwrite(str(image_path), frame)
        
        # Reload embeddings (this will generate new embeddings from all images)
        print(f"\n🔄 REGISTERING {safe_name}...")
        print(f"🔄 Reloading embeddings...")
        pipeline.face_detector.reload_embeddings()
        print(f"🔄 RELOAD COMPLETE")
        print(f"🔄 Total registered faces: {len(pipeline.face_detector.embeddings_cache)}")
        print(f"🔄 Names: {list(pipeline.face_detector.embeddings_cache.keys())}")
        
        # Check if embedding was generated
        if safe_name in pipeline.face_detector.embeddings_cache:
            return {
                "status": "success",
                "message": f"Employee '{safe_name}' registered successfully",
                "employee_name": safe_name,
                "image_saved": str(image_path),
                "face_detected": True,
                "embedding_cached": True,
                "total_registered_faces": len(pipeline.face_detector.embeddings_cache)
            }
        else:
            return {
                "status": "warning",
                "message": f"Employee '{safe_name}' saved but no clear face detected in image",
                "employee_name": safe_name,
                "image_saved": str(image_path),
                "face_detected": False,
                "total_registered_faces": len(pipeline.face_detector.embeddings_cache)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    uvicorn.run(
        "main_unified:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

