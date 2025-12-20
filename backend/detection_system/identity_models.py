"""
Module 1: Person Identity & Access Intelligence - Database Models
SQLAlchemy models for Employee and AccessLog entities
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, Index, Enum as SQLEnum,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================

class EmployeeStatus(str, enum.Enum):
    """Employee status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class AccessStatus(str, enum.Enum):
    """Access authorization status"""
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN = "unknown"


class DepartmentEnum(str, enum.Enum):
    """Department enumeration"""
    MANUFACTURING = "manufacturing"
    WAREHOUSE = "warehouse"
    QUALITY = "quality"
    MAINTENANCE = "maintenance"
    ADMINISTRATION = "administration"
    SECURITY = "security"
    UNKNOWN = "unknown"


# ============================================================================
# EMPLOYEE MODEL
# ============================================================================

class Employee(Base):
    """
    Employee record with AWS face identification.
    
    Stores employee information and AWS Rekognition face IDs for identification.
    One employee can have multiple access log entries.
    """
    __tablename__ = 'employees'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    department = Column(SQLEnum(DepartmentEnum), default=DepartmentEnum.UNKNOWN, nullable=False)
    employee_id_code = Column(String(50), nullable=True, unique=True, index=True)  # Badge ID, etc.
    phone = Column(String(20), nullable=True)
    
    # AWS Integration
    aws_face_id = Column(String(255), nullable=True, index=True)  # AWS Rekognition Face ID
    photo_url = Column(Text, nullable=True)  # Path to enrollment photo
    
    # Status & Metadata
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False, index=True)
    is_authorized = Column(Boolean, default=True, nullable=False, index=True)
    
    # Temporal Data
    enrolled_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    last_seen = Column(DateTime, nullable=True, index=True)
    
    # Audit Fields
    created_by = Column(String(255), nullable=True)  # Admin who enrolled the employee
    notes = Column(Text, nullable=True)
    
    # Relationships
    access_logs = relationship(
        'AccessLog',
        back_populates='employee',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'department', name='uq_employee_name_dept'),
        Index('idx_employee_status', 'status'),
        Index('idx_employee_aws_face_id', 'aws_face_id'),
        Index('idx_employee_enrolled', 'enrolled_at'),
        CheckConstraint("status IN ('active', 'inactive', 'on_leave', 'terminated')", name='ck_employee_status'),
    )
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', dept='{self.department.value}', status='{self.status.value}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department.value,
            'employee_id_code': self.employee_id_code,
            'phone': self.phone,
            'aws_face_id': self.aws_face_id,
            'photo_url': self.photo_url,
            'status': self.status.value,
            'is_authorized': self.is_authorized,
            'enrolled_at': self.enrolled_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        return cls(
            name=data.get('name'),
            email=data.get('email'),
            department=DepartmentEnum(data.get('department', 'unknown')),
            employee_id_code=data.get('employee_id_code'),
            phone=data.get('phone'),
            aws_face_id=data.get('aws_face_id'),
            photo_url=data.get('photo_url'),
            status=EmployeeStatus(data.get('status', 'active')),
            is_authorized=data.get('is_authorized', True),
            notes=data.get('notes')
        )


# ============================================================================
# ACCESS LOG MODEL
# ============================================================================

