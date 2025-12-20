"""
Module 4: People Counting & Occupancy Analytics
FastAPI Endpoints for Real-time and Historical Occupancy Data
Author: Factory Safety Detection Team
Date: 2025
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
import logging

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .occupancy_models import (
    Camera, VirtualLine, OccupancyLog, HourlyOccupancy, DailyOccupancy, MonthlyOccupancy,
    OccupancyAlert, LineDirection, OccupancyAlertType,
    CameraDAO, VirtualLineDAO, OccupancyLogDAO, HourlyOccupancyDAO, DailyOccupancyDAO,
    MonthlyOccupancyDAO, OccupancyAlertDAO
)
from .occupancy_service import OccupancyService, TimeSeriesAggregator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/occupancy", tags=["occupancy"])

# Global service instance (would be injected in production)
occupancy_service: Optional[OccupancyService] = None


# ============================================================================
# Request/Response Schemas
# ============================================================================

class CameraCreate(BaseModel):
    """Create camera request"""
    camera_id: str = Field(..., description="Unique camera identifier")
    camera_name: str = Field(..., description="Display name for camera")
    location: Optional[str] = Field(None, description="Physical location")
    camera_type: Optional[str] = Field("bidirectional", description="entry_only, exit_only, or bidirectional")
    max_occupancy: Optional[int] = Field(None, description="Maximum capacity for this area")
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None


class CameraResponse(BaseModel):
    """Camera response"""
    id: int
    camera_id: str
    camera_name: str
    location: Optional[str]
    camera_type: Optional[str]
    is_active: bool
    max_occupancy: Optional[int]

    class Config:
        from_attributes = True


class VirtualLineCreate(BaseModel):
    """Create virtual line request"""
    camera_id: int = Field(..., description="Camera database ID")
    line_name: str = Field(..., description="Name for this line")
    x1: int = Field(..., description="Start X coordinate (pixels)")
    y1: int = Field(..., description="Start Y coordinate (pixels)")
    x2: int = Field(..., description="End X coordinate (pixels)")
    y2: int = Field(..., description="End Y coordinate (pixels)")
    direction: str = Field("bidirectional", description="entry, exit, or bidirectional")
    confidence_threshold: float = Field(0.5, description="Min confidence for crossing")


class VirtualLineResponse(BaseModel):
    """Virtual line response"""
    id: int
    camera_id: int
    line_name: str
    x1: int
    y1: int
    x2: int
    y2: int
    direction: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OccupancyLiveResponse(BaseModel):
    """Current occupancy response"""
    camera_id: int
    current_occupancy: int
    total_entries: int
    total_exits: int
    unique_persons: int
    last_updated: datetime


class OccupancyLogResponse(BaseModel):
    """Occupancy log response"""
    id: int
    camera_id: int
    entry_count: int
    exit_count: int
    net_occupancy: int
    timestamp: datetime
    tracked_persons: int

    class Config:
        from_attributes = True


class HourlyOccupancyResponse(BaseModel):
    """Hourly occupancy response"""
    hour: str
    camera_id: int
    entries: int
    exits: int
    avg_occupancy: float
    peak_occupancy: int
    unique_persons: int

    class Config:
        from_attributes = True


class DailyOccupancyResponse(BaseModel):
    """Daily occupancy response"""
    date: str
    camera_id: int
    entries: int
    exits: int
    avg_occupancy: float
    peak_occupancy: int
    peak_hour: Optional[int]
    unique_persons: int

    class Config:
        from_attributes = True


class MonthlyOccupancyResponse(BaseModel):
    """Monthly occupancy response"""
    period: str
    camera_id: int
    entries: int
    exits: int
    avg_daily_occupancy: float
    peak_occupancy: int
    unique_persons: int

    class Config:
        from_attributes = True


class FacilityOccupancyResponse(BaseModel):
    """Facility-wide occupancy response"""
    facility_occupancy: int
    total_entries_all_cameras: int
    total_exits_all_cameras: int
    cameras_active: int
    last_updated: datetime


class OccupancyAlertResponse(BaseModel):
    """Occupancy alert response"""
    id: int
    camera_id: int
    alert_type: str
    current_occupancy: Optional[int]
    message: str
    is_resolved: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class ManualCalibrationRequest(BaseModel):
    """Manual occupancy calibration request"""
    occupancy_value: int = Field(..., description="Manual occupancy count")
    notes: Optional[str] = None


class AggregationRequest(BaseModel):
    """Request to trigger aggregation"""
    camera_id: Optional[int] = Field(None, description="Specific camera or all if None")
    aggregation_level: str = Field("hourly", description="hourly, daily, or monthly")


class FacilityStatsResponse(BaseModel):
    """Facility statistics response"""
    total_cameras: int
    active_cameras: int
    total_persons_in_facility: int
    capacity_utilization: float
    active_alerts: int
    timestamp: datetime


# ============================================================================
# Camera Management Endpoints
# ============================================================================

@router.post("/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(camera_data: CameraCreate, session: Session = Depends(get_db)):
    """Create a new camera for occupancy tracking"""
    try:
        # Check if camera_id already exists
        existing = CameraDAO.get_by_camera_id(session, camera_data.camera_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Camera with ID '{camera_data.camera_id}' already exists"
            )

        camera = CameraDAO.create(session, camera_data.dict())
        return camera

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating camera: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating camera: {str(e)}"
        )


@router.get("/cameras", response_model=List[CameraResponse])
async def list_cameras(session: Session = Depends(get_db)):
    """Get all active cameras"""
    try:
        cameras = CameraDAO.get_all_active(session)
        return cameras
    except Exception as e:
        logger.error(f"Error listing cameras: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing cameras"
        )


@router.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: int, session: Session = Depends(get_db)):
    """Get camera details"""
    try:
        camera = CameraDAO.get_by_id(session, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        return camera
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting camera"
        )


@router.put("/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: int, update_data: CameraCreate, session: Session = Depends(get_db)):
    """Update camera configuration"""
    try:
        camera = CameraDAO.update(session, camera_id, update_data.dict(exclude_unset=True))
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        return camera
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating camera"
        )


# ============================================================================
# Virtual Line Management Endpoints
# ============================================================================

@router.post("/lines", response_model=VirtualLineResponse, status_code=status.HTTP_201_CREATED)
async def create_virtual_line(line_data: VirtualLineCreate, session: Session = Depends(get_db)):
    """Create a new virtual line for occupancy tracking"""
    try:
        # Validate camera exists
        camera = CameraDAO.get_by_id(session, line_data.camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {line_data.camera_id} not found"
            )

        line = VirtualLineDAO.create(session, line_data.dict())
        return line

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating line: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating line: {str(e)}"
        )


@router.get("/cameras/{camera_id}/lines", response_model=List[VirtualLineResponse])
async def get_camera_lines(camera_id: int, session: Session = Depends(get_db)):
    """Get all virtual lines for a camera"""
    try:
        lines = VirtualLineDAO.get_by_camera(session, camera_id)
        return lines
    except Exception as e:
        logger.error(f"Error getting lines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting lines"
        )


@router.get("/lines/{line_id}", response_model=VirtualLineResponse)
async def get_virtual_line(line_id: int, session: Session = Depends(get_db)):
    """Get virtual line details"""
    try:
        line = VirtualLineDAO.get_by_id(session, line_id)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Line {line_id} not found"
            )
        return line
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting line: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting line"
        )


@router.put("/lines/{line_id}", response_model=VirtualLineResponse)
async def update_virtual_line(line_id: int, update_data: VirtualLineCreate, session: Session = Depends(get_db)):
    """Update virtual line configuration"""
    try:
        line = VirtualLineDAO.update(session, line_id, update_data.dict(exclude_unset=True))
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Line {line_id} not found"
            )
        return line
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating line: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating line"
        )


# ============================================================================
# Real-time Occupancy Endpoints
# ============================================================================

@router.get("/cameras/{camera_id}/live", response_model=OccupancyLiveResponse)
async def get_live_occupancy(camera_id: int, session: Session = Depends(get_db)):
    """Get current occupancy for a camera"""
    try:
        if not occupancy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Occupancy service not initialized"
            )

        state = occupancy_service.get_occupancy_state(camera_id)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No occupancy data for camera {camera_id}"
            )

        return OccupancyLiveResponse(
            camera_id=state['camera_id'],
            current_occupancy=state['current_occupancy'],
            total_entries=state['total_entries'],
            total_exits=state['total_exits'],
            unique_persons=state['unique_persons'],
            last_updated=state['last_updated']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live occupancy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting occupancy data"
        )


@router.get("/facility/live", response_model=FacilityOccupancyResponse)
async def get_facility_occupancy():
    """Get facility-wide occupancy"""
    try:
        if not occupancy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Occupancy service not initialized"
            )

        state = occupancy_service.get_facility_state()
        return FacilityOccupancyResponse(
            facility_occupancy=state['facility_occupancy'],
            total_entries_all_cameras=state['total_entries_all_cameras'],
            total_exits_all_cameras=state['total_exits_all_cameras'],
            cameras_active=state['cameras_active'],
            last_updated=datetime.fromisoformat(state['last_updated'])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting facility occupancy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting facility occupancy"
        )


@router.post("/cameras/{camera_id}/calibrate", status_code=status.HTTP_200_OK)
async def calibrate_occupancy(camera_id: int, calibration: ManualCalibrationRequest, 
                             session: Session = Depends(get_db)):
    """Manually set occupancy (for correction after manual headcount)"""
    try:
        if not occupancy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Occupancy service not initialized"
            )

        # Verify camera exists
        camera = CameraDAO.get_by_id(session, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )

        occupancy_service.manual_calibration(camera_id, calibration.occupancy_value)

        return {
            "status": "success",
            "camera_id": camera_id,
            "occupancy_set_to": calibration.occupancy_value,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calibrating occupancy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calibrating occupancy"
        )


# ============================================================================
# Historical Data Endpoints
# ============================================================================

@router.get("/cameras/{camera_id}/logs", response_model=List[OccupancyLogResponse])
async def get_occupancy_logs(
    camera_id: int,
    hours: int = Query(24, description="Last N hours"),
    session: Session = Depends(get_db)
):
    """Get recent occupancy logs for a camera"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        logs = OccupancyLogDAO.get_time_range(session, camera_id, start_time, end_time)
        return [log.to_dict() for log in logs]

    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting occupancy logs"
        )


