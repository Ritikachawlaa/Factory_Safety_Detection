"""
Module 3: Attendance Service
Core business logic for face-based attendance tracking, shift management, and reporting
Integrates with Identity Service (Module 1) for employee identification
Author: Factory Safety Detection Team
Date: 2025
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, List, Tuple, Set
from enum import Enum
import logging
import threading
from collections import defaultdict
import json

from sqlalchemy.orm import Session
from detection_system.attendance_models import (
    Shift, Department, Employee, AttendanceRecord, TimeFenceLog,
    ShiftDAO, DepartmentDAO, AttendanceRecordDAO, TimeFenceLogDAO,
    AttendanceStatus, CheckInOutType, ExitReason, TimeFenceEventType,
    EmployeeSessionState, AttendanceCheckInResult, AttendanceCheckOutResult
)

logger = logging.getLogger(__name__)


class IdentityServiceIntegration:
    """
    Integration wrapper for Module 1: Identity Service
    Handles communication with AWS Rekognition and face detection results
    """

    def __init__(self, session: Session):
        """
        Initialize identity service integration
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.aws_rekognition_cache = {}  # Cache of AWS IDs to Employee
        self._load_cache()

    def _load_cache(self) -> None:
        """Load AWS Rekognition IDs to employee mapping into cache"""
        try:
            employees = self.session.query(Employee).filter(
                Employee.aws_rekognition_id.isnot(None),
                Employee.is_active == True
            ).all()
            
            for emp in employees:
                if emp.aws_rekognition_id:
                    self.aws_rekognition_cache[emp.aws_rekognition_id] = emp
            
            logger.info(f"Loaded {len(self.aws_rekognition_cache)} employees to cache")
        except Exception as e:
            logger.error(f"Error loading identity cache: {str(e)}")

    def identify_employee(self, aws_rekognition_id: str, confidence: float = 0.9) -> Optional[Employee]:
        """
        Identify employee from AWS Rekognition match
        
        Args:
            aws_rekognition_id: AWS Rekognition person ID from Module 1
            confidence: Face detection confidence score (0-1)
        
        Returns:
            Employee object if matched and active, None otherwise
        """
        if confidence < 0.8:  # Minimum confidence threshold
            logger.warning(f"Low confidence match: {confidence}")
            return None
        
        # Check cache first
        if aws_rekognition_id in self.aws_rekognition_cache:
            employee = self.aws_rekognition_cache[aws_rekognition_id]
            if employee.is_active:
                return employee
        
        # Fall back to database query
        try:
            employee = self.session.query(Employee).filter(
                Employee.aws_rekognition_id == aws_rekognition_id,
                Employee.is_active == True
            ).first()
            
            if employee and aws_rekognition_id not in self.aws_rekognition_cache:
                self.aws_rekognition_cache[aws_rekognition_id] = employee
            
            return employee
        except Exception as e:
            logger.error(f"Error identifying employee: {str(e)}")
            return None

    def refresh_cache(self) -> None:
        """Refresh identity cache (call periodically or on employee updates)"""
        self.aws_rekognition_cache.clear()
        self._load_cache()


class GracePeriodCalculator:
    """Handles grace period and late detection logic"""

    @staticmethod
    def is_late(check_in_time: datetime, shift: Shift) -> bool:
        """
        Determine if check-in is late based on grace period
        
        Args:
            check_in_time: Actual check-in timestamp
            shift: Employee's assigned shift
        
        Returns:
            True if check-in is after grace period, False otherwise
        """
        # Convert check-in time to time object
        check_in_time_only = check_in_time.time()
        
        # Create datetime for grace period calculation
        grace_delta = timedelta(minutes=shift.grace_period_minutes)
        shift_start_dt = datetime.combine(check_in_time.date(), shift.start_time)
        grace_time_dt = shift_start_dt + grace_delta
        grace_time = grace_time_dt.time()
        
        return check_in_time_time_only > grace_time

    @staticmethod
    def calculate_late_minutes(check_in_time: datetime, shift: Shift) -> int:
        """
        Calculate how many minutes late the check-in is
        
        Args:
            check_in_time: Actual check-in timestamp
            shift: Employee's assigned shift
        
        Returns:
            Number of minutes late (0 if not late)
        """
        check_in_time_only = check_in_time.time()
        grace_delta = timedelta(minutes=shift.grace_period_minutes)
        shift_start_dt = datetime.combine(check_in_time.date(), shift.start_time)
        grace_time_dt = shift_start_dt + grace_delta
        grace_time = grace_time_dt.time()
        
        if check_in_time_only <= grace_time:
            return 0
        
        # Calculate minutes late
        check_in_dt = datetime.combine(check_in_time.date(), check_in_time_only)
        grace_time_dt_full = datetime.combine(check_in_time.date(), grace_time)
        late_minutes = int((check_in_dt - grace_time_dt_full).total_seconds() / 60)
        return max(0, late_minutes)