class AccessLog(Base):
    """
    Access log entry for person identification and access tracking.
    
    Records every identification attempt, successful or not, including:
    - Known employees (matched via AWS Rekognition)
    - Unknown persons (no match in face collection)
    - Face snapshot for audit trails
    """
    __tablename__ = 'access_logs'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Tracking Information
    track_id = Column(Integer, nullable=False, index=True)  # ByteTrack ID from detector
    person_name = Column(String(255), nullable=False, index=True)  # Identified name or 'Unknown'
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True, index=True)  # FK if known
    
    # Status Information
    is_authorized = Column(Boolean, nullable=False, index=True, default=True)
    access_status = Column(
        SQLEnum(AccessStatus),
        nullable=False,
        index=True,
        default=AccessStatus.AUTHORIZED
    )
    
    # Confidence & Recognition Details
    confidence_score = Column(Float, nullable=True)  # AWS matching confidence (0-100)
    aws_face_id = Column(String(255), nullable=True)  # AWS face ID of matched person
    recognition_method = Column(
        String(50),
        nullable=True,
        default='rekognition'  # 'rekognition', 'fallback', 'manual', etc.
    )
    
    # Snapshot & Evidence
    snapshot_path = Column(Text, nullable=True)  # Path to saved face crop
    full_frame_path = Column(Text, nullable=True)  # Optional path to full detection frame
    
    # Temporal Data
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.now)
    
    # Additional Context
    entry_point = Column(String(100), nullable=True)  # Zone/gate where access occurred
    location_x = Column(Float, nullable=True)  # Optional spatial coordinates
    location_y = Column(Float, nullable=True)
    
    # Notes & Audit
    notes = Column(Text, nullable=True)  # Any special notes about this access
    flagged = Column(Boolean, default=False, nullable=False, index=True)  # Manual flag for review
    
    # Relationships
    employee = relationship(
        'Employee',
        back_populates='access_logs',
        foreign_keys=[employee_id],
        lazy='joined'
    )
    
    # Constraints
    __table_args__ = (
        Index('idx_access_timestamp', 'timestamp'),
        Index('idx_access_person', 'person_name'),
        Index('idx_access_authorized', 'is_authorized'),
        Index('idx_access_employee_id', 'employee_id'),
        Index('idx_access_track_id', 'track_id'),
        Index('idx_access_status', 'access_status'),
        Index('idx_access_flagged', 'flagged'),
        # Compound indexes for common queries
        Index('idx_access_timestamp_authorized', 'timestamp', 'is_authorized'),
        Index('idx_access_person_timestamp', 'person_name', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AccessLog(id={self.id}, track_id={self.track_id}, person='{self.person_name}', authorized={self.is_authorized}, timestamp='{self.timestamp}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'track_id': self.track_id,
            'person_name': self.person_name,
            'employee_id': self.employee_id,
            'is_authorized': self.is_authorized,
            'access_status': self.access_status.value,
            'confidence_score': self.confidence_score,
            'aws_face_id': self.aws_face_id,
            'recognition_method': self.recognition_method,
            'snapshot_path': self.snapshot_path,
            'full_frame_path': self.full_frame_path,
            'timestamp': self.timestamp.isoformat(),
            'entry_point': self.entry_point,
            'location': {
                'x': self.location_x,
                'y': self.location_y
            } if self.location_x is not None else None,
            'notes': self.notes,
            'flagged': self.flagged,
            'employee': self.employee.to_dict() if self.employee else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        return cls(
            track_id=data.get('track_id'),
            person_name=data.get('person_name'),
            employee_id=data.get('employee_id'),
            is_authorized=data.get('is_authorized', True),
            access_status=AccessStatus(data.get('access_status', 'authorized')),
            confidence_score=data.get('confidence_score'),
            aws_face_id=data.get('aws_face_id'),
            recognition_method=data.get('recognition_method', 'rekognition'),
            snapshot_path=data.get('snapshot_path'),
            full_frame_path=data.get('full_frame_path'),
            entry_point=data.get('entry_point'),
            location_x=data.get('location_x'),
            location_y=data.get('location_y'),
            notes=data.get('notes'),
            flagged=data.get('flagged', False)
        )


# ============================================================================
# DATABASE INITIALIZATION UTILITIES
# ============================================================================

def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables(engine):
    """Drop all tables from the database (dangerous!)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")


# ============================================================================
# DATA ACCESS OBJECTS (DAO) - HELPER FUNCTIONS
# ============================================================================

class EmployeeDAO:
    """Data Access Object for Employee operations"""
    
    @staticmethod
    def create(db_session, employee_data: dict) -> Employee:
        """Create a new employee"""
        employee = Employee.from_dict(employee_data)
        db_session.add(employee)
        db_session.commit()
        return employee
    
    @staticmethod
    def get_by_id(db_session, employee_id: int) -> Employee:
        """Get employee by ID"""
        return db_session.query(Employee).filter(Employee.id == employee_id).first()
    
    @staticmethod
    def get_by_name(db_session, name: str) -> Employee:
        """Get employee by name"""
        return db_session.query(Employee).filter(Employee.name == name).first()
    
    @staticmethod
    def get_by_aws_face_id(db_session, aws_face_id: str) -> Employee:
        """Get employee by AWS face ID"""
        return db_session.query(Employee).filter(Employee.aws_face_id == aws_face_id).first()
    
    @staticmethod
    def get_by_email(db_session, email: str) -> Employee:
        """Get employee by email"""
        return db_session.query(Employee).filter(Employee.email == email).first()
    
    @staticmethod
    def get_active_employees(db_session, limit: int = 100) -> list:
        """Get all active employees"""
        return db_session.query(Employee).filter(
            Employee.status == EmployeeStatus.ACTIVE,
            Employee.is_authorized == True
        ).limit(limit).all()
    
    @staticmethod
    def get_by_department(db_session, department: DepartmentEnum) -> list:
        """Get employees by department"""
        return db_session.query(Employee).filter(Employee.department == department).all()
    
    @staticmethod
    def update(db_session, employee_id: int, updates: dict) -> Employee:
        """Update employee record"""
        employee = EmployeeDAO.get_by_id(db_session, employee_id)
        if employee:
            for key, value in updates.items():
                if hasattr(employee, key) and key not in ['id', 'enrolled_at']:
                    setattr(employee, key, value)
            employee.updated_at = datetime.now()
            db_session.commit()
        return employee
    
    @staticmethod
    def delete(db_session, employee_id: int) -> bool:
        """Delete employee (soft delete by marking inactive)"""
        employee = EmployeeDAO.get_by_id(db_session, employee_id)
        if employee:
            employee.status = EmployeeStatus.TERMINATED
            employee.updated_at = datetime.now()
            db_session.commit()
            return True
        return False
    
    @staticmethod
    def get_total_count(db_session) -> int:
        """Get total number of employees"""
        return db_session.query(Employee).count()
    
    @staticmethod
    def search(db_session, query: str, limit: int = 20) -> list:
        """Search employees by name or email"""
        return db_session.query(Employee).filter(
            (Employee.name.ilike(f"%{query}%")) |
            (Employee.email.ilike(f"%{query}%"))
        ).limit(limit).all()


class AccessLogDAO:
    """Data Access Object for AccessLog operations"""
    
    @staticmethod
    def create(db_session, log_data: dict) -> AccessLog:
        """Create a new access log entry"""
        log = AccessLog.from_dict(log_data)
        db_session.add(log)
        db_session.commit()
        return log
    
    @staticmethod
    def get_by_id(db_session, log_id: int) -> AccessLog:
        """Get log by ID"""
        return db_session.query(AccessLog).filter(AccessLog.id == log_id).first()
    
    @staticmethod
    def get_by_track_id(db_session, track_id: int, limit: int = 10) -> list:
        """Get all logs for a track_id"""
        return db_session.query(AccessLog).filter(
            AccessLog.track_id == track_id
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_person(db_session, person_name: str, limit: int = 50) -> list:
        """Get all logs for a person"""
        return db_session.query(AccessLog).filter(
            AccessLog.person_name == person_name
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_employee_id(db_session, employee_id: int, limit: int = 100) -> list:
        """Get all logs for an employee"""
        return db_session.query(AccessLog).filter(
            AccessLog.employee_id == employee_id
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_unknown_persons(db_session, limit: int = 50) -> list:
        """Get all unknown person access attempts"""
        return db_session.query(AccessLog).filter(
            AccessLog.person_name == 'Unknown'
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_unauthorized_accesses(db_session, limit: int = 50) -> list:
        """Get all unauthorized access attempts"""
        return db_session.query(AccessLog).filter(
            AccessLog.is_authorized == False
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_flagged_entries(db_session, limit: int = 50) -> list:
        """Get all manually flagged entries"""
        return db_session.query(AccessLog).filter(
            AccessLog.flagged == True
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_time_range(db_session, start_time: datetime, end_time: datetime) -> list:
        """Get logs within a time range"""
        return db_session.query(AccessLog).filter(
            AccessLog.timestamp.between(start_time, end_time)
        ).order_by(AccessLog.timestamp.desc()).all()
    
    @staticmethod
    def get_statistics(db_session, start_time: datetime, end_time: datetime) -> dict:
        """Get access statistics for a time period"""
        query = db_session.query(AccessLog).filter(
            AccessLog.timestamp.between(start_time, end_time)
        )
        
        total = query.count()
        authorized = query.filter(AccessLog.is_authorized == True).count()
        unauthorized = query.filter(AccessLog.is_authorized == False).count()
        unknown = query.filter(AccessLog.person_name == 'Unknown').count()
        
        return {
            'total_accesses': total,
            'authorized': authorized,
            'unauthorized': unauthorized,
            'unknown': unknown,
            'authorization_rate': (authorized / total * 100) if total > 0 else 0,
            'unknown_rate': (unknown / total * 100) if total > 0 else 0,
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }
    
    @staticmethod
    def update_with_employee(db_session, log_id: int, employee_id: int) -> AccessLog:
        """Update an access log with employee ID (for post-matching)"""
        log = AccessLogDAO.get_by_id(db_session, log_id)
        if log:
            log.employee_id = employee_id
            log.updated_at = datetime.now()
            db_session.commit()
        return log
    
    @staticmethod
    def flag_entry(db_session, log_id: int, flag: bool = True) -> AccessLog:
        """Flag an entry for manual review"""
        log = AccessLogDAO.get_by_id(db_session, log_id)
        if log:
            log.flagged = flag
            db_session.commit()
        return log
    
    @staticmethod
    def delete_old_logs(db_session, days_to_keep: int = 90) -> int:
        """Delete logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        count = db_session.query(AccessLog).filter(
            AccessLog.timestamp < cutoff_date
        ).delete()
        db_session.commit()
        return count
