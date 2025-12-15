"""
Factory Safety Detection System - Unified FastAPI Backend
Single endpoint for 12 AI features using 4 core models
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import cv2
import numpy as np
import base64
from services.detection_pipeline import DetectionPipeline
import uvicorn

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
    allow_origins=["http://localhost:4000", "http://localhost:4200", "http://localhost:4300"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detection pipeline
pipeline = DetectionPipeline()

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

@app.post("/api/detect", response_model=DetectionResponse)
async def unified_detection(request: DetectionRequest):
    """
    🎯 UNIFIED DETECTION ENDPOINT
    
    Process a single frame through all enabled AI features
    
    Returns comprehensive detection results in one response
    """
    try:
        print(f"\n📥 /api/detect REQUEST")
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
        
        # Process frame through pipeline
        result = pipeline.process_frame(frame, features_dict, line_x=request.line_x)
        print(f"📤 /api/detect RESPONSE: faces_detected={result.get('faces_detected')}")
        
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

