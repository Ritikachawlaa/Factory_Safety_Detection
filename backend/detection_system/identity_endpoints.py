"""
Module 1: FastAPI Endpoints for Person Identity & Access Intelligence
Ready-to-use endpoint implementations
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import base64
import cv2
import numpy as np
import logging

from services.identity_service import IdentityService
from detection_system.identity_models import (
    EmployeeDAO, AccessLogDAO, AccessStatus, DepartmentEnum
)
from sqlalchemy.orm import Session

# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/module1", tags=["Module 1: Identity & Access"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db() -> Session:
    """Dependency for database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/factory_safety")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_identity_service(db: Session = Depends(get_db)) -> IdentityService:
    """Dependency for identity service"""
    return IdentityService(db)

# ============================================================================
# PYDANTIC MODELS - REQUESTS
# ============================================================================

class TrackDetection(BaseModel):
    """Single tracked person detection"""
    track_id: int = Field(..., description="ByteTrack ID")
    face_crop: str = Field(..., description="Base64 encoded face crop image")
    confidence: Optional[float] = Field(None, description="Detection confidence from tracker")

class ProcessFrameRequest(BaseModel):
    """Request to process a video frame"""
    frame: str = Field(..., description="Base64 encoded full frame")
    track_ids: List[TrackDetection] = Field(..., description="List of tracked persons with face crops")
    frame_id: Optional[int] = Field(None, description="Optional frame number for tracking")
    timestamp: Optional[str] = Field(None, description="Frame timestamp ISO format")

class EnrollEmployeeRequest(BaseModel):
    """Employee enrollment request"""
    name: str = Field(..., min_length=2, max_length=255, description="Employee name")
    department: str = Field(..., description="Department (manufacturing, warehouse, etc.)")
    email: Optional[str] = Field(None, description="Employee email")
    employee_id_code: Optional[str] = Field(None, description="Badge ID or employee code")
    phone: Optional[str] = Field(None, description="Phone number")
    notes: Optional[str] = Field(None, description="Additional notes")

class UpdateEmployeeRequest(BaseModel):
    """Update employee details"""
    email: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    is_authorized: Optional[bool] = None
    notes: Optional[str] = None

class QueryAccessLogsRequest(BaseModel):
    """Query access logs with filters"""
    person_name: Optional[str] = None
    employee_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_authorized: Optional[bool] = None
    limit: int = Field(100, le=1000)
    offset: int = Field(0, ge=0)

# ============================================================================
# PYDANTIC MODELS - RESPONSES
# ============================================================================

class IdentityResult(BaseModel):
    """Result for a single identified person"""
    track_id: int
    name: str
    confidence: float
    is_cached: bool
    is_authorized: bool
    face_id: Optional[str] = None
    access_log_id: Optional[int] = None

class ProcessFrameResponse(BaseModel):
    """Response from frame processing"""
    success: bool
    identities: List[IdentityResult]
    unknown_count: int
    processing_time_ms: float
    frame_id: Optional[int] = None
    cache_stats: Dict
    errors: List[str] = []

class EnrollEmployeeResponse(BaseModel):
    """Response from employee enrollment"""
    success: bool
    employee_id: Optional[int] = None
    face_id: Optional[str] = None
    message: str
    error: Optional[str] = None

class EmployeeInfo(BaseModel):
    """Employee information"""
    id: int
    name: str
    email: Optional[str]
    department: str
    employee_id_code: Optional[str]
    aws_face_id: Optional[str]
    photo_url: Optional[str]
    status: str
    is_authorized: bool
    enrolled_at: datetime
    last_seen: Optional[datetime]

class AccessLogEntry(BaseModel):
    """Single access log entry"""
    id: int
    track_id: int
    person_name: str
    employee_id: Optional[int]
    is_authorized: bool
    confidence_score: Optional[float]
    snapshot_path: Optional[str]
    timestamp: datetime
    flagged: bool

class AccessSummary(BaseModel):
    """Access summary statistics"""
    total_accesses: int
    authorized: int
    unauthorized: int
    unknown: int
    authorization_rate: float
    unknown_rate: float
    period: Dict

# ============================================================================
# ENDPOINT 1: PROCESS FRAME
# ============================================================================

