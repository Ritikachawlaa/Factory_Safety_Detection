"""
Factory Safety Detection System - FastAPI Backend
Complete backend API handling ML inference, data persistence, and configuration management
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import base64
import cv2
import numpy as np
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import uvicorn

# Import ML services
from app.services import helmet_service
from app.services import loitering_service
from app.services import production_counter_service
from app.services import attendance_service

# Initialize FastAPI app
app = FastAPI(
    title="Factory Safety Detection System",
    description="AI-powered factory safety monitoring with helmet detection, loitering detection, production counting, and attendance tracking",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Thread pool for concurrent ML inference
ml_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ML-Worker")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA STORAGE PATHS ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- PYDANTIC MODELS ---

class FrameData(BaseModel):
    frame: str  # Base64 encoded image

class HelmetDetectionResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    totalPeople: int
    compliantCount: int
    violationCount: int
    complianceRate: float

class LoiteringDetectionResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    activeGroups: int
    totalPeople: int
    alertTriggered: bool

class ProductionCounterResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    itemCount: int
    sessionDate: date

class AttendanceResponse(BaseModel):
    timestamp: datetime
    verifiedCount: int
    lastPersonSeen: str
    attendanceLog: List[str]

class Employee(BaseModel):
    id: Optional[int] = None
    employee_id: str
    first_name: str
    last_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

class SystemLog(BaseModel):
    timestamp: datetime
    log_type: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None

# --- UTILITY FUNCTIONS ---

def decode_frame(frame_data: str) -> np.ndarray:
    """Decode base64 frame to OpenCV image"""
    try:
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid frame data: {str(e)}")

def save_json_data(filename: str, data: dict):
    """Save data to JSON file"""
    file_path = DATA_DIR / filename
    existing_data = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            existing_data = json.load(f)
    existing_data.append(data)
    with open(file_path, 'w') as f:
        json.dump(existing_data, f, indent=2, default=str)

def load_json_data(filename: str) -> List[dict]:
    """Load data from JSON file"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def log_system_event(log_type: str, severity: str, message: str, details: dict = None):
    """Log system events"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "log_type": log_type,
        "severity": severity,
        "message": message,
        "details": details or {}
    }
    save_json_data("system_logs.json", log_entry)

# --- ROOT ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "message": "Factory Safety Detection System API",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "helmet_detection": "/api/status/helmet",
            "loitering_detection": "/api/status/loitering",
            "production_counter": "/api/status/counting",
            "attendance": "/api/status/attendance"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- HELMET DETECTION ENDPOINTS ---

@app.get("/api/status/helmet")
def get_helmet_status():
    """Get current helmet detection status (simple endpoint for compatibility)"""
    # This returns mock data for now - real data comes from POST /api/live/helmet/
    return {
        "totalPeople": 0,
        "compliantCount": 0,
        "violationCount": 0
    }

@app.post("/api/live/helmet/", response_model=HelmetDetectionResponse)
async def helmet_detection_live(frame_data: FrameData):
    """Process webcam frame for helmet detection"""
    try:
        frame = decode_frame(frame_data.frame)
        
        # Run ML inference
        result = helmet_service.get_helmet_detection_status(frame)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Calculate compliance rate
        total = result.get('totalPeople', 0)
        compliant = result.get('compliantCount', 0)
        compliance_rate = (compliant / total * 100) if total > 0 else 0.0
        
        # Save to storage
        detection_record = {
            "timestamp": datetime.now().isoformat(),
            "total_people": result['totalPeople'],
            "compliant_count": result['compliantCount'],
            "violation_count": result['violationCount'],
            "compliance_rate": compliance_rate
        }
        save_json_data("helmet_detections.json", detection_record)
        
        # Log violations
        if result['violationCount'] > 0:
            log_system_event(
                "helmet",
                "warning",
                f"Helmet violation detected: {result['violationCount']} person(s)",
                result
            )
        
        return HelmetDetectionResponse(
            timestamp=datetime.now(),
            totalPeople=result['totalPeople'],
            compliantCount=result['compliantCount'],
            violationCount=result['violationCount'],
            complianceRate=compliance_rate
        )
        
    except Exception as e:
        log_system_event("helmet", "error", f"Helmet detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/helmet/")
def get_helmet_stats():
    """Get helmet detection statistics"""
    data = load_json_data("helmet_detections.json")
    return {
        "total_records": len(data),
        "latest_detection": data[-1] if data else None,
        "recent_detections": data[-10:] if data else []
    }

@app.get("/api/helmet-detection/")
def get_helmet_records(limit: int = 10):
    """Get historical helmet detection records"""
    data = load_json_data("helmet_detections.json")
    return data[-limit:] if data else []

# --- LOITERING DETECTION ENDPOINTS ---

@app.get("/api/status/loitering")
def get_loitering_status():
    """Get current loitering detection status"""
    return {"activeGroups": 0, "totalPeople": 0}

@app.post("/api/live/loitering/", response_model=LoiteringDetectionResponse)
async def loitering_detection_live(frame_data: FrameData):
    """Process webcam frame for loitering detection"""
    try:
        frame = decode_frame(frame_data.frame)
        
        # Run ML inference
        result = loitering_service.get_loitering_status(frame)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        alert_triggered = result.get('activeGroups', 0) > 0
        
        # Save to storage
        detection_record = {
            "timestamp": datetime.now().isoformat(),
            "active_groups": result['activeGroups'],
            "total_people": result.get('totalPeople', 0),
            "alert_triggered": alert_triggered
        }
        save_json_data("loitering_detections.json", detection_record)
        
        # Log alerts
        if alert_triggered:
            log_system_event(
                "loitering",
                "warning",
                f"Loitering detected: {result['activeGroups']} group(s)",
                result
            )
        
        return LoiteringDetectionResponse(
            timestamp=datetime.now(),
            activeGroups=result['activeGroups'],
            totalPeople=result.get('totalPeople', 0),
            alertTriggered=alert_triggered
        )
        
    except Exception as e:
        log_system_event("loitering", "error", f"Loitering detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/loitering/")
def get_loitering_stats():
    """Get loitering detection statistics"""
    data = load_json_data("loitering_detections.json")
    return {
        "total_records": len(data),
        "latest_detection": data[-1] if data else None,
        "recent_detections": data[-10:] if data else []
    }

# --- PRODUCTION COUNTER ENDPOINTS ---

@app.get("/api/status/counting")
def get_production_counting_status():
    """Get current production count"""
    return {"itemCount": production_counter_service.production_count}

@app.post("/api/live/production/", response_model=ProductionCounterResponse)
async def production_counter_live(frame_data: FrameData):
    """Process webcam frame for production counting"""
    try:
        frame = decode_frame(frame_data.frame)
        
        # Run ML inference
        result = production_counter_service.get_production_count(frame)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Save to storage
        counter_record = {
            "timestamp": datetime.now().isoformat(),
            "item_count": result['itemCount'],
            "session_date": date.today().isoformat()
        }
        save_json_data("production_counts.json", counter_record)
        
        return ProductionCounterResponse(
            timestamp=datetime.now(),
            itemCount=result['itemCount'],
            sessionDate=date.today()
        )
        
    except Exception as e:
        log_system_event("production", "error", f"Production counter error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/live/production/reset/")
def reset_production_counter():
    """Reset production counter"""
    try:
        from app.services.production_counter_service import reset_production_count
        result = reset_production_count()
        log_system_event("production", "info", "Production counter reset")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/production/today/")
def get_production_today():
    """Get today's production summary"""
    data = load_json_data("production_counts.json")
    today = date.today().isoformat()
    today_records = [r for r in data if r.get("session_date") == today]
    total = today_records[-1]["item_count"] if today_records else 0
    return {
        "date": today,
        "total_items": total,
        "records": today_records
    }