@router.get("/cameras/{camera_id}/hourly", response_model=List[HourlyOccupancyResponse])
async def get_hourly_occupancy(
    camera_id: int,
    days: int = Query(7, description="Last N days"),
    session: Session = Depends(get_db)
):
    """Get hourly occupancy data"""
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        hourly_records = HourlyOccupancyDAO.get_date_range(session, camera_id, start_date, end_date)
        return [record.to_dict() for record in hourly_records]

    except Exception as e:
        logger.error(f"Error getting hourly data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting hourly occupancy data"
        )


@router.get("/cameras/{camera_id}/daily", response_model=List[DailyOccupancyResponse])
async def get_daily_occupancy(
    camera_id: int,
    days: int = Query(30, description="Last N days"),
    session: Session = Depends(get_db)
):
    """Get daily occupancy data"""
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        daily_records = DailyOccupancyDAO.get_date_range(session, camera_id, start_date, end_date)
        return [record.to_dict() for record in daily_records]

    except Exception as e:
        logger.error(f"Error getting daily data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting daily occupancy data"
        )


@router.get("/cameras/{camera_id}/monthly", response_model=List[MonthlyOccupancyResponse])
async def get_monthly_occupancy(
    camera_id: int,
    months: int = Query(12, description="Last N months"),
    session: Session = Depends(get_db)
):
    """Get monthly occupancy data"""
    try:
        now = datetime.utcnow()
        end_year = now.year
        end_month = now.month

        records = []
        for i in range(months):
            month = end_month - i
            year = end_year
            while month <= 0:
                month += 12
                year -= 1

            monthly = MonthlyOccupancyDAO.create_or_update(
                session, camera_id, year, month, {}
            )
            if monthly:
                records.append(monthly.to_dict())

        return sorted(records, key=lambda x: x['period'], reverse=True)

    except Exception as e:
        logger.error(f"Error getting monthly data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting monthly occupancy data"
        )


