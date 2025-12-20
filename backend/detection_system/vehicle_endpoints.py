"""
Vehicle & Gate Management FastAPI Endpoints
Provides HTTP API for vehicle detection, ANPR, access logging, and reporting.

Endpoints:
- POST /api/module2/process-frame - Process single frame
- POST /api/module2/vehicle/register - Register new vehicle
- GET /api/module2/vehicles - List vehicles
- GET /api/module2/vehicles/{id} - Get vehicle details
- PUT /api/module2/vehicles/{id}/status - Update vehicle status
- GET /api/module2/access-logs - Query access logs
- GET /api/module2/access-logs/daily-summary - Daily statistics
- GET /api/module2/access-logs/monthly-summary - Monthly statistics
- POST /api/module2/access-logs/{id}/flag - Flag entry for review
- GET /api/module2/alerts - Get recent gate alerts
- GET /api/module2/statistics - Get real-time statistics
- GET /api/module2/health - Service health check
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import base64
import cv2
import numpy as np
from io import BytesIO

# Import service components
from backend.services.vehicle_gate_service import (
    VehicleGateService, VehicleType, PlateStatus, GateAlertType, FrameGateAlert
)
from backend.detection_system.vehicle_models import (
    AuthorizedVehicle, VehicleAccessLog, AuthorizedVehicleDAO, 
    VehicleAccessLogDAO, VehicleStatus, VehicleCategory, AccessStatus,
    create_session, create_tables
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/module2", tags=["module2_vehicle_gate"])

# Global service instance (should be initialized once at app startup)
vehicle_service: Optional[VehicleGateService] = None
db_session = None


# ==================== Pydantic Models ====================

class VehicleRegisterRequest(BaseModel):
    """Request to register new authorized vehicle."""
    plate_number: str = Field(..., min_length=3, max_length=20, description="License plate")
    owner_name: str = Field(..., min_length=1, max_length=255, description="Owner/company name")
    owner_email: Optional[str] = Field(None, description="Contact email")
    vehicle_type: str = Field(..., description="Vehicle type: car, truck, bike, bus, forklift")
    vehicle_model: Optional[str] = Field(None, description="Vehicle make/model")
    category: str = Field(default="vendor", description="Owner category: employee, vendor, guest, contractor")
    department: Optional[str] = Field(None, description="Department/division")
    phone_number: Optional[str] = Field(None, description="Contact phone")
    notes: Optional[str] = Field(None, description="Additional notes")
    status: str = Field(default="allowed", description="Status: allowed, blocked, pending_review")
    
    @validator('vehicle_type')
    def validate_vehicle_type(cls, v):
        valid_types = ['car', 'truck', 'bike', 'bus', 'forklift']
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid vehicle type. Must be one of: {valid_types}")
        return v.lower()
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['allowed', 'blocked', 'pending_review', 'suspended']
        if v.lower() not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v.lower()


class VehicleResponse(BaseModel):
    """Response model for vehicle information."""
    id: int
    plate_number: str
    owner_name: str
    owner_email: Optional[str]
    vehicle_type: str
    vehicle_model: Optional[str]
    status: str
    category: str
    department: Optional[str]
    phone_number: Optional[str]
    is_active: bool
    last_access: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VehicleStatusUpdateRequest(BaseModel):
    """Request to update vehicle status."""
    status: str = Field(..., description="New status: allowed, blocked, pending_review, suspended")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['allowed', 'blocked', 'pending_review', 'suspended']
        if v.lower() not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v.lower()


class ProcessFrameRequest(BaseModel):
    """Request to process video frame."""
    frame_base64: str = Field(..., description="Frame encoded in base64")
    frame_index: int = Field(default=0, description="Frame counter")
    
    @validator('frame_base64')
    def validate_frame(cls, v):
        if not v or len(v) < 100:
            raise ValueError("Invalid frame data")
        return v


class ProcessFrameResponse(BaseModel):
    """Response from frame processing."""
    frame_index: int
    vehicles_detected: int
    vehicles_tracked: int
    plates_recognized: int
    alerts_triggered: int
    vehicle_counts: Dict[str, int]
    recent_alerts: List[Dict[str, Any]]
    processing_time_ms: float


class VehicleAccessLogResponse(BaseModel):
    """Response model for access log."""
    id: int
    plate_number: str
    vehicle_type: str
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_seconds: Optional[int]
    status: str
    category: str
    is_authorized: bool
    plate_confidence: float
    flagged: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class AccessLogFlagRequest(BaseModel):
    """Request to flag access log entry."""
    notes: Optional[str] = Field(None, description="Flag notes")


class GateAlertResponse(BaseModel):
    """Response model for gate alerts."""
    alert_type: str
    track_id: int
    vehicle_type: str
    plate_number: Optional[str]
    status: str
    timestamp: datetime
    confidence: float
    message: str


class DailySummaryResponse(BaseModel):
    """Daily traffic summary."""
    date: str
    total_vehicles: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    authorized_count: int
    blocked_count: int
    unknown_count: int
    peak_hour: Optional[str]
    peak_hour_count: int


class MonthlySummaryResponse(BaseModel):
    """Monthly traffic summary."""
    period: str
    total_vehicles: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    daily_average: float
    authorized_count: int
    blocked_count: int
    unknown_count: int
    employee_vehicles: int
    vendor_vehicles: int


class StatisticsResponse(BaseModel):
    """Service statistics."""
    frame_count: int
    total_vehicles_detected: int
    total_plates_recognized: int
    active_sessions: int
    vehicle_counts: Dict[str, int]
    pending_alerts: int
    ocr_engine: str
    uptime_seconds: float


class HealthResponse(BaseModel):
    """Service health check."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


