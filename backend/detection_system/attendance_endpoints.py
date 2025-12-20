"""
Module 3: Attendance Endpoints
FastAPI routes for attendance management, reporting, and manual overrides
Provides REST interface for attendance system operations
Author: Factory Safety Detection Team
Date: 2025
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import Optional, List, Dict
import logging

from sqlalchemy.orm import Session
from detection_system.attendance_models import (
    AttendanceStatus, CheckInOutType, ExitReason, TimeFenceEventType,
    AttendanceRecordDAO, ShiftDAO, DepartmentDAO, TimeFenceLogDAO, Employee,
    Shift, Department, AttendanceRecord, TimeFenceLog
)
from detection_system.attendance_service import (
    AttendanceService, AttendanceReportingUtility
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

# Global service instance
_attendance_service: Optional[AttendanceService] = None
_reporting_utility: Optional[AttendanceReportingUtility] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class FaceDetectionRequest(BaseModel):
    """Request model for face detection processing"""
    aws_rekognition_id: str = Field(..., description="AWS Rekognition person ID")
    camera_id: str = Field(..., description="Camera ID where face detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    is_exit: bool = Field(default=False, description="Whether this is exit detection")
    exit_reason: str = Field(default="unknown", description="Reason for exit")


class ManualOverrideRequest(BaseModel):
    """Request model for manual attendance override"""
    employee_id: int = Field(..., description="Employee ID")
    attendance_date: date = Field(..., description="Date of attendance")
    check_in_time: Optional[datetime] = Field(None, description="Override check-in time")
    check_out_time: Optional[datetime] = Field(None, description="Override check-out time")
    status: Optional[str] = Field(None, description="Override status (Present/Late/Absent/Leave/Half-day)")
    reason: str = Field(..., description="Reason for override")
    override_user: str = Field(default="admin", description="User making override")


class ShiftCreateRequest(BaseModel):
    """Request model for shift creation"""
    shift_name: str = Field(..., description="Shift name")
    start_time: time = Field(..., description="Shift start time (HH:MM:SS)")
    end_time: time = Field(..., description="Shift end time (HH:MM:SS)")
    grace_period_minutes: int = Field(default=5, description="Grace period in minutes")
    break_start: Optional[time] = Field(None, description="Break start time")
    break_end: Optional[time] = Field(None, description="Break end time")
    break_duration_minutes: int = Field(default=0, description="Break duration")
    description: Optional[str] = Field(None, description="Shift description")


class DepartmentCreateRequest(BaseModel):
    """Request model for department creation"""
    dept_name: str = Field(..., description="Department name")
    shift_id: int = Field(..., description="Shift ID")
    manager_name: Optional[str] = Field(None, description="Manager name")
    location: Optional[str] = Field(None, description="Department location")
    entry_camera_id: Optional[str] = Field(None, description="Entry camera ID")
    exit_camera_id: Optional[str] = Field(None, description="Exit camera ID")


class AttendanceRecordResponse(BaseModel):
    """Response model for attendance record"""
    id: int
    employee_id: int
    employee_name: str
    attendance_date: str
    check_in_time: Optional[str]
    check_out_time: Optional[str]
    status: str
    is_manual_override: bool
    actual_duration_minutes: Optional[int]


class ShiftResponse(BaseModel):
    """Response model for shift"""
    id: int
    shift_name: str
    start_time: str
    end_time: str
    grace_period_minutes: int
    duration_minutes: int
    is_active: bool


class DepartmentResponse(BaseModel):
    """Response model for department"""
    id: int
    dept_name: str
    shift_id: int
    manager_name: Optional[str]
    location: Optional[str]
    entry_camera_id: Optional[str]
    exit_camera_id: Optional[str]
    is_active: bool


class AttendanceSummaryResponse(BaseModel):
    """Response model for attendance summary"""
    date: str
    total_employees: int
    present: int
    late: int
    half_day: int
    absent: int
    leave: int
    currently_in_frame: int
    check_ins_today: int
    check_outs_today: int
    late_entries: int


class ReportResponse(BaseModel):
    """Generic report response"""
    success: bool
    timestamp: str
    data: Dict


# ============================================================================
# Dependency Functions
# ============================================================================

def get_attendance_service(session: Session = Depends(lambda: None)) -> AttendanceService:
    """Get attendance service instance"""
    global _attendance_service
    if _attendance_service is None:
        # Note: session parameter should be injected from FastAPI dependency
        # This is a placeholder - real implementation should pass session
        raise RuntimeError("Attendance service not initialized")
    return _attendance_service


def get_reporting_utility(session: Session = Depends(lambda: None)) -> AttendanceReportingUtility:
    """Get reporting utility instance"""
    global _reporting_utility
    if _reporting_utility is None:
        raise RuntimeError("Reporting utility not initialized")
    return _reporting_utility


# ============================================================================
# Face Detection Endpoints
# ============================================================================

@router.post("/process-face-detection")
async def process_face_detection(
    request: FaceDetectionRequest,
    service: AttendanceService = Depends(get_attendance_service)
) -> Dict:
    """
    Process face detection from camera feed
    Entry point for Module 1 Identity Service
    
    Args:
        request: Face detection data from camera
        service: Attendance service instance
    
    Returns:
        Check-in/out result with employee details
    """
    try:
        if request.is_exit:
            # Process exit
            exit_reason = ExitReason[request.exit_reason.upper()] if hasattr(ExitReason, request.exit_reason.upper()) else ExitReason.UNKNOWN
            result = service.process_exit_detection(
                request.aws_rekognition_id,
                request.camera_id,
                request.confidence,
                exit_reason
            )
            return {
                'success': result.success,
                'employee_id': result.employee_id,
                'check_out_time': result.check_out_time.isoformat() if result.check_out_time else None,
                'duration_minutes': result.duration_minutes,
                'message': result.message
            }
        else:
            # Process check-in
            result = service.process_face_detection(
                request.aws_rekognition_id,
                request.camera_id,
                request.confidence
            )
            return {
                'success': result.success,
                'employee_id': result.employee_id,
                'employee_name': result.employee_name,
                'check_in_time': result.check_in_time.isoformat() if result.check_in_time else None,
                'is_late': result.is_late,
                'message': result.message
            }
    except Exception as e:
        logger.error(f"Error processing face detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Manual Override Endpoints
# ============================================================================

@router.post("/override")
async def create_manual_override(
    request: ManualOverrideRequest,
    service: AttendanceService = Depends(get_attendance_service),
    session: Session = Depends(lambda: None)
) -> Dict:
    """
    Create or update attendance record with manual override
    Used for camera downtime, obstruction, or HR corrections
    
    Args:
        request: Override details
        service: Attendance service
        session: Database session
    
    Returns:
        Override result
    """
    try:
        status = None
        if request.status:
            status = AttendanceStatus[request.status.upper()]
        
        result = service.manual_override_attendance(
            employee_id=request.employee_id,
            override_date=request.attendance_date,
            check_in_time=request.check_in_time,
            check_out_time=request.check_out_time,
            status=status,
            override_reason=request.reason,
            override_user=request.override_user
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    
    except Exception as e:
        logger.error(f"Error creating override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/record/{record_id}")
async def get_attendance_record(
    record_id: int,
    session: Session = Depends(lambda: None)
) -> AttendanceRecordResponse:
    """
    Get specific attendance record
    
    Args:
        record_id: Attendance record ID
        session: Database session
    
    Returns:
        Attendance record details
    """
    try:
        record = AttendanceRecordDAO.get_by_id(session, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        return AttendanceRecordResponse(
            id=record.id,
            employee_id=record.employee_id,
            employee_name=record.employee.name if record.employee else "Unknown",
            attendance_date=record.attendance_date.isoformat(),
            check_in_time=record.check_in_time.isoformat() if record.check_in_time else None,
            check_out_time=record.check_out_time.isoformat() if record.check_out_time else None,
            status=record.status.value,
            is_manual_override=record.is_manual_override,
            actual_duration_minutes=record.calculate_duration()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Reporting Endpoints
# ============================================================================

@router.get("/reports")
async def get_attendance_reports(
    report_date: date = Query(None, description="Date for report (default: today)"),
    report_type: str = Query("summary", description="Report type: summary, shift-wise, department-wise, late-entries"),
    utility: AttendanceReportingUtility = Depends(get_reporting_utility),
    session: Session = Depends(lambda: None)
) -> ReportResponse:
    """
    Get attendance reports for specified date
    
    Args:
        report_date: Date for report
        report_type: Type of report to generate
        utility: Reporting utility instance
        session: Database session
    
    Returns:
        Report data based on type
    """
    try:
        if report_date is None:
            report_date = date.today()
        
        if report_type == "summary":
            data = _attendance_service.get_todays_attendance_summary() if report_date == date.today() else {}
        elif report_type == "shift-wise":
            data = {'shifts': utility.get_shift_wise_report(report_date)}
        elif report_type == "department-wise":
            data = {'departments': utility.get_department_wise_report(report_date)}
        elif report_type == "late-entries":
            data = {'late_entries': utility.get_late_entries_report(report_date)}
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        return ReportResponse(
            success=True,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee/{employee_id}/monthly-report")
async def get_employee_monthly_report(
    employee_id: int,
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    utility: AttendanceReportingUtility = Depends(get_reporting_utility)
) -> Dict:
    """
    Get monthly attendance report for employee
    
    Args:
        employee_id: Employee ID
        year: Year for report
        month: Month for report
        utility: Reporting utility
    
    Returns:
        Monthly attendance data
    """
    try:
        report = utility.get_employee_monthly_report(employee_id, year, month)
        if not report:
            raise HTTPException(status_code=404, detail="Employee or report not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee/{employee_id}/records")
async def get_employee_attendance_records(
    employee_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    session: Session = Depends(lambda: None)
) -> List[AttendanceRecordResponse]:
    """
    Get employee attendance records for date range
    
    Args:
        employee_id: Employee ID
        start_date: Start date
        end_date: End date
        session: Database session
    
    Returns:
        List of attendance records
    """
    try:
        records = AttendanceRecordDAO.get_date_range(session, employee_id, start_date, end_date)
        
        return [
            AttendanceRecordResponse(
                id=r.id,
                employee_id=r.employee_id,
                employee_name=r.employee.name if r.employee else "Unknown",
                attendance_date=r.attendance_date.isoformat(),
                check_in_time=r.check_in_time.isoformat() if r.check_in_time else None,
                check_out_time=r.check_out_time.isoformat() if r.check_out_time else None,
                status=r.status.value,
                is_manual_override=r.is_manual_override,
                actual_duration_minutes=r.calculate_duration()
            )
            for r in records
        ]
    except Exception as e:
        logger.error(f"Error getting employee records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Shift Management Endpoints
# ============================================================================

@router.post("/shifts")
async def create_shift(
    request: ShiftCreateRequest,
    session: Session = Depends(lambda: None)
) -> ShiftResponse:
    """
    Create new shift
    
    Args:
        request: Shift creation data
        session: Database session
    
    Returns:
        Created shift details
    """
    try:
        shift_data = request.dict()
        shift = ShiftDAO.create(session, shift_data)
        
        return ShiftResponse(
            id=shift.id,
            shift_name=shift.shift_name,
            start_time=shift.start_time.isoformat(),
            end_time=shift.end_time.isoformat(),
            grace_period_minutes=shift.grace_period_minutes,
            duration_minutes=shift.get_duration_minutes(),
            is_active=shift.is_active
        )
    except Exception as e:
        logger.error(f"Error creating shift: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shifts")
async def get_all_shifts(
    session: Session = Depends(lambda: None)
) -> List[ShiftResponse]:
    """
    Get all active shifts
    
    Args:
        session: Database session
    
    Returns:
        List of shifts
    """
    try:
        shifts = ShiftDAO.get_all_active(session)
        
        return [
            ShiftResponse(
                id=s.id,
                shift_name=s.shift_name,
                start_time=s.start_time.isoformat(),
                end_time=s.end_time.isoformat(),
                grace_period_minutes=s.grace_period_minutes,
                duration_minutes=s.get_duration_minutes(),
                is_active=s.is_active
            )
            for s in shifts
        ]
    except Exception as e:
        logger.error(f"Error getting shifts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shifts/{shift_id}")
async def get_shift(
    shift_id: int,
    session: Session = Depends(lambda: None)
) -> ShiftResponse:
    """
    Get shift details
    
    Args:
        shift_id: Shift ID
        session: Database session
    
    Returns:
        Shift details
    """
    try:
        shift = ShiftDAO.get_by_id(session, shift_id)
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        
        return ShiftResponse(
            id=shift.id,
            shift_name=shift.shift_name,
            start_time=shift.start_time.isoformat(),
            end_time=shift.end_time.isoformat(),
            grace_period_minutes=shift.grace_period_minutes,
            duration_minutes=shift.get_duration_minutes(),
            is_active=shift.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shift: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Department Management Endpoints
# ============================================================================

@router.post("/departments")
async def create_department(
    request: DepartmentCreateRequest,
    session: Session = Depends(lambda: None)
) -> DepartmentResponse:
    """
    Create new department
    
    Args:
        request: Department creation data
        session: Database session
    
    Returns:
        Created department details
    """
    try:
        dept_data = request.dict()
        dept = DepartmentDAO.create(session, dept_data)
        
        return DepartmentResponse(
            id=dept.id,
            dept_name=dept.dept_name,
            shift_id=dept.shift_id,
            manager_name=dept.manager_name,
            location=dept.location,
            entry_camera_id=dept.entry_camera_id,
            exit_camera_id=dept.exit_camera_id,
            is_active=dept.is_active
        )
    except Exception as e:
        logger.error(f"Error creating department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments")
async def get_all_departments(
    session: Session = Depends(lambda: None)
) -> List[DepartmentResponse]:
    """
    Get all active departments
    
    Args:
        session: Database session
    
    Returns:
        List of departments
    """
    try:
        depts = DepartmentDAO.get_all_active(session)
        
        return [
            DepartmentResponse(
                id=d.id,
                dept_name=d.dept_name,
                shift_id=d.shift_id,
                manager_name=d.manager_name,
                location=d.location,
                entry_camera_id=d.entry_camera_id,
                exit_camera_id=d.exit_camera_id,
                is_active=d.is_active
            )
            for d in depts
        ]
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/departments/{dept_id}")
async def get_department(
    dept_id: int,
    session: Session = Depends(lambda: None)
) -> DepartmentResponse:
    """
    Get department details
    
    Args:
        dept_id: Department ID
        session: Database session
    
    Returns:
        Department details
    """
    try:
        dept = DepartmentDAO.get_by_id(session, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        
        return DepartmentResponse(
            id=dept.id,
            dept_name=dept.dept_name,
            shift_id=dept.shift_id,
            manager_name=dept.manager_name,
            location=dept.location,
            entry_camera_id=dept.entry_camera_id,
            exit_camera_id=dept.exit_camera_id,
            is_active=dept.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Status Endpoints
# ============================================================================

@router.get("/summary")
async def get_attendance_summary(
    service: AttendanceService = Depends(get_attendance_service)
) -> AttendanceSummaryResponse:
    """
    Get today's attendance summary
    
    Args:
        service: Attendance service
    
    Returns:
        Today's attendance statistics
    """
    try:
        summary = service.get_todays_attendance_summary()
        
        return AttendanceSummaryResponse(
            date=summary.get('date', date.today().isoformat()),
            total_employees=summary.get('total_employees', 0),
            present=summary.get('present', 0),
            late=summary.get('late', 0),
            half_day=summary.get('half_day', 0),
            absent=summary.get('absent', 0),
            leave=summary.get('leave', 0),
            currently_in_frame=summary.get('currently_in_frame', 0),
            check_ins_today=summary.get('check_ins_today', 0),
            check_outs_today=summary.get('check_outs_today', 0),
            late_entries=summary.get('late_entries', 0)
        )
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'attendance_module'
    }


# ============================================================================
# Module Initialization
# ============================================================================

def init_attendance_module(session: Session) -> None:
    """
    Initialize attendance module with database session
    Call this during application startup
    
    Args:
        session: SQLAlchemy database session
    """
    global _attendance_service, _reporting_utility
    
    try:
        _attendance_service = AttendanceService(session)
        _reporting_utility = AttendanceReportingUtility(session)
        logger.info("Attendance module initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing attendance module: {str(e)}")
        raise


# Export for use in main app
__all__ = [
    'router',
    'init_attendance_module',
    'get_attendance_service',
    'get_reporting_utility'
]
