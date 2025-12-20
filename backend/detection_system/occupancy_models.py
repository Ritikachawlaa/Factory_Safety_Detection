"""
Module 4: People Counting & Occupancy Analytics
Database Models and Data Access Objects for Occupancy Tracking
Author: Factory Safety Detection Team
Date: 2025
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
import math

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text, Date, Time,
    ForeignKey, Index, Enum as SQLEnum, UniqueConstraint, CheckConstraint,
    and_, or_, desc, func, JSON
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
logger = logging.getLogger(__name__)


class LineDirection(str, Enum):
    """Direction types for virtual lines"""
    ENTRY = "entry"          # Entry line (e.g., entrance)
    EXIT = "exit"            # Exit line (e.g., exit door)
    BIDIRECTIONAL = "bidirectional"  # Counts both directions


class OccupancyAlertType(str, Enum):
    """Types of occupancy alerts"""
    CAPACITY_WARNING = "capacity_warning"    # Approaching max capacity
    CAPACITY_EXCEEDED = "capacity_exceeded"  # Over max capacity
    ANOMALY_DETECTED = "anomaly_detected"    # Unusual pattern
    NEGATIVE_COUNT = "negative_count"        # Count went below zero
    EQUIPMENT_FAILURE = "equipment_failure"  # Camera/detection failure


# ============================================================================
# Database Models
# ============================================================================

class Camera(Base):
    """
    Camera configuration for occupancy tracking
    Each camera can have multiple virtual lines
    """
    __tablename__ = 'cameras_occupancy'

    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), unique=True, nullable=False, index=True)
    camera_name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=True)  # e.g., "Gate A", "Floor 1"
    camera_type = Column(String(50), nullable=True)  # "entry_only", "exit_only", "bidirectional"
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    max_occupancy = Column(Integer, nullable=True)  # Optional capacity limit
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lines = relationship("VirtualLine", back_populates="camera")
    occupancy_logs = relationship("OccupancyLog", back_populates="camera")
    hourly_data = relationship("HourlyOccupancy", back_populates="camera")
    daily_data = relationship("DailyOccupancy", back_populates="camera")
    monthly_data = relationship("MonthlyOccupancy", back_populates="camera")
    alerts = relationship("OccupancyAlert", back_populates="camera")

    __table_args__ = (
        Index('idx_camera_active', 'is_active'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'location': self.location,
            'camera_type': self.camera_type,
            'is_active': self.is_active,
            'max_occupancy': self.max_occupancy,
            'resolution': f"{self.resolution_width}x{self.resolution_height}" if self.resolution_width else None
        }


class VirtualLine(Base):
    """
    Virtual line for detecting entry/exit
    Defined by two points (x1, y1) and (x2, y2) in pixel coordinates
    """
    __tablename__ = 'virtual_lines'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    line_name = Column(String(100), nullable=False)
    
    # Line endpoints (pixel coordinates)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    
    # Direction configuration
    direction = Column(SQLEnum(LineDirection), default=LineDirection.BIDIRECTIONAL)
    # For directional lines: positive side (e.g., "top" for entry)
    positive_direction = Column(String(50), nullable=True)  # e.g., "top_to_bottom"
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    line_color = Column(String(7), default="#00FF00")  # Hex color for visualization
    thickness = Column(Integer, default=2)
    confidence_threshold = Column(Float, default=0.5)  # Min confidence for crossing
    
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="lines")

    __table_args__ = (
        Index('idx_line_camera_active', 'camera_id', 'is_active'),
    )

    def get_line_vector(self) -> Tuple[float, float]:
        """Get normalized line direction vector"""
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        length = math.sqrt(dx**2 + dy**2)
        if length == 0:
            return (0, 0)
        return (dx / length, dy / length)

    def get_perpendicular_vector(self) -> Tuple[float, float]:
        """Get perpendicular vector to the line (pointing left)"""
        dx, dy = self.get_line_vector()
        return (-dy, dx)  # Rotate 90 degrees left

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'line_name': self.line_name,
            'endpoints': f"({self.x1},{self.y1}) to ({self.x2},{self.y2})",
            'direction': self.direction.value,
            'is_active': self.is_active
        }


class OccupancyLog(Base):
    """
    Real-time occupancy log (one entry per aggregate period, typically 1-5 minutes)
    This is the raw data that gets aggregated into hourly/daily/monthly
    """
    __tablename__ = 'occupancy_logs'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    
    # Count data
    entry_count = Column(Integer, default=0)      # People entered in this period
    exit_count = Column(Integer, default=0)       # People exited in this period
    net_occupancy = Column(Integer, default=0)    # Current occupancy (entries - exits)
    
    # Timestamp of this log entry
    log_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    period_duration_seconds = Column(Integer, default=60)  # Duration this log covers
    
    # Quality metrics
    detection_confidence = Column(Float, default=0.0)  # Average confidence in detections
    tracked_persons = Column(Integer, default=0)  # Number of unique people tracked
    
    # Additional metadata
    notes = Column(Text, nullable=True)
    is_manual_calibration = Column(Boolean, default=False)  # HR manually set count
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    camera = relationship("Camera", back_populates="occupancy_logs")

    __table_args__ = (
        Index('idx_occupancy_camera_timestamp', 'camera_id', 'log_timestamp'),
        Index('idx_occupancy_timestamp', 'log_timestamp'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'entry_count': self.entry_count,
            'exit_count': self.exit_count,
            'net_occupancy': self.net_occupancy,
            'timestamp': self.log_timestamp.isoformat(),
            'tracked_persons': self.tracked_persons
        }


class HourlyOccupancy(Base):
    """
    Hourly aggregated occupancy (aggregated from OccupancyLog)
    Provides faster queries for dashboard and reports
    """
    __tablename__ = 'hourly_occupancy'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    
    hour_date = Column(Date, nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    
    # Aggregated counts
    total_entries = Column(Integer, default=0)
    total_exits = Column(Integer, default=0)
    avg_occupancy = Column(Float, default=0.0)      # Average occupancy during hour
    peak_occupancy = Column(Integer, default=0)     # Max occupancy in hour
    min_occupancy = Column(Integer, default=0)      # Min occupancy in hour
    
    # Quality metrics
    avg_detection_confidence = Column(Float, default=0.0)
    unique_persons_count = Column(Integer, default=0)  # Unique people in hour
    
    # Status flags
    is_complete = Column(Boolean, default=True)  # Is this hour's data complete?
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="hourly_data")

    __table_args__ = (
        Index('idx_hourly_camera_hour', 'camera_id', 'hour_date', 'hour_of_day'),
        Index('idx_hourly_date', 'hour_date'),
        UniqueConstraint('camera_id', 'hour_date', 'hour_of_day', name='unique_hourly_occupancy'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'camera_id': self.camera_id,
            'hour': f"{self.hour_date.isoformat()} {self.hour_of_day:02d}:00",
            'entries': self.total_entries,
            'exits': self.total_exits,
            'avg_occupancy': round(self.avg_occupancy, 2),
            'peak_occupancy': self.peak_occupancy,
            'unique_persons': self.unique_persons_count
        }


class DailyOccupancy(Base):
    """
    Daily aggregated occupancy (aggregated from HourlyOccupancy)
    """
    __tablename__ = 'daily_occupancy'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    
    occupancy_date = Column(Date, nullable=False, index=True)
    
    # Aggregated counts
    total_entries = Column(Integer, default=0)
    total_exits = Column(Integer, default=0)
    avg_occupancy = Column(Float, default=0.0)      # Average across day
    peak_occupancy = Column(Integer, default=0)     # Max in day
    peak_hour = Column(Integer, nullable=True)      # Which hour had peak
    min_occupancy = Column(Integer, default=0)      # Min in day
    
    # Quality metrics
    avg_detection_confidence = Column(Float, default=0.0)
    unique_persons_count = Column(Integer, default=0)  # Unique people in day
    
    # Activity classification
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="daily_data")

    __table_args__ = (
        Index('idx_daily_camera_date', 'camera_id', 'occupancy_date'),
        Index('idx_daily_date', 'occupancy_date'),
        UniqueConstraint('camera_id', 'occupancy_date', name='unique_daily_occupancy'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'camera_id': self.camera_id,
            'date': self.occupancy_date.isoformat(),
            'entries': self.total_entries,
            'exits': self.total_exits,
            'avg_occupancy': round(self.avg_occupancy, 2),
            'peak_occupancy': self.peak_occupancy,
            'peak_hour': self.peak_hour,
            'unique_persons': self.unique_persons_count
        }


class MonthlyOccupancy(Base):
    """
    Monthly aggregated occupancy (aggregated from DailyOccupancy)
    For long-term planning and compliance reports
    """
    __tablename__ = 'monthly_occupancy'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    
    # Aggregated counts
    total_entries = Column(Integer, default=0)
    total_exits = Column(Integer, default=0)
    avg_daily_occupancy = Column(Float, default=0.0)   # Average across all days
    peak_day_occupancy = Column(Integer, default=0)    # Peak occupancy in month
    peak_date = Column(Date, nullable=True)            # Which date had peak
    
    # Per-day statistics
    total_working_days = Column(Integer, default=0)    # Non-weekend, non-holiday
    total_weekend_days = Column(Integer, default=0)
    total_holiday_days = Column(Integer, default=0)
    
    # Quality metrics
    avg_detection_confidence = Column(Float, default=0.0)
    unique_persons_count = Column(Integer, default=0)  # Unique people in month
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="monthly_data")

    __table_args__ = (
        Index('idx_monthly_camera_date', 'camera_id', 'year', 'month'),
        Index('idx_monthly_date', 'year', 'month'),
        UniqueConstraint('camera_id', 'year', 'month', name='unique_monthly_occupancy'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'camera_id': self.camera_id,
            'period': f"{self.year}-{self.month:02d}",
            'entries': self.total_entries,
            'exits': self.total_exits,
            'avg_daily_occupancy': round(self.avg_daily_occupancy, 2),
            'peak_occupancy': self.peak_day_occupancy,
            'unique_persons': self.unique_persons_count
        }


class OccupancyAlert(Base):
    """
    Alerts for occupancy anomalies (capacity exceeded, detection failure, etc.)
    """
    __tablename__ = 'occupancy_alerts'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras_occupancy.id'), nullable=False, index=True)
    
    alert_type = Column(SQLEnum(OccupancyAlertType), nullable=False, index=True)
    current_occupancy = Column(Integer, nullable=True)
    threshold_value = Column(Integer, nullable=True)  # What triggered alert
    
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, index=True)
    
    alert_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_timestamp = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="alerts")

    __table_args__ = (
        Index('idx_alert_camera_timestamp', 'camera_id', 'alert_timestamp'),
        Index('idx_alert_type_resolved', 'alert_type', 'is_resolved'),
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'alert_type': self.alert_type.value,
            'current_occupancy': self.current_occupancy,
            'message': self.message,
            'is_resolved': self.is_resolved,
            'timestamp': self.alert_timestamp.isoformat()
        }


# ============================================================================
# Data Access Objects (DAOs)
# ============================================================================

class CameraDAO:
    """Data Access Object for Camera operations"""

    @staticmethod
    def create(session: Session, camera_data: Dict) -> Camera:
        """Create new camera"""
        try:
            camera = Camera(**camera_data)
            session.add(camera)
            session.commit()
            logger.info(f"Created camera: {camera.camera_id}")
            return camera
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating camera: {str(e)}")
            raise

    @staticmethod
    def get_by_id(session: Session, camera_id: int) -> Optional[Camera]:
        """Get camera by ID"""
        return session.query(Camera).filter(Camera.id == camera_id).first()

    @staticmethod
    def get_by_camera_id(session: Session, camera_id: str) -> Optional[Camera]:
        """Get camera by camera_id string"""
        return session.query(Camera).filter(Camera.camera_id == camera_id).first()

    @staticmethod
    def get_all_active(session: Session) -> List[Camera]:
        """Get all active cameras"""
        return session.query(Camera).filter(Camera.is_active == True).all()

    @staticmethod
    def update(session: Session, camera_id: int, update_data: Dict) -> Optional[Camera]:
        """Update camera"""
        try:
            camera = CameraDAO.get_by_id(session, camera_id)
            if not camera:
                return None
            for key, value in update_data.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            session.commit()
            return camera
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating camera: {str(e)}")
            raise


class VirtualLineDAO:
    """Data Access Object for VirtualLine operations"""

    @staticmethod
    def create(session: Session, line_data: Dict) -> VirtualLine:
        """Create new virtual line"""
        try:
            line = VirtualLine(**line_data)
            session.add(line)
            session.commit()
            logger.info(f"Created virtual line: {line.line_name}")
            return line
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating line: {str(e)}")
            raise

    @staticmethod
    def get_by_id(session: Session, line_id: int) -> Optional[VirtualLine]:
        """Get line by ID"""
        return session.query(VirtualLine).filter(VirtualLine.id == line_id).first()

    @staticmethod
    def get_by_camera(session: Session, camera_id: int) -> List[VirtualLine]:
        """Get all active lines for a camera"""
        return session.query(VirtualLine).filter(
            and_(VirtualLine.camera_id == camera_id, VirtualLine.is_active == True)
        ).all()

    @staticmethod
    def get_all_active(session: Session) -> List[VirtualLine]:
        """Get all active lines"""
        return session.query(VirtualLine).filter(VirtualLine.is_active == True).all()

    @staticmethod
    def update(session: Session, line_id: int, update_data: Dict) -> Optional[VirtualLine]:
        """Update line"""
        try:
            line = VirtualLineDAO.get_by_id(session, line_id)
            if not line:
                return None
            for key, value in update_data.items():
                if hasattr(line, key):
                    setattr(line, key, value)
            session.commit()
            return line
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating line: {str(e)}")
            raise


class OccupancyLogDAO:
    """Data Access Object for OccupancyLog operations"""

    @staticmethod
    def create(session: Session, log_data: Dict) -> OccupancyLog:
        """Create new occupancy log entry"""
        try:
            log = OccupancyLog(**log_data)
            session.add(log)
            session.commit()
            logger.debug(f"Created occupancy log for camera {log.camera_id}")
            return log
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating log: {str(e)}")
            raise

    @staticmethod
    def get_latest(session: Session, camera_id: int) -> Optional[OccupancyLog]:
        """Get most recent log entry for camera"""
        return session.query(OccupancyLog).filter(
            OccupancyLog.camera_id == camera_id
        ).order_by(desc(OccupancyLog.log_timestamp)).first()

    @staticmethod
    def get_time_range(session: Session, camera_id: int, start_time: datetime, end_time: datetime) -> List[OccupancyLog]:
        """Get logs for time range"""
        return session.query(OccupancyLog).filter(
            and_(
                OccupancyLog.camera_id == camera_id,
                OccupancyLog.log_timestamp >= start_time,
                OccupancyLog.log_timestamp <= end_time
            )
        ).order_by(OccupancyLog.log_timestamp).all()

    @staticmethod
    def get_for_aggregation(session: Session, camera_id: int, since_timestamp: datetime) -> List[OccupancyLog]:
        """Get logs not yet aggregated (for background task)"""
        return session.query(OccupancyLog).filter(
            and_(
                OccupancyLog.camera_id == camera_id,
                OccupancyLog.log_timestamp >= since_timestamp
            )
        ).order_by(OccupancyLog.log_timestamp).all()

    @staticmethod
    def cleanup_old_logs(session: Session, days_to_keep: int = 30) -> int:
        """Delete old logs (keep aggregated data)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            old_logs = session.query(OccupancyLog).filter(
                OccupancyLog.log_timestamp < cutoff_date
            ).delete()
            session.commit()
            logger.info(f"Cleaned up {old_logs} old occupancy logs")
            return old_logs
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning logs: {str(e)}")
            raise


