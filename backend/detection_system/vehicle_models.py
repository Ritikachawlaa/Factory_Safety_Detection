"""
Vehicle Management SQLAlchemy Models
Handles authorized vehicle database, access logging, and vehicle categorization.

Supports:
- Vehicle registration and authorization status
- Access event logging with entry/exit timestamps
- 90-day data retention policy
- Vehicle categorization (Employee vs Vendor)
- Snapshot storage and audit trail
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, Text, 
    Boolean, Enum, ForeignKey, Index, CheckConstraint, UniqueConstraint,
    Table, and_, or_, func, desc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.types import TypeDecorator
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum as PyEnum
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VehicleModels - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base = declarative_base()


class VehicleStatus(str, PyEnum):
    """Vehicle authorization status."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    PENDING_REVIEW = "pending_review"
    SUSPENDED = "suspended"


class VehicleCategory(str, PyEnum):
    """Vehicle owner category."""
    EMPLOYEE = "employee"
    VENDOR = "vendor"
    GUEST = "guest"
    CONTRACTOR = "contractor"


class AccessStatus(str, PyEnum):
    """Access log status."""
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class AuthorizedVehicle(Base):
    """
    Stores authorized vehicle information.
    
    Schema:
    - id: Primary key
    - plate_number: License plate (unique)
    - owner_name: Owner/company name
    - owner_email: Contact email
    - vehicle_type: Type (car, truck, etc.)
    - vehicle_model: Model/make
    - status: Authorization status
    - category: Owner category (employee, vendor, etc.)
    - department: Department/division
    - phone_number: Contact phone
    - notes: Additional notes
    - snapshot_path: Reference photo of vehicle
    - is_active: Active status flag
    - created_at: Registration timestamp
    - updated_at: Last modification timestamp
    - last_access: Last access timestamp
    """
    
    __tablename__ = 'authorized_vehicles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    owner_name = Column(String(255), nullable=False)
    owner_email = Column(String(255), nullable=True)
    vehicle_type = Column(String(50), nullable=False)  # car, truck, bike, bus, forklift
    vehicle_model = Column(String(255), nullable=True)
    status = Column(String(50), default=VehicleStatus.ALLOWED.value, nullable=False)
    category = Column(String(50), default=VehicleCategory.VENDOR.value, nullable=False)
    department = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    snapshot_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_access = Column(DateTime, nullable=True)
    
    # Relationships
    access_logs = relationship('VehicleAccessLog', back_populates='vehicle', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('allowed', 'blocked', 'pending_review', 'suspended')", name='check_status'),
        CheckConstraint("category IN ('employee', 'vendor', 'guest', 'contractor')", name='check_category'),
        Index('idx_plate_status', 'plate_number', 'status'),
        Index('idx_owner_category', 'owner_name', 'category'),
        Index('idx_vehicle_type', 'vehicle_type'),
        Index('idx_is_active', 'is_active'),
        UniqueConstraint('plate_number', name='uq_plate_number'),
    )
    
    def __repr__(self) -> str:
        return f"<AuthorizedVehicle(plate={self.plate_number}, owner={self.owner_name}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'owner_name': self.owner_name,
            'owner_email': self.owner_email,
            'vehicle_type': self.vehicle_type,
            'vehicle_model': self.vehicle_model,
            'status': self.status,
            'category': self.category,
            'department': self.department,
            'phone_number': self.phone_number,
            'notes': self.notes,
            'snapshot_path': self.snapshot_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_access': self.last_access.isoformat() if self.last_access else None,
        }
    
    def is_authorized(self) -> bool:
        """Check if vehicle is currently authorized."""
        return self.is_active and self.status == VehicleStatus.ALLOWED.value