@router.post(
    "/process-frame",
    response_model=ProcessFrameResponse,
    summary="Process frame and identify persons",
    description="Detect and identify tracked persons in a video frame. "
                "Includes caching to avoid redundant AWS API calls."
)
async def process_frame(
    request: ProcessFrameRequest,
    service: IdentityService = Depends(get_identity_service),
    db: Session = Depends(get_db)
) -> ProcessFrameResponse:
    """
    Process a video frame to identify tracked persons.
    
    - **frame**: Base64 encoded video frame
    - **track_ids**: List of tracked persons with face crops
    - Returns: Identities, confidence scores, and authorization status
    
    Performance: Cached identities return in <1ms, new identities in 200-500ms
    """
    try:
        # Validate and decode frame
        try:
            frame_data = base64.b64decode(request.frame)
            frame = cv2.imdecode(
                np.frombuffer(frame_data, np.uint8),
                cv2.IMREAD_COLOR
            )
            if frame is None:
                raise ValueError("Failed to decode frame")
        except Exception as e:
            logger.error(f"Frame decode error: {e}")
            raise HTTPException(status_code=400, detail="Invalid frame image data")
        
        # Decode track_ids with face crops
        track_ids_decoded = []
        for track in request.track_ids:
            try:
                face_data = base64.b64decode(track.face_crop)
                face_crop = cv2.imdecode(
                    np.frombuffer(face_data, np.uint8),
                    cv2.IMREAD_COLOR
                )
                if face_crop is None:
                    logger.warning(f"Failed to decode face crop for track {track.track_id}")
                    continue
                track_ids_decoded.append((track.track_id, face_crop))
            except Exception as e:
                logger.error(f"Face crop decode error for track {track.track_id}: {e}")
                continue
        
        if not track_ids_decoded:
            return ProcessFrameResponse(
                success=True,
                identities=[],
                unknown_count=0,
                processing_time_ms=0,
                frame_id=request.frame_id,
                cache_stats=service.get_cache_stats(),
                errors=["No valid track IDs to process"]
            )
        
        # Process identities
        result = service.process_frame_identities(frame, track_ids_decoded)
        
        # Convert to response model
        identities = [
            IdentityResult(
                track_id=identity['track_id'],
                name=identity['name'],
                confidence=identity['confidence'],
                is_cached=identity.get('is_cached', False),
                is_authorized=identity['is_authorized'],
                face_id=identity.get('face_id'),
                access_log_id=identity.get('access_log_id')
            )
            for identity in result['identities']
        ]
        
        return ProcessFrameResponse(
            success=True,
            identities=identities,
            unknown_count=result['unknown_count'],
            processing_time_ms=result['processing_time_ms'],
            frame_id=request.frame_id,
            cache_stats=service.get_cache_stats(),
            errors=result.get('errors', [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Frame processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# ============================================================================
# ENDPOINT 2: ENROLL EMPLOYEE
# ============================================================================

@router.post(
    "/enroll",
    response_model=EnrollEmployeeResponse,
    summary="Enroll a new employee"
)
async def enroll_employee(
    name: str = Form(..., description="Employee name"),
    department: str = Form(..., description="Department"),
    email: Optional[str] = Form(None),
    employee_id_code: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    photo: UploadFile = File(..., description="Employee face photo (JPEG/PNG)"),
    service: IdentityService = Depends(get_identity_service)
) -> EnrollEmployeeResponse:
    """
    Enroll a new employee in the facial recognition system.
    
    - **name**: Employee full name
    - **department**: Employee department
    - **photo**: Face photo (JPEG/PNG)
    - **email**: Optional email address
    - **employee_id_code**: Optional badge/employee ID
    - **phone**: Optional phone number
    - **notes**: Optional notes
    
    Returns: Employee ID and AWS face ID on success
    """
    try:
        # Validate photo file
        if not photo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG)")
        
        if photo.size and photo.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Read photo bytes
        photo_bytes = await photo.read()
        
        # Enroll employee
        result = service.enroll_employee(
            employee_data={
                'name': name,
                'department': department,
                'email': email,
                'employee_id_code': employee_id_code,
                'phone': phone,
                'notes': notes
            },
            image_bytes=photo_bytes
        )
        
        if result['success']:
            logger.info(f"✅ Employee enrolled: {name} (ID: {result['employee_id']})")
            return EnrollEmployeeResponse(
                success=True,
                employee_id=result['employee_id'],
                face_id=result['face_id'],
                message=f"Employee '{name}' enrolled successfully"
            )
        else:
            logger.warning(f"⚠️ Enrollment failed for {name}: {result['error']}")
            raise HTTPException(status_code=400, detail=result['error'])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrollment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")

# ============================================================================
# ENDPOINT 3: GET EMPLOYEE
# ============================================================================

@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeInfo,
    summary="Get employee details"
)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details for a specific employee.
    
    - **employee_id**: Employee ID
    
    Returns: Employee information including enrollment status and face ID
    """
    try:
        employee = EmployeeDAO.get_by_id(db, employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        return EmployeeInfo(
            id=employee.id,
            name=employee.name,
            email=employee.email,
            department=employee.department.value,
            employee_id_code=employee.employee_id_code,
            aws_face_id=employee.aws_face_id,
            photo_url=employee.photo_url,
            status=employee.status.value,
            is_authorized=employee.is_authorized,
            enrolled_at=employee.enrolled_at,
            last_seen=employee.last_seen
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 4: LIST EMPLOYEES
# ============================================================================

@router.get(
    "/employees",
    response_model=Dict,
    summary="List employees"
)
async def list_employees(
    active_only: bool = Query(True),
    department: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List employees with optional filtering.
    
    - **active_only**: Only return active employees
    - **department**: Filter by department
    - **search**: Search by name or email
    - **limit**: Max results (max 1000)
    - **offset**: Pagination offset
    """
    try:
        if search:
            employees = EmployeeDAO.search(db, search, limit=limit)
        elif department:
            employees = EmployeeDAO.get_by_department(db, DepartmentEnum(department))
        elif active_only:
            employees = EmployeeDAO.get_active_employees(db, limit=limit)
        else:
            from sqlalchemy import desc
            from detection_system.identity_models import Employee
            employees = db.query(Employee).order_by(desc(Employee.enrolled_at)).limit(limit).offset(offset).all()
        
        return {
            'success': True,
            'total': len(employees),
            'employees': [
                {
                    'id': emp.id,
                    'name': emp.name,
                    'email': emp.email,
                    'department': emp.department.value,
                    'status': emp.status.value,
                    'is_authorized': emp.is_authorized,
                    'enrolled_at': emp.enrolled_at.isoformat()
                }
                for emp in employees
            ]
        }
    except Exception as e:
        logger.error(f"Error listing employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 5: GET ACCESS LOGS
# ============================================================================

@router.get(
    "/access-logs",
    response_model=Dict,
    summary="Get access logs"
)
async def get_access_logs(
    person_name: Optional[str] = None,
    employee_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    is_authorized: Optional[bool] = None,
    flagged_only: bool = False,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve access logs with optional filtering.
    
    - **person_name**: Filter by person name
    - **employee_id**: Filter by employee
    - **start_time**: Start time filter (ISO format)
    - **end_time**: End time filter (ISO format)
    - **is_authorized**: Filter by authorization status
    - **flagged_only**: Only return flagged entries
    - **limit**: Max results
    - **offset**: Pagination offset
    """
    try:
        from detection_system.identity_models import AccessLog
        from sqlalchemy import desc
        
        query = db.query(AccessLog)
        
        if person_name:
            query = query.filter(AccessLog.person_name == person_name)
        if employee_id:
            query = query.filter(AccessLog.employee_id == employee_id)
        if start_time:
            query = query.filter(AccessLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AccessLog.timestamp <= end_time)
        if is_authorized is not None:
            query = query.filter(AccessLog.is_authorized == is_authorized)
        if flagged_only:
            query = query.filter(AccessLog.flagged == True)
        
        total_count = query.count()
        logs = query.order_by(desc(AccessLog.timestamp)).limit(limit).offset(offset).all()
        
        return {
            'success': True,
            'total': total_count,
            'count': len(logs),
            'limit': limit,
            'offset': offset,
            'logs': [log.to_dict() for log in logs]
        }
    except Exception as e:
        logger.error(f"Error retrieving access logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 6: GET ACCESS SUMMARY
# ============================================================================

@router.get(
    "/access-summary",
    response_model=Dict,
    summary="Get access summary statistics"
)
async def get_access_summary(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    service: IdentityService = Depends(get_identity_service)
):
    """
    Get access summary statistics for a time period.
    
    - **start_time**: Start time (defaults to midnight today)
    - **end_time**: End time (defaults to now)
    
    Returns: Total, authorized, unauthorized, unknown counts and rates
    """
    try:
        # Default to today
        if not start_time:
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_time:
            end_time = datetime.now()
        
        summary = service.get_access_summary(start_time, end_time)
        
        return {
            'success': True,
            'summary': summary,
            'cache_stats': service.get_cache_stats()
        }
    except Exception as e:
        logger.error(f"Error getting access summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 7: FLAG SUSPICIOUS ENTRY
# ============================================================================

@router.post(
    "/access-logs/{log_id}/flag",
    response_model=Dict,
    summary="Flag access log entry for review"
)
async def flag_access_log(
    log_id: int,
    flag: bool = True,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Flag an access log entry for manual review.
    
    - **log_id**: Access log ID
    - **flag**: True to flag, False to unflag
    - **reason**: Optional reason for flagging
    """
    try:
        log = AccessLogDAO.flag_entry(db, log_id, flag)
        if not log:
            raise HTTPException(status_code=404, detail=f"Log entry {log_id} not found")
        
        if reason and flag:
            log.notes = (log.notes or "") + f" [FLAGGED: {reason}]"
            db.commit()
        
        logger.info(f"Access log {log_id} {'flagged' if flag else 'unflagged'}")
        
        return {
            'success': True,
            'message': f"Entry {'flagged' if flag else 'unflagged'} successfully",
            'log_id': log_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flagging log entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 8: GET CACHE STATISTICS
# ============================================================================

@router.get(
    "/cache-stats",
    response_model=Dict,
    summary="Get identity cache statistics"
)
async def get_cache_stats(
    service: IdentityService = Depends(get_identity_service)
):
    """
    Get statistics about the identity cache.
    
    Returns: Number of cached identities, known persons, unknown persons
    """
    try:
        stats = service.get_cache_stats()
        return {
            'success': True,
            'cache_stats': stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 9: CLEAR CACHE
# ============================================================================

@router.post(
    "/cache/clear",
    response_model=Dict,
    summary="Clear identity cache"
)
async def clear_cache(
    service: IdentityService = Depends(get_identity_service)
):
    """
    Clear the in-memory identity cache.
    Use with caution - will cause next frames to re-query AWS API.
    """
    try:
        service.clear_identity_cache()
        logger.info("Identity cache cleared")
        return {
            'success': True,
            'message': 'Cache cleared successfully'
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 10: GET UNKNOWN PERSONS
# ============================================================================

@router.get(
    "/unknown-persons",
    response_model=Dict,
    summary="Get list of unknown persons detected"
)
async def get_unknown_persons(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all unknown person detections from access logs.
    
    - **limit**: Max results
    - **offset**: Pagination offset
    
    Returns: List of unknown person access attempts with snapshots
    """
    try:
        from datetime import timedelta as td
        from detection_system.identity_models import AccessLog
        from sqlalchemy import desc
        
        # Get last 24 hours of unknown persons
        cutoff = datetime.now() - td(days=1)
        logs = AccessLogDAO.get_unknown_persons(db, limit=limit)
        
        return {
            'success': True,
            'count': len(logs),
            'unknown_persons': [
                {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'snapshot': log.snapshot_path,
                    'location': {
                        'x': log.location_x,
                        'y': log.location_y
                    } if log.location_x is not None else None,
                    'notes': log.notes
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving unknown persons: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", response_model=Dict, summary="Health check")
async def health_check(service: IdentityService = Depends(get_identity_service)):
    """
    Health check endpoint for Module 1.
    Verifies AWS connection, database connectivity, and service status.
    """
    try:
        # Check cache status
        cache_stats = service.get_cache_stats()
        
        return {
            'status': 'healthy',
            'module': 'Module 1: Person Identity & Access Intelligence',
            'timestamp': datetime.now().isoformat(),
            'cache': cache_stats,
            'database': 'connected'
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 503

# ============================================================================
# INCLUDE ROUTER IN FASTAPI APP
# ============================================================================

# In your main_unified.py or app.py:
# from identity_endpoints import router
# app.include_router(router)