class HourlyOccupancyDAO:
    """Data Access Object for HourlyOccupancy operations"""

    @staticmethod
    def create_or_update(session: Session, camera_id: int, hour_date: date, hour_of_day: int, data: Dict) -> HourlyOccupancy:
        """Create or update hourly record"""
        try:
            record = session.query(HourlyOccupancy).filter(
                and_(
                    HourlyOccupancy.camera_id == camera_id,
                    HourlyOccupancy.hour_date == hour_date,
                    HourlyOccupancy.hour_of_day == hour_of_day
                )
            ).first()

            if record:
                for key, value in data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = datetime.utcnow()
            else:
                record = HourlyOccupancy(
                    camera_id=camera_id,
                    hour_date=hour_date,
                    hour_of_day=hour_of_day,
                    **data
                )
                session.add(record)

            session.commit()
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating hourly record: {str(e)}")
            raise

    @staticmethod
    def get_date_range(session: Session, camera_id: int, start_date: date, end_date: date) -> List[HourlyOccupancy]:
        """Get hourly data for date range"""
        return session.query(HourlyOccupancy).filter(
            and_(
                HourlyOccupancy.camera_id == camera_id,
                HourlyOccupancy.hour_date >= start_date,
                HourlyOccupancy.hour_date <= end_date
            )
        ).order_by(HourlyOccupancy.hour_date, HourlyOccupancy.hour_of_day).all()

    @staticmethod
    def get_by_hour(session: Session, camera_id: int, hour_date: date) -> List[HourlyOccupancy]:
        """Get all hours for a day"""
        return session.query(HourlyOccupancy).filter(
            and_(
                HourlyOccupancy.camera_id == camera_id,
                HourlyOccupancy.hour_date == hour_date
            )
        ).order_by(HourlyOccupancy.hour_of_day).all()