class ExitDetectionManager:
    """Manages exit detection and check-out logic"""

    def __init__(self, session: Session):
        """
        Initialize exit detection manager
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.exit_cameras = self._load_exit_cameras()

    def _load_exit_cameras(self) -> Dict[int, str]:
        """Load department exit camera mappings"""
        try:
            departments = self.session.query(Department).filter(
                Department.is_active == True
            ).all()
            
            exit_map = {}
            for dept in departments:
                if dept.exit_camera_id:
                    exit_map[dept.id] = dept.exit_camera_id
            
            logger.info(f"Loaded {len(exit_map)} exit cameras")
            return exit_map
        except Exception as e:
            logger.error(f"Error loading exit cameras: {str(e)}")
            return {}

    def is_exit_detection(self, employee: Employee, camera_id: str) -> bool:
        """
        Check if employee is being detected at an exit camera
        
        Args:
            employee: Employee object
            camera_id: Camera ID where detection occurred
        
        Returns:
            True if this is an exit camera for employee's department
        """
        exit_camera = self.exit_cameras.get(employee.department_id)
        return exit_camera and camera_id == exit_camera

    def process_exit(self, employee: Employee, camera_id: str, current_time: datetime) -> Tuple[bool, Optional[str]]:
        """
        Process employee exit detection
        
        Args:
            employee: Employee object
            camera_id: Camera ID where exit detected
            current_time: Timestamp of detection
        
        Returns:
            Tuple of (is_valid_exit, reason)
        """
        # Check if employee is on shift
        shift = employee.assigned_shift
        current_time_only = current_time.time()
        
        # Allow exit if within shift hours (with 30-min buffer for extended shift)
        shift_end_buffer = timedelta(minutes=30)
        shift_end_with_buffer = datetime.combine(
            current_time.date(), shift.end_time
        ) + shift_end_buffer
        
        if current_time > shift_end_with_buffer:
            logger.warning(f"Exit detection after shift end: {employee.employee_id}")
            return False, "Outside shift hours"
        
        if current_time_only < shift.start_time:
            logger.warning(f"Exit detection before shift start: {employee.employee_id}")
            return False, "Before shift start"
        
        return True, None

    def refresh_cache(self) -> None:
        """Refresh exit camera cache"""
        self.exit_cameras = self._load_exit_cameras()


class AttendanceService:
    """
    Main attendance service orchestrating all attendance logic
    Coordinates face detection, shift validation, check-in/out, and reporting
    """

    def __init__(self, session: Session):
        """
        Initialize attendance service
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.identity_service = IdentityServiceIntegration(session)
        self.exit_manager = ExitDetectionManager(session)
        
        # In-memory session tracking (employee_id -> EmployeeSessionState)
        self.employee_sessions: Dict[int, EmployeeSessionState] = {}
        self.session_lock = threading.Lock()
        
        # Statistics tracking
        self.daily_stats = {
            'total_check_ins': 0,
            'total_check_outs': 0,
            'total_late_entries': 0,
            'last_updated': datetime.utcnow()
        }
        logger.info("Attendance Service initialized")

    def process_face_detection(self, aws_rekognition_id: str, camera_id: str, 
                               confidence: float) -> AttendanceCheckInResult:
        """
        Process face detection and handle attendance check-in
        Entry point from Module 1: Identity Service
        
        Args:
            aws_rekognition_id: AWS Rekognition person ID
            camera_id: Camera ID where face was detected
            confidence: Face detection confidence score
        
        Returns:
            AttendanceCheckInResult with check-in details
        """
        current_time = datetime.utcnow()
        
        # Step 1: Identify employee
        employee = self.identity_service.identify_employee(aws_rekognition_id, confidence)
        if not employee:
            logger.warning(f"Unknown employee detected: {aws_rekognition_id}")
            return AttendanceCheckInResult(
                success=False,
                message="Unknown employee or low confidence match"
            )
        
        logger.info(f"Face detected: {employee.employee_id} at camera {camera_id}")
        
        # Step 2: Check if employee is on shift
        shift = employee.assigned_shift
        if not self._is_on_shift_now(shift, current_time):
            logger.debug(f"Employee {employee.employee_id} not on shift")
            return AttendanceCheckInResult(
                success=False,
                employee_id=employee.id,
                employee_name=employee.name,
                message="Not on shift"
            )
        
        # Step 3: Check for existing session or create new one
        with self.session_lock:
            if employee.id in self.employee_sessions:
                # Update existing session
                session_state = self.employee_sessions[employee.id]
                if not session_state.is_expired():
                    session_state.update_detection(camera_id, confidence)
                    logger.debug(f"Updated session for {employee.employee_id}")
                    return AttendanceCheckInResult(
                        success=True,
                        employee_id=employee.id,
                        employee_name=employee.name,
                        message="Already checked in"
                    )
                else:
                    # Session expired, treat as new
                    del self.employee_sessions[employee.id]
            
            # Step 4: Get or create today's attendance record
            today = current_time.date()
            record = AttendanceRecordDAO.get_today_record(self.session, employee.id, today)
            
            if record and record.check_in_time:
                # Already checked in, just update session
                session_state = EmployeeSessionState(
                    employee_id=employee.id,
                    name=employee.name,
                    first_detection_time=current_time,
                    last_detection_time=current_time,
                    last_detection_camera=camera_id,
                    detection_confidence=confidence
                )
                self.employee_sessions[employee.id] = session_state
                
                logger.info(f"Employee {employee.employee_id} already checked in at {record.check_in_time}")
                return AttendanceCheckInResult(
                    success=True,
                    employee_id=employee.id,
                    employee_name=employee.name,
                    check_in_time=record.check_in_time,
                    is_late=record.status == AttendanceStatus.LATE,
                    message="Already checked in",
                    record_id=record.id
                )
            
            # Step 5: Create new check-in
            is_late = GracePeriodCalculator.is_late(current_time, shift)
            status = AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT
            
            if not record:
                record = AttendanceRecord(
                    employee_id=employee.id,
                    attendance_date=today,
                    check_in_time=current_time,
                    check_in_type=CheckInOutType.AUTO_FACE,
                    status=status,
                    first_detection_camera=camera_id,
                    shift_duration_minutes=shift.get_duration_minutes(),
                    grace_period_applied=is_late,
                    detection_confidence=confidence
                )
                self.session.add(record)
            else:
                record.check_in_time = current_time
                record.check_in_type = CheckInOutType.AUTO_FACE
                record.status = status
                record.first_detection_camera = camera_id
                record.grace_period_applied = is_late
                record.detection_confidence = confidence
            
            self.session.commit()
            
            # Create session state
            session_state = EmployeeSessionState(
                employee_id=employee.id,
                name=employee.name,
                first_detection_time=current_time,
                last_detection_time=current_time,
                last_detection_camera=camera_id,
                detection_confidence=confidence
            )
            self.employee_sessions[employee.id] = session_state
            
            # Update statistics
            self.daily_stats['total_check_ins'] += 1
            if is_late:
                self.daily_stats['total_late_entries'] += 1
            
            logger.info(f"Check-in processed: {employee.employee_id} at {current_time} - Status: {status.value}")
            
            return AttendanceCheckInResult(
                success=True,
                employee_id=employee.id,
                employee_name=employee.name,
                check_in_time=current_time,
                is_late=is_late,
                message=f"Checked in - {'Late' if is_late else 'On time'}",
                record_id=record.id
            )

    def process_exit_detection(self, aws_rekognition_id: str, camera_id: str,
                              confidence: float, exit_reason: ExitReason = ExitReason.UNKNOWN) -> AttendanceCheckOutResult:
        """
        Process face detection at exit point and handle check-out
        
        Args:
            aws_rekognition_id: AWS Rekognition person ID
            camera_id: Camera ID where face detected (must be exit camera)
            confidence: Face detection confidence
            exit_reason: Reason for exit (lunch, break, end of shift, etc.)
        
        Returns:
            AttendanceCheckOutResult with check-out details
        """
        current_time = datetime.utcnow()
        
        # Step 1: Identify employee
        employee = self.identity_service.identify_employee(aws_rekognition_id, confidence)
        if not employee:
            logger.warning(f"Unknown employee at exit: {aws_rekognition_id}")
            return AttendanceCheckOutResult(
                success=False,
                message="Unknown employee"
            )
        
        # Step 2: Verify exit camera
        if not self.exit_manager.is_exit_detection(employee, camera_id):
            logger.debug(f"Detection not at exit camera: {camera_id}")
            return AttendanceCheckOutResult(
                success=False,
                employee_id=employee.id,
                message="Not at exit point"
            )
        
        # Step 3: Validate exit timing
        is_valid, reason = self.exit_manager.process_exit(employee, camera_id, current_time)
        if not is_valid:
            logger.warning(f"Invalid exit for {employee.employee_id}: {reason}")
            
            # Log suspicious exit
            exit_log = TimeFenceLog(
                employee_id=employee.id,
                event_timestamp=current_time,
                event_type=TimeFenceEventType.SUSPICIOUS_MOVEMENT,
                exit_reason=exit_reason,
                camera_id=camera_id,
                detection_confidence=confidence,
                is_authorized=False
            )
            self.session.add(exit_log)
            self.session.commit()
            
            return AttendanceCheckOutResult(
                success=False,
                employee_id=employee.id,
                message=f"Invalid exit: {reason}",
                exit_reason=exit_reason
            )
        
        # Step 4: Update today's attendance record with check-out
        today = current_time.date()
        record = AttendanceRecordDAO.get_today_record(self.session, employee.id, today)
        
        if not record or not record.check_in_time:
            logger.warning(f"No check-in found for {employee.employee_id} on exit")
            return AttendanceCheckOutResult(
                success=False,
                employee_id=employee.id,
                message="No matching check-in found"
            )
        
        record.check_out_time = current_time
        record.check_out_type = CheckInOutType.AUTO_FACE
        record.last_detection_camera = camera_id
        record.actual_duration_minutes = record.calculate_duration()
        self.session.commit()
        
        # Step 5: Log exit event
        exit_log = TimeFenceLog(
            employee_id=employee.id,
            attendance_record_id=record.id,
            event_timestamp=current_time,
            event_type=TimeFenceEventType.EXIT,
            exit_reason=exit_reason,
            camera_id=camera_id,
            detection_confidence=confidence,
            is_authorized=True
        )
        self.session.add(exit_log)
        self.session.commit()
        
        # Step 6: Clear session state
        with self.session_lock:
            if employee.id in self.employee_sessions:
                del self.employee_sessions[employee.id]
        
        # Update statistics
        self.daily_stats['total_check_outs'] += 1
        
        logger.info(f"Check-out processed: {employee.employee_id} at {current_time}")
        
        return AttendanceCheckOutResult(
            success=True,
            employee_id=employee.id,
            check_out_time=current_time,
            duration_minutes=record.actual_duration_minutes,
            message="Successfully checked out",
            exit_reason=exit_reason
        )

    def manual_override_attendance(self, employee_id: int, override_date: date,
                                   check_in_time: Optional[datetime] = None,
                                   check_out_time: Optional[datetime] = None,
                                   status: Optional[AttendanceStatus] = None,
                                   override_reason: str = "",
                                   override_user: str = "admin") -> Dict:
        """
        Allow HR/Admin to manually override or add attendance record
        Used for camera downtime, obstruction, special circumstances
        
        Args:
            employee_id: Employee ID
            override_date: Date of attendance
            check_in_time: Override check-in time
            check_out_time: Override check-out time
            status: Override status
            override_reason: Reason for override
            override_user: User making override
        
        Returns:
            Dict with override result
        """
        try:
            # Get employee
            employee = self.session.query(Employee).filter(
                Employee.id == employee_id
            ).first()
            
            if not employee:
                return {'success': False, 'message': 'Employee not found'}
            
            # Get or create record
            record = AttendanceRecordDAO.get_today_record(self.session, employee_id, override_date)
            
            if not record:
                record = AttendanceRecord(
                    employee_id=employee_id,
                    attendance_date=override_date
                )
                self.session.add(record)
            
            # Apply overrides
            if check_in_time:
                record.check_in_time = check_in_time
                record.check_in_type = CheckInOutType.MANUAL_OVERRIDE
            
            if check_out_time:
                record.check_out_time = check_out_time
                record.check_out_type = CheckInOutType.MANUAL_OVERRIDE
            
            if status:
                record.status = status
            else:
                # Auto-calculate status if not provided
                if record.check_in_time:
                    shift = employee.assigned_shift
                    if GracePeriodCalculator.is_late(record.check_in_time, shift):
                        record.status = AttendanceStatus.LATE
                    else:
                        record.status = AttendanceStatus.PRESENT
                elif override_reason.lower() in ['leave', 'vacation', 'sick']:
                    record.status = AttendanceStatus.LEAVE
                else:
                    record.status = AttendanceStatus.ABSENT
            
            # Mark as override
            record.is_manual_override = True
            record.override_by_user = override_user
            record.override_reason = override_reason
            record.override_timestamp = datetime.utcnow()
            
            self.session.commit()
            
            logger.info(f"Manual override applied for {employee.employee_id} by {override_user}")
            
            return {
                'success': True,
                'message': 'Attendance record updated',
                'record_id': record.id,
                'employee_id': employee_id,
                'status': record.status.value
            }
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error applying override: {str(e)}")
            return {'success': False, 'message': str(e)}

    def _is_on_shift_now(self, shift: Shift, current_time: datetime) -> bool:
        """Check if current time is within shift window"""
        current_time_only = current_time.time()
        
        # Check if within shift hours
        if shift.start_time <= current_time_only <= shift.end_time:
            return True
        
        # Allow 30 min grace after shift end
        shift_end_buffer = datetime.combine(current_time.date(), shift.end_time) + timedelta(minutes=30)
        if current_time <= shift_end_buffer:
            return True
        
        return False

    def get_todays_attendance_summary(self) -> Dict:
        """
        Get today's attendance summary
        
        Returns:
            Dict with attendance statistics for the day
        """
        today = date.today()
        
        try:
            all_records = self.session.query(AttendanceRecord).filter(
                AttendanceRecord.attendance_date == today,
                AttendanceRecord.is_active == True
            ).all()
            
            summary = {
                'date': today.isoformat(),
                'total_employees': len(all_records),
                'present': len([r for r in all_records if r.status == AttendanceStatus.PRESENT]),
                'late': len([r for r in all_records if r.status == AttendanceStatus.LATE]),
                'half_day': len([r for r in all_records if r.status == AttendanceStatus.HALF_DAY]),
                'absent': len([r for r in all_records if r.status == AttendanceStatus.ABSENT]),
                'leave': len([r for r in all_records if r.status == AttendanceStatus.LEAVE]),
                'currently_in_frame': len(self.employee_sessions),
                'check_ins_today': self.daily_stats['total_check_ins'],
                'check_outs_today': self.daily_stats['total_check_outs'],
                'late_entries': self.daily_stats['total_late_entries']
            }
            
            return summary
        except Exception as e:
            logger.error(f"Error getting attendance summary: {str(e)}")
            return {}

    def expire_old_sessions(self, timeout_seconds: int = 300) -> int:
        """
        Expire old employee sessions (when employee leaves frame)
        
        Args:
            timeout_seconds: Session timeout in seconds
        
        Returns:
            Number of sessions expired
        """
        expired_count = 0
        
        with self.session_lock:
            expired_employees = []
            for emp_id, session_state in self.employee_sessions.items():
                if session_state.is_expired():
                    expired_employees.append(emp_id)
                    expired_count += 1
            
            for emp_id in expired_employees:
                del self.employee_sessions[emp_id]
        
        if expired_count > 0:
            logger.info(f"Expired {expired_count} old sessions")
        
        return expired_count


