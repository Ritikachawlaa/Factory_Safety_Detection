"""
Module 3: Attendance & Workforce Presence System
Database Models and DAOs for Shift, Department, and Attendance Tracking
Author: Factory Safety Detection Team
Date: 2025
"""

from datetime import datetime, time, date, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
import logging

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text, Time, Date, 
    ForeignKey, Index, Enum as SQLEnum, UniqueConstraint, CheckConstraint,
    and_, or_, desc, func
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass, field
import pytz

Base = declarative_base()
logger = logging.getLogger(__name__)


class AttendanceStatus(str, Enum):
    """Enumeration for attendance status types"""
    PRESENT = "Present"
    LATE = "Late"
    HALF_DAY = "Half-day"
    ABSENT = "Absent"
    LEAVE = "Leave"
    CANCELLED = "Cancelled"


class CheckInOutType(str, Enum):
    """Enumeration for check-in/out types"""
    AUTO_FACE = "auto_face"
    MANUAL_OVERRIDE = "manual_override"
    SYSTEM_CORRECTION = "system_correction"


class ExitReason(str, Enum):
    """Enumeration for exit reasons"""
    NORMAL_EXIT = "normal_exit"
    LUNCH_BREAK = "lunch_break"
    MEETING = "meeting"
    EMERGENCY = "emergency"
    END_OF_SHIFT = "end_of_shift"
    UNKNOWN = "unknown"


class TimeFenceEventType(str, Enum):
    """Enumeration for time fence events"""
    ENTRY = "entry"
    EXIT = "exit"
    RE_ENTRY = "re_entry"
    SUSPICIOUS_MOVEMENT = "suspicious_movement"


# ============================================================================
# Database Models
# ============================================================================

class Shift(Base):
    """
    Shift configuration model
    Defines work hours, grace periods, and break times for different shifts
    """
    __tablename__ = 'shifts'

    id = Column(Integer, primary_key=True)
    shift_name = Column(String(100), unique=True, nullable=False, index=True)
    start_time = Column(Time, nullable=False)  # HH:MM:SS format
    end_time = Column(Time, nullable=False)    # HH:MM:SS format
    grace_period_minutes = Column(Integer, default=5)  # Late tolerance in minutes
    break_start = Column(Time, nullable=True)  # Optional break start time
    break_end = Column(Time, nullable=True)    # Optional break end time
    break_duration_minutes = Column(Integer, default=0)  # Break duration
    is_active = Column(Boolean, default=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    departments = relationship("Department", back_populates="shift")
    employees = relationship("Employee", back_populates="assigned_shift")

    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_shift_time_order'),
    )

    def get_duration_minutes(self) -> int:
        """Calculate total shift duration in minutes"""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        if end_dt < start_dt:  # Night shift crossing midnight
            end_dt += timedelta(days=1)
        return int((end_dt - start_dt).total_seconds() / 60)

    def is_during_shift(self, check_time: time) -> bool:
        """Check if time falls within shift window"""
        return self.start_time <= check_time <= self.end_time

    def is_late(self, check_in_time: time) -> bool:
        """Check if check-in is after grace period"""
        grace_delta = timedelta(minutes=self.grace_period_minutes)
        grace_time = (datetime.combine(date.today(), self.start_time) + grace_delta).time()
        return check_in_time > grace_time

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'shift_name': self.shift_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'grace_period_minutes': self.grace_period_minutes,
            'break_start': self.break_start.isoformat() if self.break_start else None,
            'break_end': self.break_end.isoformat() if self.break_end else None,
            'is_active': self.is_active,
            'duration_minutes': self.get_duration_minutes()
        }


class Department(Base):
    """
    Department model mapping employees to shifts and locations
    """
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    dept_name = Column(String(150), unique=True, nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=False, index=True)
    manager_name = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)  # e.g., "Floor 1, Section A"
    entry_camera_id = Column(String(50), nullable=True)  # Main entry point
    exit_camera_id = Column(String(50), nullable=True)   # Main exit point
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shift = relationship("Shift", back_populates="departments")
    employees = relationship("Employee", back_populates="department")

    __table_args__ = (
        Index('idx_dept_shift_active', 'shift_id', 'is_active'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'dept_name': self.dept_name,
            'shift_id': self.shift_id,
            'manager_name': self.manager_name,
            'location': self.location,
            'entry_camera_id': self.entry_camera_id,
            'exit_camera_id': self.exit_camera_id,
            'is_active': self.is_active
        }


class Employee(Base):
    """
    Employee model extended with attendance tracking
    Note: This extends the existing Employee model structure
    """
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=False, index=True)
    face_encoding = Column(String(500), nullable=True)  # For face recognition
    aws_rekognition_id = Column(String(200), nullable=True, unique=True)  # AWS Rekognition index ID
    is_active = Column(Boolean, default=True, index=True)
    hire_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="employees")
    assigned_shift = relationship("Shift", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    time_fence_logs = relationship("TimeFenceLog", back_populates="employee")

    __table_args__ = (
        Index('idx_employee_dept_shift', 'department_id', 'shift_id', 'is_active'),
        Index('idx_employee_aws_id', 'aws_rekognition_id'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'department_id': self.department_id,
            'shift_id': self.shift_id,
            'is_active': self.is_active,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None
        }


class AttendanceRecord(Base):
    """
    Daily attendance record for each employee
    Tracks check-in/check-out times, status, and override information
    """
    __tablename__ = 'attendance_records'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)  # First detection of employee
    check_out_time = Column(DateTime, nullable=True)  # Last detection or exit
    check_in_type = Column(SQLEnum(CheckInOutType), default=CheckInOutType.AUTO_FACE)
    check_out_type = Column(SQLEnum(CheckInOutType), default=CheckInOutType.AUTO_FACE)
    status = Column(SQLEnum(AttendanceStatus), default=AttendanceStatus.ABSENT, index=True)
    
    # Override and correction fields
    is_manual_override = Column(Boolean, default=False, index=True)
    override_by_user = Column(String(100), nullable=True)  # User who made override
    override_reason = Column(Text, nullable=True)
    override_timestamp = Column(DateTime, nullable=True)
    
    # Metadata
    shift_duration_minutes = Column(Integer, nullable=True)  # Expected shift duration
    actual_duration_minutes = Column(Integer, nullable=True)  # Actual time at work
    grace_period_applied = Column(Boolean, default=False)  # Whether grace period was used
    notes = Column(Text, nullable=True)
    
    # Tracking metadata
    first_detection_camera = Column(String(50), nullable=True)
    last_detection_camera = Column(String(50), nullable=True)
    detection_confidence = Column(Float, default=0.0)  # Face detection confidence
    
    # Soft delete and audit
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")
    time_fence_logs = relationship("TimeFenceLog", back_populates="attendance_record")

    __table_args__ = (
        Index('idx_attendance_employee_date', 'employee_id', 'attendance_date'),
        Index('idx_attendance_date_status', 'attendance_date', 'status'),
        Index('idx_attendance_manual_override', 'is_manual_override', 'attendance_date'),
        UniqueConstraint('employee_id', 'attendance_date', name='unique_daily_attendance'),
    )

    def calculate_duration(self) -> Optional[int]:
        """Calculate duration in minutes between check-in and check-out"""
        if self.check_in_time and self.check_out_time:
            duration = (self.check_out_time - self.check_in_time).total_seconds() / 60
            return int(duration)
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'attendance_date': self.attendance_date.isoformat(),
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'status': self.status.value,
            'is_manual_override': self.is_manual_override,
            'override_by_user': self.override_by_user,
            'actual_duration_minutes': self.calculate_duration(),
            'detection_confidence': self.detection_confidence
        }


class TimeFenceLog(Base):
    """
    Time Fence event log for tracking employee movement in/out of facility
    Used to detect early departures, unauthorized absences, and re-entries
    """
    __tablename__ = 'time_fence_logs'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    attendance_record_id = Column(Integer, ForeignKey('attendance_records.id'), nullable=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(SQLEnum(TimeFenceEventType), nullable=False, index=True)
    exit_reason = Column(SQLEnum(ExitReason), default=ExitReason.UNKNOWN)
    
    # Geolocation/Camera info
    camera_id = Column(String(50), nullable=True, index=True)
    zone_name = Column(String(100), nullable=True)
    
    # Detection info
    detection_confidence = Column(Float, default=0.0)
    
    # Event analysis
    duration_outside_minutes = Column(Integer, nullable=True)  # If re-entry
    is_authorized = Column(Boolean, nullable=True)  # Whether exit was expected
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    employee = relationship("Employee", back_populates="time_fence_logs")
    attendance_record = relationship("AttendanceRecord", back_populates="time_fence_logs")

    __table_args__ = (
        Index('idx_timefence_employee_timestamp', 'employee_id', 'event_timestamp'),
        Index('idx_timefence_event_type_timestamp', 'event_type', 'event_timestamp'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'event_timestamp': self.event_timestamp.isoformat(),
            'event_type': self.event_type.value,
            'exit_reason': self.exit_reason.value,
            'camera_id': self.camera_id,
            'zone_name': self.zone_name,
            'detection_confidence': self.detection_confidence,
            'duration_outside_minutes': self.duration_outside_minutes
        }


# ============================================================================
# Data Access Objects (DAOs)
# ============================================================================

class ShiftDAO:
    """Data Access Object for Shift operations"""

    @staticmethod
    def create(session: Session, shift_data: Dict) -> Shift:
        """Create new shift"""
        try:
            shift = Shift(**shift_data)
            session.add(shift)
            session.commit()
            logger.info(f"Created shift: {shift.shift_name}")
            return shift
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating shift: {str(e)}")
            raise

    @staticmethod
    def get_by_id(session: Session, shift_id: int) -> Optional[Shift]:
        """Get shift by ID"""
        return session.query(Shift).filter(Shift.id == shift_id).first()

    @staticmethod
    def get_by_name(session: Session, shift_name: str) -> Optional[Shift]:
        """Get shift by name"""
        return session.query(Shift).filter(Shift.shift_name == shift_name).first()

    @staticmethod
    def get_all_active(session: Session) -> List[Shift]:
        """Get all active shifts"""
        return session.query(Shift).filter(Shift.is_active == True).order_by(Shift.start_time).all()

    @staticmethod
    def update(session: Session, shift_id: int, update_data: Dict) -> Optional[Shift]:
        """Update shift details"""
        try:
            shift = ShiftDAO.get_by_id(session, shift_id)
            if not shift:
                return None
            for key, value in update_data.items():
                if hasattr(shift, key):
                    setattr(shift, key, value)
            shift.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated shift: {shift_id}")
            return shift
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating shift: {str(e)}")
            raise

    @staticmethod
    def delete(session: Session, shift_id: int) -> bool:
        """Soft delete shift"""
        try:
            shift = ShiftDAO.get_by_id(session, shift_id)
            if not shift:
                return False
            shift.is_active = False
            session.commit()
            logger.info(f"Deleted shift: {shift_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting shift: {str(e)}")
            raise


class DepartmentDAO:
    """Data Access Object for Department operations"""

    @staticmethod
    def create(session: Session, dept_data: Dict) -> Department:
        """Create new department"""
        try:
            dept = Department(**dept_data)
            session.add(dept)
            session.commit()
            logger.info(f"Created department: {dept.dept_name}")
            return dept
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating department: {str(e)}")
            raise

    @staticmethod
    def get_by_id(session: Session, dept_id: int) -> Optional[Department]:
        """Get department by ID"""
        return session.query(Department).filter(Department.id == dept_id).first()

    @staticmethod
    def get_by_name(session: Session, dept_name: str) -> Optional[Department]:
        """Get department by name"""
        return session.query(Department).filter(Department.dept_name == dept_name).first()

    @staticmethod
    def get_by_shift(session: Session, shift_id: int) -> List[Department]:
        """Get all departments for a shift"""
        return session.query(Department).filter(
            and_(Department.shift_id == shift_id, Department.is_active == True)
        ).all()

    @staticmethod
    def get_all_active(session: Session) -> List[Department]:
        """Get all active departments"""
        return session.query(Department).filter(Department.is_active == True).all()

    @staticmethod
    def update(session: Session, dept_id: int, update_data: Dict) -> Optional[Department]:
        """Update department"""
        try:
            dept = DepartmentDAO.get_by_id(session, dept_id)
            if not dept:
                return None
            for key, value in update_data.items():
                if hasattr(dept, key):
                    setattr(dept, key, value)
            dept.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated department: {dept_id}")
            return dept
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating department: {str(e)}")
            raise


class AttendanceRecordDAO:
    """Data Access Object for AttendanceRecord operations"""

    @staticmethod
    def create(session: Session, record_data: Dict) -> AttendanceRecord:
        """Create new attendance record"""
        try:
            record = AttendanceRecord(**record_data)
            session.add(record)
            session.commit()
            logger.info(f"Created attendance record for employee: {record.employee_id}")
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating attendance record: {str(e)}")
            raise

    @staticmethod
    def get_by_id(session: Session, record_id: int) -> Optional[AttendanceRecord]:
        """Get record by ID"""
        return session.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()

    @staticmethod
    def get_today_record(session: Session, employee_id: int, target_date: Optional[date] = None) -> Optional[AttendanceRecord]:
        """Get today's attendance record for employee"""
        if target_date is None:
            target_date = date.today()
        return session.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date == target_date,
                AttendanceRecord.is_active == True
            )
        ).first()

    @staticmethod
    def get_date_range(session: Session, employee_id: int, start_date: date, end_date: date) -> List[AttendanceRecord]:
        """Get attendance records for date range"""
        return session.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date >= start_date,
                AttendanceRecord.attendance_date <= end_date,
                AttendanceRecord.is_active == True
            )
        ).order_by(desc(AttendanceRecord.attendance_date)).all()

    @staticmethod
    def get_by_date_and_status(session: Session, target_date: date, status: AttendanceStatus) -> List[AttendanceRecord]:
        """Get all records for date with specific status"""
        return session.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.attendance_date == target_date,
                AttendanceRecord.status == status,
                AttendanceRecord.is_active == True
            )
        ).all()

    @staticmethod
    def update(session: Session, record_id: int, update_data: Dict) -> Optional[AttendanceRecord]:
        """Update attendance record"""
        try:
            record = AttendanceRecordDAO.get_by_id(session, record_id)
            if not record:
                return None
            for key, value in update_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            record.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated attendance record: {record_id}")
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating attendance record: {str(e)}")
            raise

    @staticmethod
    def manual_override(session: Session, record_id: int, override_data: Dict, user: str) -> Optional[AttendanceRecord]:
        """Apply manual override to attendance record"""
        try:
            record = AttendanceRecordDAO.get_by_id(session, record_id)
            if not record:
                return None
            
            # Update fields
            for key, value in override_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            # Mark as manual override
            record.is_manual_override = True
            record.override_by_user = user
            record.override_timestamp = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Manual override applied to record {record_id} by {user}")
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error applying override: {str(e)}")
            raise

    @staticmethod
    def get_monthly_stats(session: Session, employee_id: int, year: int, month: int) -> Dict:
        """Get monthly attendance statistics"""
        from datetime import datetime as dt
        
        # Get first and last day of month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        records = AttendanceRecordDAO.get_date_range(session, employee_id, start_date, end_date)
        
        stats = {
            'total_days': len([r for r in records if r.is_active]),
            'present': len([r for r in records if r.status == AttendanceStatus.PRESENT]),
            'late': len([r for r in records if r.status == AttendanceStatus.LATE]),
            'half_day': len([r for r in records if r.status == AttendanceStatus.HALF_DAY]),
            'absent': len([r for r in records if r.status == AttendanceStatus.ABSENT]),
            'leave': len([r for r in records if r.status == AttendanceStatus.LEAVE]),
        }
        
        return stats

    @staticmethod
    def cleanup_old_records(session: Session, days_to_keep: int = 365) -> int:
        """Delete records older than specified days (soft delete)"""
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            old_records = session.query(AttendanceRecord).filter(
                AttendanceRecord.attendance_date < cutoff_date
            ).update({'is_active': False})
            session.commit()
            logger.info(f"Cleaned up {old_records} old attendance records")
            return old_records
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up records: {str(e)}")
            raise


class TimeFenceLogDAO:
    """Data Access Object for TimeFenceLog operations"""

    @staticmethod
    def create(session: Session, log_data: Dict) -> TimeFenceLog:
        """Create new time fence log"""
        try:
            log = TimeFenceLog(**log_data)
            session.add(log)
            session.commit()
            logger.info(f"Created time fence log for employee: {log.employee_id}")
            return log
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating time fence log: {str(e)}")
            raise

    @staticmethod
    def get_today_events(session: Session, employee_id: int, target_date: Optional[date] = None) -> List[TimeFenceLog]:
        """Get all time fence events for employee on given date"""
        if target_date is None:
            target_date = date.today()
        
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        return session.query(TimeFenceLog).filter(
            and_(
                TimeFenceLog.employee_id == employee_id,
                TimeFenceLog.event_timestamp >= start_dt,
                TimeFenceLog.event_timestamp <= end_dt
            )
        ).order_by(TimeFenceLog.event_timestamp).all()

    @staticmethod
    def get_last_event(session: Session, employee_id: int) -> Optional[TimeFenceLog]:
        """Get most recent time fence event for employee"""
        return session.query(TimeFenceLog).filter(
            TimeFenceLog.employee_id == employee_id
        ).order_by(desc(TimeFenceLog.event_timestamp)).first()

    @staticmethod
    def get_unauthorized_exits(session: Session, target_date: date) -> List[TimeFenceLog]:
        """Get all unauthorized exits for a date"""
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        return session.query(TimeFenceLog).filter(
            and_(
                TimeFenceLog.event_type == TimeFenceEventType.EXIT,
                TimeFenceLog.is_authorized == False,
                TimeFenceLog.event_timestamp >= start_dt,
                TimeFenceLog.event_timestamp <= end_dt
            )
        ).all()

    @staticmethod
    def get_by_date_range(session: Session, employee_id: int, start_date: date, end_date: date) -> List[TimeFenceLog]:
        """Get time fence logs for date range"""
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        
        return session.query(TimeFenceLog).filter(
            and_(
                TimeFenceLog.employee_id == employee_id,
                TimeFenceLog.event_timestamp >= start_dt,
                TimeFenceLog.event_timestamp <= end_dt
            )
        ).order_by(TimeFenceLog.event_timestamp).all()

    @staticmethod
    def cleanup_old_logs(session: Session, days_to_keep: int = 90) -> int:
        """Delete logs older than specified days"""
        try:
            cutoff_dt = datetime.utcnow() - timedelta(days=days_to_keep)
            old_logs = session.query(TimeFenceLog).filter(
                TimeFenceLog.event_timestamp < cutoff_dt
            ).delete()
            session.commit()
            logger.info(f"Cleaned up {old_logs} old time fence logs")
            return old_logs
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up logs: {str(e)}")
            raise


# ============================================================================
# Helper Data Classes
# ============================================================================

@dataclass
class EmployeeSessionState:
    """
    In-memory session state for tracking employee presence in frame
    Used to determine check-in/out without database queries per frame
    """
    employee_id: int
    name: str
    first_detection_time: datetime
    last_detection_time: datetime
    detection_count: int = 1
    last_detection_camera: str = ""
    detection_confidence: float = 0.0
    is_in_frame: bool = True
    session_timeout_seconds: int = 300  # 5 minutes
    
    def is_expired(self) -> bool:
        """Check if session has timed out"""
        time_since_last = (datetime.utcnow() - self.last_detection_time).total_seconds()
        return time_since_last > self.session_timeout_seconds
    
    def update_detection(self, camera_id: str, confidence: float) -> None:
        """Update session with new detection"""
        self.last_detection_time = datetime.utcnow()
        self.detection_count += 1
        self.last_detection_camera = camera_id
        self.detection_confidence = max(self.detection_confidence, confidence)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'employee_id': self.employee_id,
            'name': self.name,
            'first_detection_time': self.first_detection_time.isoformat(),
            'last_detection_time': self.last_detection_time.isoformat(),
            'detection_count': self.detection_count,
            'last_detection_camera': self.last_detection_camera,
            'detection_confidence': self.detection_confidence,
            'is_in_frame': self.is_in_frame
        }


@dataclass
class AttendanceCheckInResult:
    """Result of check-in processing"""
    success: bool
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    check_in_time: Optional[datetime] = None
    is_late: bool = False
    message: str = ""
    record_id: Optional[int] = None


@dataclass
class AttendanceCheckOutResult:
    """Result of check-out processing"""
    success: bool
    employee_id: Optional[int] = None
    check_out_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    message: str = ""
    exit_reason: ExitReason = ExitReason.UNKNOWN