# --- ATTENDANCE SYSTEM ENDPOINTS ---

@app.get("/api/status/attendance")
def get_attendance_status_simple():
    """Get current attendance status (simple endpoint for compatibility)"""
    return {
        "verifiedCount": 0,
        "lastPersonSeen": "---",
        "attendanceLog": []
    }

@app.post("/api/live/attendance/", response_model=AttendanceResponse)
async def attendance_system_live(frame_data: FrameData):
    """Process webcam frame for attendance/face recognition"""
    try:
        frame = decode_frame(frame_data.frame)
        
        # Run ML inference
        result = attendance_service.get_attendance_status(frame)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return AttendanceResponse(
            timestamp=datetime.now(),
            verifiedCount=result['verifiedCount'],
            lastPersonSeen=result['lastPersonSeen'],
            attendanceLog=result['attendanceLog']
        )
        
    except Exception as e:
        log_system_event("attendance", "error", f"Attendance system error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/attendance/")
def get_attendance_stats():
    """Get attendance statistics"""
    # Return current in-memory state from attendance service
    return {
        "verified_count": len(attendance_service.logged_today),
        "last_person_seen": attendance_service.last_person_seen,
        "attendance_log": attendance_service.attendance_log
    }

# --- EMPLOYEE MANAGEMENT ENDPOINTS ---