class VehicleAccessLog(Base):
    """
    Logs every vehicle entry/exit at gate.
    
    Schema:
    - id: Primary key
    - plate_number: License plate (denormalized for queries)
    - vehicle_id: FK to AuthorizedVehicle
    - vehicle_type: Vehicle type (redundant for query speed)
    - entry_time: Gate entry timestamp
    - exit_time: Gate exit timestamp (null if still inside)
    - status: Access status (authorized, blocked, unknown)
    - category: Vehicle owner category
    - is_authorized: Quick boolean flag
    - snapshot_path: Entry snapshot path
    - full_frame_path: Full frame snapshot path
    - entry_point: Entry location/zone
    - location_x, location_y: GPS or spatial coordinates
    - plate_confidence: OCR confidence score
    - notes: Additional notes
    - flagged: Manual review flag
    - created_at: Log creation timestamp
    
    Supports:
    - 90-day data retention
    - Rapid queries by date/time
    - Vehicle traffic analysis
    - Incident investigation
    """
    
    __tablename__ = 'vehicle_access_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_number = Column(String(20), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey('authorized_vehicles.id', ondelete='SET NULL'), nullable=True, index=True)
    vehicle_type = Column(String(50), nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default=AccessStatus.UNKNOWN.value, nullable=False, index=True)
    category = Column(String(50), default=VehicleCategory.VENDOR.value, nullable=False)
    is_authorized = Column(Boolean, default=False, nullable=False, index=True)
    snapshot_path = Column(String(500), nullable=True)
    full_frame_path = Column(String(500), nullable=True)
    entry_point = Column(String(100), nullable=True)
    location_x = Column(Float, nullable=True)
    location_y = Column(Float, nullable=True)
    plate_confidence = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    flagged = Column(Boolean, default=False, nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    vehicle = relationship('AuthorizedVehicle', back_populates='access_logs')
    
    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint("status IN ('authorized', 'blocked', 'unknown')", name='check_access_status'),
        CheckConstraint("category IN ('employee', 'vendor', 'guest', 'contractor')", name='check_access_category'),
        Index('idx_entry_time', 'entry_time'),
        Index('idx_plate_entry_time', 'plate_number', 'entry_time'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_flagged_created', 'flagged', 'created_at'),
        Index('idx_vehicle_type_entry', 'vehicle_type', 'entry_time'),
        Index('idx_date_range', 'entry_time', 'exit_time'),
    )
    
    def __repr__(self) -> str:
        return f"<VehicleAccessLog(plate={self.plate_number}, status={self.status}, entry={self.entry_time})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'vehicle_id': self.vehicle_id,
            'vehicle_type': self.vehicle_type,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'status': self.status,
            'category': self.category,
            'is_authorized': self.is_authorized,
            'snapshot_path': self.snapshot_path,
            'full_frame_path': self.full_frame_path,
            'entry_point': self.entry_point,
            'location_x': self.location_x,
            'location_y': self.location_y,
            'plate_confidence': self.plate_confidence,
            'notes': self.notes,
            'flagged': self.flagged,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def update_exit_time(self):
        """Update exit time and calculate duration."""
        self.exit_time = datetime.utcnow()
        if self.entry_time:
            duration = self.exit_time - self.entry_time
            self.duration_seconds = int(duration.total_seconds())


class AuthorizedVehicleDAO:
    """Data Access Object for AuthorizedVehicle operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, 
              plate_number: str,
              owner_name: str,
              vehicle_type: str,
              status: str = VehicleStatus.ALLOWED.value,
              **kwargs) -> Optional[AuthorizedVehicle]:
        """Create new authorized vehicle record."""
        try:
            vehicle = AuthorizedVehicle(
                plate_number=plate_number,
                owner_name=owner_name,
                vehicle_type=vehicle_type,
                status=status,
                **kwargs
            )
            self.session.add(vehicle)
            self.session.commit()
            logger.info(f"Created vehicle: {plate_number}")
            return vehicle
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating vehicle: {e}")
            return None
    
    def get_by_id(self, vehicle_id: int) -> Optional[AuthorizedVehicle]:
        """Get vehicle by ID."""
        try:
            return self.session.query(AuthorizedVehicle).filter_by(id=vehicle_id).first()
        except Exception as e:
            logger.error(f"Error fetching vehicle: {e}")
            return None
    
    def get_by_plate(self, plate_number: str) -> Optional[AuthorizedVehicle]:
        """Get vehicle by plate number."""
        try:
            return self.session.query(AuthorizedVehicle)\
                .filter_by(plate_number=plate_number, is_active=True).first()
        except Exception as e:
            logger.error(f"Error fetching vehicle by plate: {e}")
            return None
    
    def get_all_authorized(self) -> Dict[str, Dict[str, Any]]:
        """Get all authorized vehicles as dictionary {plate: data}."""
        try:
            vehicles = self.session.query(AuthorizedVehicle)\
                .filter_by(is_active=True).all()
            return {
                v.plate_number: {
                    'owner_name': v.owner_name,
                    'status': v.status,
                    'category': v.category,
                    'vehicle_type': v.vehicle_type,
                }
                for v in vehicles
            }
        except Exception as e:
            logger.error(f"Error fetching authorized vehicles: {e}")
            return {}
    
    def list_by_status(self, status: str, limit: int = 100) -> List[AuthorizedVehicle]:
        """List vehicles by status."""
        try:
            return self.session.query(AuthorizedVehicle)\
                .filter_by(status=status, is_active=True)\
                .order_by(desc(AuthorizedVehicle.created_at))\
                .limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing vehicles by status: {e}")
            return []
    
    def list_by_category(self, category: str, limit: int = 100) -> List[AuthorizedVehicle]:
        """List vehicles by category (employee, vendor, etc.)."""
        try:
            return self.session.query(AuthorizedVehicle)\
                .filter_by(category=category, is_active=True)\
                .order_by(desc(AuthorizedVehicle.created_at))\
                .limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing vehicles by category: {e}")
            return []
    
    def update_status(self, plate_number: str, new_status: str) -> bool:
        """Update vehicle status."""
        try:
            vehicle = self.get_by_plate(plate_number)
            if vehicle:
                vehicle.status = new_status
                vehicle.updated_at = datetime.utcnow()
                self.session.commit()
                logger.info(f"Updated {plate_number} status to {new_status}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating vehicle status: {e}")
            return False
    
    def update_last_access(self, plate_number: str) -> bool:
        """Update last access timestamp."""
        try:
            vehicle = self.get_by_plate(plate_number)
            if vehicle:
                vehicle.last_access = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating last access: {e}")
            return False
    
    def deactivate(self, plate_number: str) -> bool:
        """Deactivate vehicle."""
        try:
            vehicle = self.get_by_plate(plate_number)
            if vehicle:
                vehicle.is_active = False
                vehicle.updated_at = datetime.utcnow()
                self.session.commit()
                logger.info(f"Deactivated vehicle: {plate_number}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating vehicle: {e}")
            return False
    
    def search(self, owner_name: str = None, vehicle_type: str = None, 
               category: str = None, limit: int = 100) -> List[AuthorizedVehicle]:
        """Search vehicles by multiple criteria."""
        try:
            query = self.session.query(AuthorizedVehicle).filter_by(is_active=True)
            
            if owner_name:
                query = query.filter(AuthorizedVehicle.owner_name.ilike(f"%{owner_name}%"))
            if vehicle_type:
                query = query.filter_by(vehicle_type=vehicle_type)
            if category:
                query = query.filter_by(category=category)
            
            return query.order_by(desc(AuthorizedVehicle.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching vehicles: {e}")
            return []


class VehicleAccessLogDAO:
    """Data Access Object for VehicleAccessLog operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, 
              plate_number: str,
              vehicle_type: str,
              status: str = AccessStatus.UNKNOWN.value,
              **kwargs) -> Optional[VehicleAccessLog]:
        """Create new access log entry."""
        try:
            log = VehicleAccessLog(
                plate_number=plate_number,
                vehicle_type=vehicle_type,
                status=status,
                **kwargs
            )
            self.session.add(log)
            self.session.commit()
            return log
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating access log: {e}")
            return None
    
    def get_by_id(self, log_id: int) -> Optional[VehicleAccessLog]:
        """Get log entry by ID."""
        try:
            return self.session.query(VehicleAccessLog).filter_by(id=log_id).first()
        except Exception as e:
            logger.error(f"Error fetching log: {e}")
            return None
    
    def get_by_plate_today(self, plate_number: str) -> List[VehicleAccessLog]:
        """Get all entries for a plate today."""
        try:
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            
            return self.session.query(VehicleAccessLog)\
                .filter(
                    VehicleAccessLog.plate_number == plate_number,
                    VehicleAccessLog.entry_time >= datetime.combine(today, datetime.min.time()),
                    VehicleAccessLog.entry_time < datetime.combine(tomorrow, datetime.min.time())
                )\
                .order_by(desc(VehicleAccessLog.entry_time)).all()
        except Exception as e:
            logger.error(f"Error fetching plate entries: {e}")
            return []
    
    def get_date_range(self, 
                      start_date: datetime,
                      end_date: datetime,
                      status: Optional[str] = None) -> List[VehicleAccessLog]:
        """Get logs within date range."""
        try:
            query = self.session.query(VehicleAccessLog).filter(
                VehicleAccessLog.entry_time >= start_date,
                VehicleAccessLog.entry_time <= end_date
            )
            
            if status:
                query = query.filter_by(status=status)
            
            return query.order_by(desc(VehicleAccessLog.entry_time)).all()
        except Exception as e:
            logger.error(f"Error fetching date range: {e}")
            return []
    
    def get_by_status(self, status: str, limit: int = 100) -> List[VehicleAccessLog]:
        """Get logs by status."""
        try:
            return self.session.query(VehicleAccessLog)\
                .filter_by(status=status)\
                .order_by(desc(VehicleAccessLog.entry_time))\
                .limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching by status: {e}")
            return []
    
    def get_flagged(self, limit: int = 100) -> List[VehicleAccessLog]:
        """Get flagged entries for manual review."""
        try:
            return self.session.query(VehicleAccessLog)\
                .filter_by(flagged=True)\
                .order_by(desc(VehicleAccessLog.created_at))\
                .limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching flagged entries: {e}")
            return []
    
    def update_exit_time(self, log_id: int) -> bool:
        """Update exit time for a log entry."""
        try:
            log = self.get_by_id(log_id)
            if log:
                log.update_exit_time()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating exit time: {e}")
            return False
    
    def flag_entry(self, log_id: int, notes: str = "") -> bool:
        """Flag entry for manual review."""
        try:
            log = self.get_by_id(log_id)
            if log:
                log.flagged = True
                if notes:
                    log.notes = notes
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error flagging entry: {e}")
            return False
    
    def get_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get traffic statistics for date range."""
        try:
            logs = self.get_date_range(start_date, end_date)
            
            if not logs:
                return {
                    'total_entries': 0,
                    'by_type': {},
                    'by_status': {},
                    'by_category': {},
                }
            
            stats = {
                'total_entries': len(logs),
                'by_type': {},
                'by_status': {},
                'by_category': {},
            }
            
            for log in logs:
                # Count by vehicle type
                vtype = log.vehicle_type
                stats['by_type'][vtype] = stats['by_type'].get(vtype, 0) + 1
                
                # Count by status
                status = log.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Count by category
                category = log.category
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Delete records older than specified days (90-day retention policy).
        
        Args:
            days: Number of days to retain
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = self.session.query(VehicleAccessLog)\
                .filter(VehicleAccessLog.created_at < cutoff_date)\
                .delete()
            self.session.commit()
            logger.info(f"Cleaned up {deleted} old access log records")
            return deleted
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cleaning up old records: {e}")
            return 0


def create_tables(engine):
    """Create all tables in the database."""
    try:
        Base.metadata.create_all(engine)
        logger.info("✓ All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")


def create_session(database_url: str) -> Session:
    """Create a database session."""
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        return SessionLocal()
    except Exception as e:
        logger.error(f"Error creating database session: {e}")
        return None


if __name__ == "__main__":
    print("Vehicle Models module loaded successfully")