class DailyOccupancyDAO:
    """Data Access Object for DailyOccupancy operations"""

    @staticmethod
    def create_or_update(session: Session, camera_id: int, occupancy_date: date, data: Dict) -> DailyOccupancy:
        """Create or update daily record"""
        try:
            record = session.query(DailyOccupancy).filter(
                and_(
                    DailyOccupancy.camera_id == camera_id,
                    DailyOccupancy.occupancy_date == occupancy_date
                )
            ).first()

            if record:
                for key, value in data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = datetime.utcnow()
            else:
                record = DailyOccupancy(
                    camera_id=camera_id,
                    occupancy_date=occupancy_date,
                    **data
                )
                session.add(record)

            session.commit()
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating daily record: {str(e)}")
            raise

    @staticmethod
    def get_date_range(session: Session, camera_id: int, start_date: date, end_date: date) -> List[DailyOccupancy]:
        """Get daily data for date range"""
        return session.query(DailyOccupancy).filter(
            and_(
                DailyOccupancy.camera_id == camera_id,
                DailyOccupancy.occupancy_date >= start_date,
                DailyOccupancy.occupancy_date <= end_date
            )
        ).order_by(desc(DailyOccupancy.occupancy_date)).all()

    @staticmethod
    def get_month(session: Session, camera_id: int, year: int, month: int) -> List[DailyOccupancy]:
        """Get daily data for month"""
        return session.query(DailyOccupancy).filter(
            and_(
                DailyOccupancy.camera_id == camera_id,
                func.extract('year', DailyOccupancy.occupancy_date) == year,
                func.extract('month', DailyOccupancy.occupancy_date) == month
            )
        ).order_by(desc(DailyOccupancy.occupancy_date)).all()


class MonthlyOccupancyDAO:
    """Data Access Object for MonthlyOccupancy operations"""

    @staticmethod
    def create_or_update(session: Session, camera_id: int, year: int, month: int, data: Dict) -> MonthlyOccupancy:
        """Create or update monthly record"""
        try:
            record = session.query(MonthlyOccupancy).filter(
                and_(
                    MonthlyOccupancy.camera_id == camera_id,
                    MonthlyOccupancy.year == year,
                    MonthlyOccupancy.month == month
                )
            ).first()

            if record:
                for key, value in data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = datetime.utcnow()
            else:
                record = MonthlyOccupancy(
                    camera_id=camera_id,
                    year=year,
                    month=month,
                    **data
                )
                session.add(record)

            session.commit()
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating monthly record: {str(e)}")
            raise

    @staticmethod
    def get_year(session: Session, camera_id: int, year: int) -> List[MonthlyOccupancy]:
        """Get all months for a year"""
        return session.query(MonthlyOccupancy).filter(
            and_(
                MonthlyOccupancy.camera_id == camera_id,
                MonthlyOccupancy.year == year
            )
        ).order_by(MonthlyOccupancy.month).all()


class OccupancyAlertDAO:
    """Data Access Object for OccupancyAlert operations"""

    @staticmethod
    def create(session: Session, alert_data: Dict) -> OccupancyAlert:
        """Create new alert"""
        try:
            alert = OccupancyAlert(**alert_data)
            session.add(alert)
            session.commit()
            logger.warning(f"Created alert: {alert.alert_type.value} for camera {alert.camera_id}")
            return alert
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating alert: {str(e)}")
            raise

    @staticmethod
    def get_active_alerts(session: Session, camera_id: Optional[int] = None) -> List[OccupancyAlert]:
        """Get unresolved alerts"""
        query = session.query(OccupancyAlert).filter(OccupancyAlert.is_resolved == False)
        if camera_id:
            query = query.filter(OccupancyAlert.camera_id == camera_id)
        return query.order_by(desc(OccupancyAlert.alert_timestamp)).all()

    @staticmethod
    def resolve_alert(session: Session, alert_id: int) -> Optional[OccupancyAlert]:
        """Mark alert as resolved"""
        try:
            alert = session.query(OccupancyAlert).filter(OccupancyAlert.id == alert_id).first()
            if alert:
                alert.is_resolved = True
                alert.resolved_timestamp = datetime.utcnow()
                session.commit()
            return alert
        except Exception as e:
            session.rollback()
            logger.error(f"Error resolving alert: {str(e)}")
            raise


# ============================================================================
# Helper Data Classes
# ============================================================================

@dataclass
class LineCrossingData:
    """Data for a single line crossing event"""
    track_id: int
    timestamp: datetime
    direction: str  # "entry" or "exit"
    confidence: float
    centroid_position: Tuple[float, float]
    line_id: int


@dataclass
class OccupancyState:
    """Current occupancy state for a camera"""
    camera_id: int
    current_occupancy: int
    total_entries: int
    total_exits: int
    last_updated: datetime
    unique_persons: set  # Set of track_ids currently in frame
    
    def add_entry(self) -> None:
        """Record entry"""
        self.total_entries += 1
        self.current_occupancy += 1
        self.last_updated = datetime.utcnow()
    
    def add_exit(self) -> None:
        """Record exit"""
        self.total_exits += 1
        self.current_occupancy = max(0, self.current_occupancy - 1)  # Never negative
        self.last_updated = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'camera_id': self.camera_id,
            'current_occupancy': self.current_occupancy,
            'total_entries': self.total_entries,
            'total_exits': self.total_exits,
            'unique_persons': len(self.unique_persons),
            'last_updated': self.last_updated.isoformat()
        }