# ============================================================================
# Alert Management Endpoints
# ============================================================================

@router.get("/alerts", response_model=List[OccupancyAlertResponse])
async def get_active_alerts(
    camera_id: Optional[int] = None,
    session: Session = Depends(get_db)
):
    """Get active occupancy alerts"""
    try:
        alerts = OccupancyAlertDAO.get_active_alerts(session, camera_id)
        return [alert.to_dict() for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting alerts"
        )


@router.put("/alerts/{alert_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_alert(alert_id: int, session: Session = Depends(get_db)):
    """Resolve an alert"""
    try:
        alert = OccupancyAlertDAO.resolve_alert(session, alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        return {
            "status": "success",
            "alert_id": alert_id,
            "resolved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resolving alert"
        )


# ============================================================================
# Aggregation and Admin Endpoints
# ============================================================================

@router.post("/aggregate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_aggregation(request: AggregationRequest, session: Session = Depends(get_db)):
    """Trigger time-series data aggregation"""
    try:
        aggregator = TimeSeriesAggregator()

        if request.aggregation_level == "hourly":
            aggregator.run_hourly_aggregation(session)
        elif request.aggregation_level == "daily":
            aggregator.run_daily_aggregation(session)
        elif request.aggregation_level == "monthly":
            aggregator.run_monthly_aggregation(session)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid aggregation level. Use: hourly, daily, or monthly"
            )

        return {
            "status": "aggregation_triggered",
            "level": request.aggregation_level,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering aggregation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error triggering aggregation"
        )


@router.get("/facility/stats", response_model=FacilityStatsResponse)
async def get_facility_stats(session: Session = Depends(get_db)):
    """Get facility statistics"""
    try:
        if not occupancy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Occupancy service not initialized"
            )

        cameras = CameraDAO.get_all_active(session)
        active_cameras = len(cameras)
        
        facility_state = occupancy_service.get_facility_state()
        total_persons = facility_state['facility_occupancy']

        # Calculate capacity utilization
        total_capacity = sum(c.max_occupancy for c in cameras if c.max_occupancy) or 1
        capacity_utilization = (total_persons / total_capacity * 100) if total_capacity > 0 else 0

        # Get active alerts
        alerts = OccupancyAlertDAO.get_active_alerts(session)
        active_alerts = len(alerts)

        return FacilityStatsResponse(
            total_cameras=len(cameras),
            active_cameras=active_cameras,
            total_persons_in_facility=total_persons,
            capacity_utilization=round(capacity_utilization, 2),
            active_alerts=active_alerts,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting facility statistics"
        )


# ============================================================================
# Initialization Function
# ============================================================================

def init_occupancy_service(db_session: Session) -> None:
    """Initialize the occupancy service - call this on app startup"""
    global occupancy_service
    try:
        occupancy_service = OccupancyService(db_session)
        logger.info("Occupancy service initialized")
    except Exception as e:
        logger.error(f"Error initializing occupancy service: {str(e)}")


async def get_db() -> Session:
    """Get database session - implement based on your DB setup"""
    # This is a placeholder - implement based on your database configuration
    # Example with SQLAlchemy:
    # from .database import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    raise NotImplementedError("Database dependency injection not configured")
