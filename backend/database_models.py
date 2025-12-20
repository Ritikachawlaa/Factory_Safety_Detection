"""
SQLAlchemy ORM Models for Factory AI SaaS
Schemas for all 4 modules: Identity, Vehicle, Attendance, Occupancy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database connection
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./factory_ai.db'  # Default: SQLite for development
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ============================================================================
# MODULE 1 & 3: IDENTITY & ATTENDANCE
# ============================================================================

class Employee(Base):
    """Employee database with face embeddings."""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True)
    name = Column(String(100), index=True)
    email = Column(String(100))
    phone = Column(String(20))
    department = Column(String(50))
    shift_start = Column(String(5))  # HH:MM
    shift_end = Column(String(5))
    grace_period_minutes = Column(Integer, default=5)
    aws_face_id = Column(String(100))  # AWS Rekognition Face ID
    enrollment_date = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AttendanceRecord(Base):
    """Attendance logs for payroll and analytics."""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), index=True)
    employee_name = Column(String(100))
    
    check_in_time = Column(DateTime, index=True)
    check_out_time = Column(DateTime, nullable=True)
    
    # Status: PRESENT, LATE, EARLY_EXIT, ABSENT
    status = Column(String(20), index=True)
    
    grace_period_used = Column(Integer, default=0)  # minutes
    is_early_exit = Column(Boolean, default=False)
    is_manual_override = Column(Boolean, default=False)
    
    aws_face_confidence = Column(Float)  # 0-100
    track_id = Column(Integer)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now, index=True)


class FaceCache(Base):
    """Cache for recognized faces (optional for debugging)."""
    __tablename__ = "face_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True)
    employee_id = Column(String(50), index=True)
    employee_name = Column(String(100))
    confidence = Column(Float)
    
    frame_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    ttl_expires = Column(DateTime)  # Cache expiration


# ============================================================================
# MODULE 2: VEHICLE & ANPR
# ============================================================================

class Vehicle(Base):
    """Whitelisted/blacklisted vehicles."""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, index=True)
    vehicle_type = Column(String(20))  # car, truck, bus, motorcycle
    
    owner_name = Column(String(100))
    owner_contact = Column(String(50))
    
    # Status: WHITELIST, BLACKLIST, UNKNOWN
    status = Column(String(20), default='UNKNOWN')
    
    allowed_until = Column(DateTime, nullable=True)  # Temporary access
    reason = Column(Text, nullable=True)
    
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    entry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)


class VehicleLog(Base):
    """Detailed vehicle movement logs."""
    __tablename__ = "vehicle_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True)
    
    plate_number = Column(String(20), index=True)
    vehicle_type = Column(String(20))
    
    entry_time = Column(DateTime, index=True)
    exit_time = Column(DateTime, nullable=True)
    
    ocr_confidence = Column(Float)  # OCR confidence 0-100
    status = Column(String(20))  # ALLOWED, BLOCKED, UNKNOWN
    
    created_at = Column(DateTime, default=datetime.now, index=True)


# ============================================================================
# MODULE 4: OCCUPANCY & PEOPLE COUNTING
# ============================================================================

class OccupancyLog(Base):
    """Real-time occupancy logs."""
    __tablename__ = "occupancy_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), index=True)
    
    current_occupancy = Column(Integer)  # Net people count
    entries_count = Column(Integer, default=0)
    exits_count = Column(Integer, default=0)
    
    people_detected = Column(Integer)  # In this frame
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    frame_id = Column(Integer)


class OccupancyDailyAggregate(Base):
    """Hourly and daily occupancy summaries."""
    __tablename__ = "occupancy_daily_aggregate"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), index=True)
    
    occupancy_date = Column(String(10), index=True)  # YYYY-MM-DD
    hour = Column(Integer)  # 0-23
    
    avg_occupancy = Column(Float)
    max_occupancy = Column(Integer)
    min_occupancy = Column(Integer)
    
    total_entries = Column(Integer)
    total_exits = Column(Integer)
    
    peak_time = Column(String(5))  # HH:MM when occupancy peaked
    
    created_at = Column(DateTime, default=datetime.now)


# ============================================================================
# SYSTEM & MONITORING
# ============================================================================

class SystemMetric(Base):
    """System performance and health metrics."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    frame_id = Column(Integer)
    processing_time_ms = Column(Float)  # ms
    
    gpu_memory_used = Column(Float, nullable=True)  # MB
    cpu_usage = Column(Float, nullable=True)  # %
    
    faces_processed = Column(Integer)
    vehicles_processed = Column(Integer)
    
    aws_calls = Column(Integer, default=0)
    aws_cost_estimated = Column(Float, default=0.0)
    
    timestamp = Column(DateTime, default=datetime.now, index=True)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