# ==================== Dependency Injection ====================

def get_vehicle_service() -> VehicleGateService:
    """Get vehicle service instance."""
    global vehicle_service
    if vehicle_service is None:
        raise HTTPException(status_code=503, detail="Vehicle service not initialized")
    return vehicle_service


def get_db_session():
    """Get database session."""
    global db_session
    if db_session is None:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    return db_session


def get_authorized_plates() -> Dict[str, Dict[str, str]]:
    """Get all authorized plates from database."""
    try:
        session = get_db_session()
        dao = AuthorizedVehicleDAO(session)
        return dao.get_all_authorized()
    except Exception as e:
        logger.error(f"Error fetching authorized plates: {e}")
        return {}


# ==================== Endpoints ====================

@router.post("/process-frame", response_model=ProcessFrameResponse)
async def process_frame(
    request: ProcessFrameRequest,
    service: VehicleGateService = Depends(get_vehicle_service)
) -> ProcessFrameResponse:
    """
    Process a single video frame for vehicle detection and ANPR.
    
    - Detects vehicles using YOLO
    - Tracks vehicles using ByteTrack
    - Triggers ANPR when vehicle enters gate zone
    - Checks authorization and generates alerts
    - Saves snapshots for blocked/unknown vehicles
    """
    try:
        import time
        start_time = time.time()
        
        # Decode base64 frame
        try:
            frame_bytes = base64.b64decode(request.frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise HTTPException(status_code=400, detail="Invalid frame data")
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            raise HTTPException(status_code=400, detail="Failed to decode frame")
        
        # Process frame
        sessions, alerts = service.process_frame(
            frame, 
            request.frame_index,
            get_authorized_plates
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Format response
        alert_list = []
        for alert in alerts[-10:]:  # Last 10 alerts
            alert_list.append({
                'alert_type': alert.alert_type.value,
                'track_id': alert.track_id,
                'vehicle_type': alert.vehicle_type.value,
                'plate_number': alert.plate_number,
                'timestamp': alert.timestamp.isoformat(),
                'confidence': alert.confidence,
                'message': alert.message,
            })
        
        return ProcessFrameResponse(
            frame_index=request.frame_index,
            vehicles_detected=len(sessions),
            vehicles_tracked=len(sessions),
            plates_recognized=service.total_plates_recognized,
            alerts_triggered=len(alerts),
            vehicle_counts=service.get_vehicle_counts(),
            recent_alerts=alert_list,
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        raise HTTPException(status_code=500, detail=f"Frame processing failed: {str(e)}")


@router.post("/vehicle/register", response_model=VehicleResponse)
async def register_vehicle(
    request: VehicleRegisterRequest,
    session = Depends(get_db_session)
) -> VehicleResponse:
    """Register a new authorized vehicle."""
    try:
        # Check if plate already exists
        dao = AuthorizedVehicleDAO(session)
        existing = dao.get_by_plate(request.plate_number)
        if existing:
            raise HTTPException(status_code=400, detail="Plate already registered")
        
        # Create vehicle
        vehicle = dao.create(
            plate_number=request.plate_number,
            owner_name=request.owner_name,
            owner_email=request.owner_email,
            vehicle_type=request.vehicle_type,
            vehicle_model=request.vehicle_model,
            category=request.category,
            department=request.department,
            phone_number=request.phone_number,
            notes=request.notes,
            status=request.status,
        )
        
        if not vehicle:
            raise HTTPException(status_code=500, detail="Failed to register vehicle")
        
        return VehicleResponse.model_validate(vehicle)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    session = Depends(get_db_session)
) -> List[VehicleResponse]:
    """List authorized vehicles with optional filters."""
    try:
        dao = AuthorizedVehicleDAO(session)
        
        if category:
            vehicles = dao.list_by_category(category, limit)
        elif status:
            vehicles = dao.list_by_status(status, limit)
        else:
            vehicles = session.query(AuthorizedVehicle)\
                .filter_by(is_active=True)\
                .limit(limit).all()
        
        return [VehicleResponse.model_validate(v) for v in vehicles]
    
    except Exception as e:
        logger.error(f"Error listing vehicles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list vehicles: {str(e)}")


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    session = Depends(get_db_session)
) -> VehicleResponse:
    """Get vehicle details by ID."""
    try:
        dao = AuthorizedVehicleDAO(session)
        vehicle = dao.get_by_id(vehicle_id)
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return VehicleResponse.model_validate(vehicle)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicle: {str(e)}")


@router.put("/vehicles/{vehicle_id}/status", response_model=VehicleResponse)
async def update_vehicle_status(
    vehicle_id: int,
    request: VehicleStatusUpdateRequest,
    session = Depends(get_db_session)
) -> VehicleResponse:
    """Update vehicle authorization status."""
    try:
        dao = AuthorizedVehicleDAO(session)
        vehicle = dao.get_by_id(vehicle_id)
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle.status = request.status
        if request.reason:
            vehicle.notes = f"{vehicle.notes}\n[{datetime.utcnow().isoformat()}] Status: {request.status} - {request.reason}" if vehicle.notes else f"[{datetime.utcnow().isoformat()}] Status: {request.status} - {request.reason}"
        vehicle.updated_at = datetime.utcnow()
        
        session.commit()
        return VehicleResponse.model_validate(vehicle)
    
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating vehicle status: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/access-logs", response_model=List[VehicleAccessLogResponse])
async def query_access_logs(
    status: Optional[str] = Query(None, description="Filter by status: authorized, blocked, unknown"),
    plate_number: Optional[str] = Query(None, description="Filter by plate number"),
    days: int = Query(1, ge=1, le=90, description="Days to look back"),
    limit: int = Query(100, ge=1, le=1000),
    session = Depends(get_db_session)
) -> List[VehicleAccessLogResponse]:
    """Query vehicle access logs with filters."""
    try:
        dao = VehicleAccessLogDAO(session)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        logs = dao.get_date_range(start_date, datetime.utcnow(), status)
        
        if plate_number:
            logs = [log for log in logs if log.plate_number == plate_number]
        
        return [VehicleAccessLogResponse.model_validate(log) for log in logs[:limit]]
    
    except Exception as e:
        logger.error(f"Error querying access logs: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/access-logs/daily-summary", response_model=DailySummaryResponse)
async def daily_summary(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), default today"),
    session = Depends(get_db_session)
) -> DailySummaryResponse:
    """Get daily traffic summary."""
    try:
        from backend.services.vehicle_gate_service import VehicleReportingUtility
        
        dao = VehicleAccessLogDAO(session)
        
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.utcnow()
        
        start = datetime.combine(target_date.date(), datetime.min.time())
        end = start + timedelta(days=1)
        
        logs = dao.get_date_range(start, end)
        logs_dicts = [log.to_dict() for log in logs]
        
        summary = VehicleReportingUtility.generate_daily_summary(logs_dicts, target_date)
        
        return DailySummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/access-logs/monthly-summary", response_model=MonthlySummaryResponse)