@app.get("/api/employees/")
def list_employees():
    """List all employees"""
    data = load_json_data("employees.json")
    return data

@app.post("/api/employees/")
def create_employee(employee: Employee):
    """Create new employee"""
    employees = load_json_data("employees.json")
    employee_dict = employee.dict()
    employee_dict["id"] = len(employees) + 1
    employee_dict["created_at"] = datetime.now().isoformat()
    save_json_data("employees.json", employee_dict)
    return employee_dict

@app.get("/api/employees/{employee_id}")
def get_employee(employee_id: int):
    """Get employee by ID"""
    employees = load_json_data("employees.json")
    for emp in employees:
        if emp.get("id") == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

@app.get("/api/employees/search/")
def search_employees(q: str):
    """Search employees by name or employee_id"""
    employees = load_json_data("employees.json")
    results = [emp for emp in employees if 
               q.lower() in emp.get("first_name", "").lower() or
               q.lower() in emp.get("last_name", "").lower() or
               q.lower() in emp.get("employee_id", "").lower()]
    return results

# --- SYSTEM LOGS ENDPOINTS ---

@app.get("/api/system-logs/")
def get_system_logs(limit: int = 50):
    """Get system logs"""
    logs = load_json_data("system_logs.json")
    return logs[-limit:] if logs else []

# --- CONFIGURATION ENDPOINTS ---

@app.get("/api/config/system/")
def get_system_config():
    """Get system configuration"""
    config_file = DATA_DIR / "system_config.json"
    if not config_file.exists():
        return {}
    with open(config_file, 'r') as f:
        return json.load(f)

@app.post("/api/config/system/")
def update_system_config(config: Dict[str, Any]):
    """Update system configuration"""
    config_file = DATA_DIR / "system_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    return config

@app.get("/api/config/modules/")
def get_module_config():
    """Get module configuration"""
    config_file = DATA_DIR / "module_config.json"
    if not config_file.exists():
        return {}
    with open(config_file, 'r') as f:
        return json.load(f)

@app.post("/api/config/modules/")
def update_module_config(config: Dict[str, Any]):
    """Update module configuration"""
    config_file = DATA_DIR / "module_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    return config

# --- VIOLATIONS ENDPOINTS ---

@app.get("/api/violations/helmet/")
def get_helmet_violations():
    """Get helmet violations"""
    data = load_json_data("helmet_detections.json")
    violations = [d for d in data if d.get("violation_count", 0) > 0]
    return violations[-20:] if violations else []

@app.get("/api/violations/loitering/")
def get_loitering_violations():
    """Get loitering alerts"""
    data = load_json_data("loitering_detections.json")
    alerts = [d for d in data if d.get("alert_triggered", False)]
    return alerts[-20:] if alerts else []

# --- STARTUP EVENT ---

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("=" * 60)
    print("Factory Safety Detection System - FastAPI Backend")
    print("=" * 60)
    print("✅ Server started successfully")
    print(f"📁 Data directory: {DATA_DIR}")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print(f"🔧 Alternative docs: http://localhost:8000/redoc")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    log_system_event("system", "info", "System started successfully")

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )