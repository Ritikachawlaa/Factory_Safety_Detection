"""
Module 3: Attendance Shift Integrity Service
Implements shift-based attendance validation with early exit detection and double-entry prevention.

Key Features:
- Grace period validation (late entry detection)
- Early exit detection (check-out time vs shift end time)
- Double-entry prevention (face recognition within 12 hours)
- Shift status computation
"""

import logging
from datetime import datetime, timedelta, date, time
from typing import Dict, Optional, Tuple, List
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AttendanceStatus(str, Enum):
    """Attendance status enumeration"""
    PRESENT = "PRESENT"
    LATE = "LATE"
    EARLY_EXIT = "EARLY_EXIT"
    ABSENT = "ABSENT"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class ShiftIntegrityService:
    """
    Service to handle shift-based attendance validation.
    Enforces grace periods, detects early exits, and prevents duplicate entries.
    """
    
    # In-memory cache for recent check-ins (employee_id -> list of check-in records)
    RECENT_CHECKINS = {}
    DOUBLE_ENTRY_WINDOW_HOURS = 12
    
    def __init__(self, db_session=None):
        """
        Initialize the shift integrity service.
        
        Args:
            db_session: SQLAlchemy database session for persistence
        """
        self.db = db_session
        logger.info("✅ ShiftIntegrityService initialized")
    
    def process_shift_status(
        self,
        employee_id: int,
        check_in_time: datetime,
        check_out_time: Optional[datetime] = None,
        shift_data: Optional[Dict] = None
    ) -> Dict:
        """
        Main function to process shift status for an employee.
        
        Handles:
        1. Grace period validation (LATE detection)
        2. Early exit detection (check-out before shift end)
        3. Double-entry prevention (ignore if checked in within last 12 hours)
        
        Args:
            employee_id: Employee ID
            check_in_time: Check-in datetime
            check_out_time: Optional check-out datetime
            shift_data: Shift information dict with keys: start_time, end_time, grace_period_minutes
        
        Returns:
            {
                'employee_id': int,
                'status': AttendanceStatus,
                'check_in_time': datetime,
                'check_out_time': Optional[datetime],
                'is_late': bool,
                'is_early_exit': bool,
                'grace_period_applied': bool,
                'message': str,
                'flagged_for_review': bool
            }
        """
        try:
            logger.info(f"🔄 Processing shift status for employee {employee_id}")
            
            # Step 1: DOUBLE-ENTRY PREVENTION
            if self._is_duplicate_checkin(employee_id, check_in_time):
                logger.warning(f"⚠️ Duplicate check-in detected for employee {employee_id} within last 12 hours")
                return {
                    'employee_id': employee_id,
                    'status': AttendanceStatus.PRESENT,
                    'check_in_time': check_in_time,
                    'check_out_time': check_out_time,
                    'is_late': False,
                    'is_early_exit': False,
                    'grace_period_applied': False,
                    'message': 'Duplicate check-in ignored (already checked in today)',
                    'flagged_for_review': False,
                    'skipped_duplicate': True
                }
            
            # Record this check-in
            self._record_checkin(employee_id, check_in_time)
            
            # Step 2: GRACE PERIOD VALIDATION (Late Entry Detection)
            status = AttendanceStatus.PRESENT
            is_late = False
            grace_period_applied = False
            
            if shift_data:
                shift_start = self._parse_time(shift_data.get('start_time'))
                shift_end = self._parse_time(shift_data.get('end_time'))
                grace_period_minutes = shift_data.get('grace_period_minutes', 5)
                
                # Check if within shift hours
                check_in_time_only = check_in_time.time()
                
                if check_in_time_only < shift_start:
                    logger.info(f"✓ Employee {employee_id} checked in early (before shift start)")
                elif check_in_time_only > shift_end:
                    logger.warning(f"⚠️ Employee {employee_id} checked in after shift end")
                    status = AttendanceStatus.ABSENT
                else:
                    # Within shift hours - check grace period
                    grace_time = self._add_minutes_to_time(shift_start, grace_period_minutes)
                    
                    if check_in_time_only > grace_time:
                        status = AttendanceStatus.LATE
                        is_late = True
                        grace_period_applied = True
                        logger.warning(f"⚠️ Employee {employee_id} is LATE (check-in at {check_in_time_only}, grace expired at {grace_time})")
                    else:
                        logger.info(f"✓ Employee {employee_id} checked in ON TIME")
            
            # Step 3: EARLY EXIT DETECTION (Check-out before shift end)
            is_early_exit = False
            if check_out_time and shift_data:
                shift_end = self._parse_time(shift_data.get('end_time'))
                check_out_time_only = check_out_time.time()
                
                if check_out_time_only < shift_end:
                    is_early_exit = True
                    logger.warning(f"⚠️ Employee {employee_id} EARLY EXIT detected (check-out at {check_out_time_only}, shift ends at {shift_end})")
            
            result = {
                'employee_id': employee_id,
                'status': status,
                'check_in_time': check_in_time,
                'check_out_time': check_out_time,
                'is_late': is_late,
                'is_early_exit': is_early_exit,
                'grace_period_applied': grace_period_applied,
                'message': self._get_status_message(status, is_late, is_early_exit),
                'flagged_for_review': is_late or is_early_exit,
                'skipped_duplicate': False
            }
            
            logger.info(f"✅ Shift status processing completed for employee {employee_id}: {status.value}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Error processing shift status: {e}", exc_info=True)
            return {
                'employee_id': employee_id,
                'status': AttendanceStatus.ABSENT,
                'error': str(e),
                'flagged_for_review': True
            }
    
    def _is_duplicate_checkin(self, employee_id: int, current_time: datetime) -> bool:
        """
        Check if employee has already checked in within the last 12 hours.
        Double-entry prevention for face recognition.
        
        Args:
            employee_id: Employee ID
            current_time: Current check-in time
        
        Returns:
            True if duplicate check-in detected, False otherwise
        """
        if employee_id not in self.RECENT_CHECKINS:
            return False
        
        recent = self.RECENT_CHECKINS[employee_id]
        cutoff_time = current_time - timedelta(hours=self.DOUBLE_ENTRY_WINDOW_HOURS)
        
        # Check if any recent check-in is within the window
        for checkin_time in recent:
            if checkin_time > cutoff_time:
                logger.info(f"🔍 Duplicate check-in: Employee {employee_id} last checked in at {checkin_time}")
                return True
        
        return False
    
    def _record_checkin(self, employee_id: int, checkin_time: datetime) -> None:
        """
        Record a check-in time in the in-memory cache.
        
        Args:
            employee_id: Employee ID
            checkin_time: Check-in datetime
        """
        if employee_id not in self.RECENT_CHECKINS:
            self.RECENT_CHECKINS[employee_id] = []
        
        # Keep only last 20 check-ins and clean up old ones
        cutoff = checkin_time - timedelta(hours=self.DOUBLE_ENTRY_WINDOW_HOURS)
        self.RECENT_CHECKINS[employee_id] = [
            ct for ct in self.RECENT_CHECKINS[employee_id] if ct > cutoff
        ]
        self.RECENT_CHECKINS[employee_id].append(checkin_time)
        logger.debug(f"📝 Recorded check-in for employee {employee_id} at {checkin_time}")
    
    def _parse_time(self, time_str) -> time:
        """
        Parse time from string or return as-is if already a time object.
        
        Args:
            time_str: Time as string (HH:MM:SS) or time object
        
        Returns:
            time object
        """
        if isinstance(time_str, time):
            return time_str
        
        if isinstance(time_str, str):
            parts = time_str.split(':')
            return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
        
        return time_str
    
    def _add_minutes_to_time(self, t: time, minutes: int) -> time:
        """
        Add minutes to a time object.
        
        Args:
            t: Time object
            minutes: Minutes to add
        
        Returns:
            New time object with minutes added
        """
        dt = datetime.combine(date.today(), t)
        new_dt = dt + timedelta(minutes=minutes)
        return new_dt.time()
    
    def _get_status_message(self, status: AttendanceStatus, is_late: bool, is_early_exit: bool) -> str:
        """
        Generate a human-readable status message.
        
        Args:
            status: Attendance status
            is_late: Whether employee is late
            is_early_exit: Whether employee left early
        
        Returns:
            Status message string
        """
        if is_early_exit:
            return "Employee left early from shift"
        elif is_late:
            return "Employee checked in after grace period"
        elif status == AttendanceStatus.PRESENT:
            return "Employee checked in on time"
        elif status == AttendanceStatus.ABSENT:
            return "Employee not marked present"
        else:
            return f"Status: {status.value}"
    
    def get_employee_shift_summary(self, employee_id: int, date_range: Tuple[date, date]) -> Dict:
        """
        Get a summary of employee's attendance for a date range.
        Useful for payroll and compliance reports.
        
        Args:
            employee_id: Employee ID
            date_range: Tuple of (start_date, end_date)
        
        Returns:
            {
                'employee_id': int,
                'date_range': str,
                'total_days': int,
                'on_time': int,
                'late': int,
                'early_exits': int,
                'absent': int,
                'on_time_percentage': float
            }
        """
        logger.info(f"📊 Generating shift summary for employee {employee_id}")
        
        # This would query the database in production
        # For now, returning the structure
        return {
            'employee_id': employee_id,
            'date_range': f"{date_range[0]} to {date_range[1]}",
            'total_days': (date_range[1] - date_range[0]).days,
            'on_time': 0,
            'late': 0,
            'early_exits': 0,
            'absent': 0,
            'on_time_percentage': 0.0
        }
    
    def flag_attendance_for_review(self, employee_id: int, reason: str) -> None:
        """
        Flag an attendance record for HR review (manual override needed).
        
        Args:
            employee_id: Employee ID
            reason: Reason for flagging
        """
        logger.warning(f"🚩 Flagged employee {employee_id} for review: {reason}")
        # In production, this would update the database


# ============================================================================
# FastAPI Integration Helper
# ============================================================================

def get_shift_integrity_service(db_session=None) -> ShiftIntegrityService:
    """
    Factory function to create ShiftIntegrityService instance.
    Can be used as FastAPI dependency.
    """
    return ShiftIntegrityService(db_session=db_session)