class AttendanceReportingUtility:
    """Generates various attendance reports"""

    def __init__(self, session: Session):
        """
        Initialize reporting utility
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_shift_wise_report(self, report_date: date) -> List[Dict]:
        """
        Generate shift-wise attendance report
        
        Args:
            report_date: Date for report
        
        Returns:
            List of dicts with shift-wise attendance data
        """
        try:
            shifts = self.session.query(Shift).filter(Shift.is_active == True).all()
            report = []
            
            for shift in shifts:
                # Get all employees in this shift
                employees = self.session.query(Employee).filter(
                    Employee.shift_id == shift.id,
                    Employee.is_active == True
                ).all()
                
                # Get attendance records
                records = self.session.query(AttendanceRecord).filter(
                    AttendanceRecord.attendance_date == report_date,
                    AttendanceRecord.is_active == True,
                    AttendanceRecord.employee_id.in_([e.id for e in employees])
                ).all()
                
                shift_data = {
                    'shift_name': shift.shift_name,
                    'shift_hours': f"{shift.start_time} - {shift.end_time}",
                    'total_employees': len(employees),
                    'present': len([r for r in records if r.status == AttendanceStatus.PRESENT]),
                    'late': len([r for r in records if r.status == AttendanceStatus.LATE]),
                    'half_day': len([r for r in records if r.status == AttendanceStatus.HALF_DAY]),
                    'absent': len([r for r in records if r.status == AttendanceStatus.ABSENT]),
                    'leave': len([r for r in records if r.status == AttendanceStatus.LEAVE]),
                    'attendance_percentage': (len(records) / len(employees) * 100) if employees else 0
                }
                report.append(shift_data)
            
            return report
        except Exception as e:
            logger.error(f"Error generating shift report: {str(e)}")
            return []

    def get_department_wise_report(self, report_date: date) -> List[Dict]:
        """
        Generate department-wise attendance report
        
        Args:
            report_date: Date for report
        
        Returns:
            List of dicts with department-wise attendance data
        """
        try:
            departments = self.session.query(Department).filter(
                Department.is_active == True
            ).all()
            report = []
            
            for dept in departments:
                # Get all employees in this department
                employees = self.session.query(Employee).filter(
                    Employee.department_id == dept.id,
                    Employee.is_active == True
                ).all()
                
                # Get attendance records
                records = self.session.query(AttendanceRecord).filter(
                    AttendanceRecord.attendance_date == report_date,
                    AttendanceRecord.is_active == True,
                    AttendanceRecord.employee_id.in_([e.id for e in employees])
                ).all()
                
                dept_data = {
                    'department_name': dept.dept_name,
                    'location': dept.location or 'N/A',
                    'manager': dept.manager_name or 'N/A',
                    'total_employees': len(employees),
                    'present': len([r for r in records if r.status == AttendanceStatus.PRESENT]),
                    'late': len([r for r in records if r.status == AttendanceStatus.LATE]),
                    'half_day': len([r for r in records if r.status == AttendanceStatus.HALF_DAY]),
                    'absent': len([r for r in records if r.status == AttendanceStatus.ABSENT]),
                    'leave': len([r for r in records if r.status == AttendanceStatus.LEAVE]),
                    'attendance_percentage': (len(records) / len(employees) * 100) if employees else 0
                }
                report.append(dept_data)
            
            return report
        except Exception as e:
            logger.error(f"Error generating department report: {str(e)}")
            return []

    def get_employee_monthly_report(self, employee_id: int, year: int, month: int) -> Dict:
        """
        Generate monthly report for single employee
        
        Args:
            employee_id: Employee ID
            year: Year for report
            month: Month for report
        
        Returns:
            Dict with monthly attendance data
        """
        try:
            employee = self.session.query(Employee).filter(
                Employee.id == employee_id
            ).first()
            
            if not employee:
                return {}
            
            # Get monthly statistics
            stats = AttendanceRecordDAO.get_monthly_stats(self.session, employee_id, year, month)
            
            return {
                'employee_id': employee.employee_id,
                'employee_name': employee.name,
                'department': employee.department.dept_name if employee.department else 'N/A',
                'shift': employee.assigned_shift.shift_name if employee.assigned_shift else 'N/A',
                'year': year,
                'month': month,
                **stats
            }
        except Exception as e:
            logger.error(f"Error generating employee monthly report: {str(e)}")
            return {}

    def get_late_entries_report(self, report_date: date) -> List[Dict]:
        """
        Generate report of all late entries for a date
        
        Args:
            report_date: Date for report
        
        Returns:
            List of dicts with late entry details
        """
        try:
            late_records = self.session.query(AttendanceRecord).filter(
                AttendanceRecord.attendance_date == report_date,
                AttendanceRecord.status == AttendanceStatus.LATE,
                AttendanceRecord.is_active == True
            ).all()
            
            report = []
            for record in late_records:
                employee = record.employee
                late_minutes = GracePeriodCalculator.calculate_late_minutes(
                    record.check_in_time, employee.assigned_shift
                )
                
                report.append({
                    'employee_id': employee.employee_id,
                    'employee_name': employee.name,
                    'department': employee.department.dept_name if employee.department else 'N/A',
                    'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                    'late_minutes': late_minutes,
                    'grace_period_minutes': employee.assigned_shift.grace_period_minutes,
                    'override': record.is_manual_override
                })
            
            return sorted(report, key=lambda x: x['late_minutes'], reverse=True)
        except Exception as e:
            logger.error(f"Error generating late entries report: {str(e)}")
            return []