async def monthly_summary(
    year: int = Query(2025),
    month: int = Query(12, ge=1, le=12),
    session = Depends(get_db_session)
) -> MonthlySummaryResponse:
    """Get monthly traffic summary."""
    try:
        from backend.services.vehicle_gate_service import VehicleReportingUtility
        
        dao = VehicleAccessLogDAO(session)
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        logs = dao.get_date_range(start, end)
        logs_dicts = [log.to_dict() for log in logs]
        
        summary = VehicleReportingUtility.generate_monthly_summary(logs_dicts, year, month)
        
        return MonthlySummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Error generating monthly summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/access-logs/{log_id}/flag", response_model=VehicleAccessLogResponse)
async def flag_access_log(
    log_id: int,
    request: AccessLogFlagRequest,
    session = Depends(get_db_session)
) -> VehicleAccessLogResponse:
    """Flag access log entry for manual review."""
    try:
        dao = VehicleAccessLogDAO(session)
        success = dao.flag_entry(log_id, request.notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        log = dao.get_by_id(log_id)
        return VehicleAccessLogResponse.model_validate(log)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flagging entry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to flag entry: {str(e)}")


@router.get("/alerts", response_model=List[GateAlertResponse])
async def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    service: VehicleGateService = Depends(get_vehicle_service)
) -> List[GateAlertResponse]:
    """Get recent gate alerts."""
    try:
        alerts = service.get_recent_alerts(limit)
        return [
            GateAlertResponse(
                alert_type=alert.alert_type.value,
                track_id=alert.track_id,
                vehicle_type=alert.vehicle_type.value,
                plate_number=alert.plate_number,
                status=alert.alert_type.value,
                timestamp=alert.timestamp,
                confidence=alert.confidence,
                message=alert.message,
            )
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    service: VehicleGateService = Depends(get_vehicle_service)
) -> StatisticsResponse:
    """Get real-time service statistics."""
    try:
        stats = service.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Service health check."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


# ==================== Initialization ====================

def init_vehicle_module(
    database_url: str,
    model_path: str = "yolov8n.pt",
    ocr_engine: str = "easyocr",
    snapshot_dir: str = "snapshots/vehicles",
    use_gpu: bool = True
):
    """Initialize vehicle management module."""
    global vehicle_service, db_session
    
    try:
        # Initialize database
        db_session = create_session(database_url)
        if db_session is None:
            raise Exception("Failed to create database session")
        
        create_tables(db_session.get_bind())
        logger.info("✓ Database initialized")
        
        # Initialize vehicle service
        vehicle_service = VehicleGateService(
            model_path=model_path,
            ocr_engine=ocr_engine,
            snapshot_dir=snapshot_dir,
            use_gpu=use_gpu,
        )
        logger.info("✓ Vehicle service initialized")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize vehicle module: {e}")
        return False


if __name__ == "__main__":
    print("Vehicle endpoints module loaded successfully")
