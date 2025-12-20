"""
Module 1: Person Identity & Access Intelligence
AWS Rekognition Integration + Stateful Tracking + Access Logging
"""
import boto3
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import numpy as np
import cv2
from botocore.exceptions import ClientError, BotoCoreError
import asyncio
from functools import lru_cache
from sqlalchemy.orm import Session
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# AWS Rekognition Settings
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REKOGNITION_COLLECTION_ID = os.getenv("REKOGNITION_COLLECTION_ID", "factory-employees")
FACE_MATCH_THRESHOLD = 85.0  # 85% confidence threshold

# Local paths
SNAPSHOTS_DIR = Path("data/snapshots/unknown")
ENROLLMENT_DIR = Path("data/enrollment_photos")
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
ENROLLMENT_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiting for AWS API (avoid throttling)
MAX_REKOGNITION_CALLS_PER_SECOND = 5
RATE_LIMIT_WINDOW = 1.0  # seconds
API_CALL_TIMESTAMPS = []

# State management for tracked identities
IDENTITY_CACHE: Dict[int, Dict] = {}  # {track_id: {name, face_id, confidence, timestamp}}
CACHE_TTL_SECONDS = 300  # 5 minutes cache validity
UNKNOWN_PERSON_COOLDOWN = 30  # seconds before re-capturing unknown person

# ============================================================================
# AWS REKOGNITION CLIENT INITIALIZATION
# ============================================================================

class AWSRecognitionClient:
    """Wrapper for AWS Rekognition API interactions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        try:
            self.client = boto3.client(
                'rekognition',
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY
            )
            self._initialized = True
            logger.info("✅ AWS Rekognition client initialized")
            
            # Verify collection exists
            self._verify_collection()
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS Rekognition: {e}")
            self.client = None
    
    def _verify_collection(self):
        """Verify the Rekognition collection exists"""
        try:
            response = self.client.describe_collection(
                CollectionId=REKOGNITION_COLLECTION_ID
            )
            logger.info(f"✅ Collection '{REKOGNITION_COLLECTION_ID}' verified")
            logger.info(f"   Faces in collection: {response.get('FaceCount', 0)}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"⚠️ Collection '{REKOGNITION_COLLECTION_ID}' not found. Creating...")
                self._create_collection()
            else:
                logger.error(f"❌ Error verifying collection: {e}")
    
    def _create_collection(self):
        """Create the Rekognition collection if it doesn't exist"""
        try:
            self.client.create_collection(
                CollectionId=REKOGNITION_COLLECTION_ID
            )
            logger.info(f"✅ Collection '{REKOGNITION_COLLECTION_ID}' created successfully")
        except ClientError as e:
            logger.error(f"❌ Failed to create collection: {e}")
    
    def search_faces_by_image(self, image_bytes: bytes) -> Dict:
        """
        Search for faces in a given image against the collection.
        
        Args:
            image_bytes: Raw image bytes (JPEG/PNG)
        
        Returns:
            {
                'matched_faces': [
                    {
                        'external_id': str,      # Employee name from collection
                        'confidence': float,     # Match confidence (0-100)
                        'face_id': str          # AWS face_id
                    }
                ],
                'unmatched_faces': int,          # Faces detected but not matched
                'error': Optional[str]
            }
        """
        try:
            # Rate limiting check
            self._check_rate_limit()
            
            response = self.client.search_faces_by_image(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={'Bytes': image_bytes},
                FaceMatchThreshold=FACE_MATCH_THRESHOLD,
                MaxFaces=1  # Return top 1 match only
            )
            
            matched_faces = []
            for face_match in response.get('FaceMatches', []):
                face = face_match['Face']
                confidence = face_match['Similarity']
                
                matched_faces.append({
                    'external_id': face.get('ExternalImageId', 'Unknown'),
                    'face_id': face.get('FaceId'),
                    'confidence': confidence
                })
            
            return {
                'matched_faces': matched_faces,
                'unmatched_faces': len(response.get('UnmatchedFaces', [])),
                'error': None
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'InvalidImageFormatException':
                logger.warning(f"⚠️ Invalid image format: {error_msg}")
            elif error_code == 'ImageTooLargeException':
                logger.warning(f"⚠️ Image too large: {error_msg}")
            elif error_code == 'ThrottlingException':
                logger.warning(f"⚠️ AWS throttling - rate limited")
            else:
                logger.error(f"❌ AWS API Error ({error_code}): {error_msg}")
            
            return {
                'matched_faces': [],
                'unmatched_faces': 0,
                'error': f"{error_code}: {error_msg}"
            }
        
        except BotoCoreError as e:
            logger.error(f"❌ Boto3 Core Error: {e}")
            return {
                'matched_faces': [],
                'unmatched_faces': 0,
                'error': f"Connection error: {str(e)}"
            }
    
    def index_faces(self, image_bytes: bytes, external_id: str) -> Dict:
        """
        Index a face in the collection during enrollment.
        
        Args:
            image_bytes: Raw image bytes
            external_id: Employee name (identifier for the face)
        
        Returns:
            {
                'face_id': str,
                'face_records': int,
                'error': Optional[str]
            }
        """
        try:
            self._check_rate_limit()
            
            response = self.client.index_faces(
                CollectionId=REKOGNITION_COLLECTION_ID,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_id,
                MaxFaces=1,
                QualityFilter='AUTO'
            )
            
            face_records = response.get('FaceRecords', [])
            if face_records:
                face_id = face_records[0]['Face']['FaceId']
                logger.info(f"✅ Face indexed for '{external_id}' - FaceId: {face_id}")
                return {
                    'face_id': face_id,
                    'face_records': len(face_records),
                    'error': None
                }
            else:
                logger.warning(f"⚠️ No faces detected in enrollment image for '{external_id}'")
                return {
                    'face_id': None,
                    'face_records': 0,
                    'error': 'No faces detected in image'
                }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"❌ AWS API Error during enrollment ({error_code}): {e}")
            return {
                'face_id': None,
                'face_records': 0,
                'error': str(e)
            }
    
    def _check_rate_limit(self):
        """Enforce rate limiting to avoid AWS throttling"""
        global API_CALL_TIMESTAMPS
        
        now = datetime.now()
        # Remove old timestamps outside the window
        API_CALL_TIMESTAMPS = [ts for ts in API_CALL_TIMESTAMPS 
                               if (now - ts).total_seconds() < RATE_LIMIT_WINDOW]
        
        if len(API_CALL_TIMESTAMPS) >= MAX_REKOGNITION_CALLS_PER_SECOND:
            sleep_duration = RATE_LIMIT_WINDOW - (now - API_CALL_TIMESTAMPS[0]).total_seconds()
            if sleep_duration > 0:
                logger.warning(f"⚠️ Rate limit approaching - sleeping {sleep_duration:.2f}s")
                import time
                time.sleep(sleep_duration + 0.01)
        
        API_CALL_TIMESTAMPS.append(now)


# ============================================================================
# IDENTITY STATE MANAGEMENT
# ============================================================================

class IdentityStateManager:
    """Manages the identity cache and state for tracked persons"""
    
    @staticmethod
    def get_cached_identity(track_id: int) -> Optional[Dict]:
        """
        Get cached identity for a track_id.
        
        Returns None if not cached or cache expired.
        """
        if track_id not in IDENTITY_CACHE:
            return None
        
        cached = IDENTITY_CACHE[track_id]
        age = (datetime.now() - cached['timestamp']).total_seconds()
        
        if age > CACHE_TTL_SECONDS:
            # Cache expired
            del IDENTITY_CACHE[track_id]
            return None
        
        return cached
    
    @staticmethod
    def set_cached_identity(track_id: int, name: str, face_id: str, confidence: float):
        """Cache an identified person"""
        IDENTITY_CACHE[track_id] = {
            'name': name,
            'face_id': face_id,
            'confidence': confidence,
            'timestamp': datetime.now()
        }
        logger.debug(f"🔍 Cached identity: track_id={track_id}, name={name}, conf={confidence:.1f}%")
    
    @staticmethod
    def set_unknown_identity(track_id: int):
        """Mark a track_id as unknown"""
        IDENTITY_CACHE[track_id] = {
            'name': 'Unknown',
            'face_id': None,
            'confidence': 0.0,
            'timestamp': datetime.now()
        }
    
    @staticmethod
    def clear_cache():
        """Clear the entire identity cache"""
        IDENTITY_CACHE.clear()
        logger.info("🗑️ Identity cache cleared")
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """Get statistics about the current cache"""
        return {
            'cached_identities': len(IDENTITY_CACHE),
            'known_persons': len([v for v in IDENTITY_CACHE.values() if v['name'] != 'Unknown']),
            'unknown_persons': len([v for v in IDENTITY_CACHE.values() if v['name'] == 'Unknown'])
        }


# ============================================================================
# IMAGE PROCESSING UTILITIES
# ============================================================================

class ImageProcessor:
    """Utilities for image handling and snapshot management"""
    
    @staticmethod
    def encode_image_to_bytes(image: np.ndarray, format: str = 'jpg') -> bytes:
        """Convert OpenCV image to bytes"""
        if format.lower() == 'jpg':
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        else:
            _, buffer = cv2.imencode('.png', image)
        return buffer.tobytes()
    
    @staticmethod
    def decode_bytes_to_image(image_bytes: bytes) -> Optional[np.ndarray]:
        """Convert bytes to OpenCV image"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"❌ Failed to decode image: {e}")
            return None
    
    @staticmethod
    def save_snapshot(image: np.ndarray, person_type: str = 'unknown', 
                     person_id: Optional[str] = None) -> Optional[str]:
        """
        Save a high-quality snapshot of a person.
        
        Args:
            image: OpenCV image
            person_type: 'unknown' or 'known'
            person_id: Optional person identifier for known persons
        
        Returns:
            Path to saved image or None on error
        """
        try:
            # Create date-based subdirectory
            date_dir = SNAPSHOTS_DIR / datetime.now().strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%H-%M-%S-%f")[:-3]
            filename = f"{timestamp}.jpg"
            
            if person_type == 'unknown':
                filepath = date_dir / filename
            else:
                known_dir = date_dir / "known"
                known_dir.mkdir(exist_ok=True)
                filepath = known_dir / f"{person_id}_{filename}"
            
            # Save with high quality
            cv2.imwrite(
                str(filepath),
                image,
                [cv2.IMWRITE_JPEG_QUALITY, 95]
            )
            
            logger.info(f"💾 Snapshot saved: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"❌ Failed to save snapshot: {e}")
            return None


# ============================================================================
# MAIN IDENTITY SERVICE
# ============================================================================

class IdentityService:
    """
    Main service for person identification and access logging.
    Coordinates AWS Rekognition, state management, and database operations.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.rekognition = AWSRecognitionClient()
        self.state_manager = IdentityStateManager()
        self.image_processor = ImageProcessor()
    
    # ========================================================================
    # MAIN PROCESSING FUNCTION
    # ========================================================================
    
    def process_frame_identities(self, frame: np.ndarray, 
                                track_ids: List[Tuple[int, np.ndarray]]) -> Dict:
        """
        Process a frame and identify all tracked persons.
        
        Args:
            frame: Full frame image
            track_ids: List of (track_id, face_crop) tuples from ByteTrack
        
        Returns:
            {
                'identities': [
                    {
                        'track_id': int,
                        'name': str,
                        'confidence': float,
                        'is_new': bool,
                        'is_authorized': bool
                    }
                ],
                'unknown_count': int,
                'processing_time_ms': float,
                'errors': List[str]
            }
        """
        start_time = datetime.now()
        identities = []
        errors = []
        unknown_count = 0
        
        for track_id, face_crop in track_ids:
            try:
                identity = self._identify_track(track_id, face_crop, frame)
                
                if identity['name'] == 'Unknown':
                    unknown_count += 1
                
                identities.append(identity)
            
            except Exception as e:
                logger.error(f"❌ Error identifying track_id {track_id}: {e}")
                errors.append(f"Track {track_id}: {str(e)}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'identities': identities,
            'unknown_count': unknown_count,
            'processing_time_ms': processing_time,
            'errors': errors
        }
    
    def _identify_track(self, track_id: int, face_crop: np.ndarray, 
                       full_frame: np.ndarray) -> Dict:
        """
        Identify a single tracked person.
        Uses cache to avoid redundant API calls.
        """
        # Check cache first
        cached = self.state_manager.get_cached_identity(track_id)
        if cached:
            return {
                'track_id': track_id,
                'name': cached['name'],
                'confidence': cached['confidence'],
                'is_cached': True,
                'is_authorized': self._check_authorization(cached['name']),
                'face_id': cached.get('face_id')
            }
        
        # Face not in cache - query AWS Rekognition
        face_bytes = self.image_processor.encode_image_to_bytes(face_crop)
        result = self.rekognition.search_faces_by_image(face_bytes)
        
        if result['error']:
            logger.warning(f"⚠️ AWS search failed for track_id {track_id}: {result['error']}")
            self.state_manager.set_unknown_identity(track_id)
            identity_name = 'Unknown'
            confidence = 0.0
            face_id = None
        elif result['matched_faces']:
            # Face found in collection
            match = result['matched_faces'][0]
            identity_name = match['external_id']
            confidence = match['confidence']
            face_id = match['face_id']
            
            self.state_manager.set_cached_identity(track_id, identity_name, face_id, confidence)
            logger.info(f"✅ Identified track_id {track_id}: {identity_name} ({confidence:.1f}%)")
        else:
            # No match found
            self.state_manager.set_unknown_identity(track_id)
            identity_name = 'Unknown'
            confidence = 0.0
            face_id = None
            
            # Trigger snapshot save for unknown persons
            self._handle_unknown_person(track_id, face_crop)
        
        # Log to database
        access_log = self._log_access(
            track_id=track_id,
            person_name=identity_name,
            is_authorized=self._check_authorization(identity_name),
            snapshot=face_crop
        )
        
        return {
            'track_id': track_id,
            'name': identity_name,
            'confidence': confidence,
            'is_cached': False,
            'is_authorized': self._check_authorization(identity_name),
            'access_log_id': access_log.id if access_log else None,
            'face_id': face_id
        }
    
    # ========================================================================
    # UNKNOWN PERSON HANDLING
    # ========================================================================
    
    def _handle_unknown_person(self, track_id: int, face_crop: np.ndarray):
        """
        Handle detection of unknown person.
        Saves snapshot and triggers any necessary alerts.
        """
        # Check cooldown to avoid duplicate snapshots
        cached = IDENTITY_CACHE.get(track_id, {})
        last_capture = cached.get('last_unknown_capture', datetime.min)
        time_since_capture = (datetime.now() - last_capture).total_seconds()
        
        if time_since_capture < UNKNOWN_PERSON_COOLDOWN:
            return
        
        # Save high-quality snapshot
        snapshot_path = self.image_processor.save_snapshot(
            face_crop,
            person_type='unknown',
            person_id=f"track_{track_id}"
        )
        
        if snapshot_path:
            # Update cache with capture timestamp
            if track_id in IDENTITY_CACHE:
                IDENTITY_CACHE[track_id]['last_unknown_capture'] = datetime.now()
            
            logger.warning(f"⚠️ Unknown person detected - snapshot: {snapshot_path}")
            # TODO: Trigger alert notification system
    
    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================
    
    def _log_access(self, track_id: int, person_name: str, 
                    is_authorized: bool, snapshot: np.ndarray) -> Optional[object]:
        """
        Log an access event to the database.
        
        Args:
            track_id: ByteTrack ID
            person_name: Identified person's name or 'Unknown'
            is_authorized: Authorization status
            snapshot: Face crop image
        
        Returns:
            AccessLog object or None on error
        """
        try:
            # Import models here to avoid circular imports
            from detection_system.models import AccessLog
            
            snapshot_path = None
            if person_name != 'Unknown':
                snapshot_path = self.image_processor.save_snapshot(
                    snapshot,
                    person_type='known',
                    person_id=person_name
                )
            
            access_log = AccessLog(
                track_id=track_id,
                person_name=person_name,
                timestamp=datetime.now(),
                is_authorized=is_authorized,
                snapshot_path=snapshot_path
            )
            
            self.db.add(access_log)
            self.db.commit()
            
            logger.debug(f"📝 Access logged: {person_name} (authorized={is_authorized})")
            return access_log
        
        except Exception as e:
            logger.error(f"❌ Failed to log access: {e}")
            self.db.rollback()
            return None
    
    def _check_authorization(self, person_name: str) -> bool:
        """
        Check if a person is authorized to access.
        
        In a full implementation, this would check employee status,
        shift timing, department restrictions, etc.
        """
        if person_name == 'Unknown':
            return False
        
        try:
            from detection_system.models import Employee
            
            employee = self.db.query(Employee).filter(
                Employee.name == person_name
            ).first()
            
            if employee is None:
                return False
            
            # Additional checks could be added here
            # e.g., check if employee is active, on shift, etc.
            return True
        
        except Exception as e:
            logger.error(f"❌ Error checking authorization for {person_name}: {e}")
            return False
    
    # ========================================================================
    # ENROLLMENT
    # ========================================================================
    
    def enroll_employee(self, employee_data: Dict, image_bytes: bytes) -> Dict:
        """
        Enroll a new employee in the system.
        
        Args:
            employee_data: {
                'name': str,
                'department': str,
                'email': Optional[str]
            }
            image_bytes: Face photo bytes (JPEG/PNG)
        
        Returns:
            {
                'success': bool,
                'employee_id': Optional[int],
                'face_id': Optional[str],
                'error': Optional[str]
            }
        """
        try:
            from detection_system.models import Employee
            
            # Check if employee already exists
            existing = self.db.query(Employee).filter(
                Employee.name == employee_data['name']
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'employee_id': None,
                    'face_id': None,
                    'error': f"Employee '{employee_data['name']}' already enrolled"
                }
            
            # Index face in AWS Rekognition
            enrollment_result = self.rekognition.index_faces(
                image_bytes=image_bytes,
                external_id=employee_data['name']
            )
            
            if enrollment_result['error']:
                return {
                    'success': False,
                    'employee_id': None,
                    'face_id': None,
                    'error': enrollment_result['error']
                }
            
            # Save photo locally
            photo_path = None
            try:
                image = self.image_processor.decode_bytes_to_image(image_bytes)
                if image is not None:
                    photo_filename = f"{employee_data['name']}.jpg"
                    photo_path = ENROLLMENT_DIR / photo_filename
                    cv2.imwrite(str(photo_path), image)
                    photo_path = str(photo_path)
            except Exception as e:
                logger.warning(f"⚠️ Could not save enrollment photo: {e}")
            
            # Create database record
            employee = Employee(
                name=employee_data['name'],
                aws_face_id=enrollment_result['face_id'],
                department=employee_data.get('department', 'Unassigned'),
                photo_url=photo_path,
                email=employee_data.get('email'),
                enrolled_at=datetime.now()
            )
            
            self.db.add(employee)
            self.db.commit()
            
            logger.info(f"✅ Employee enrolled: {employee_data['name']} (ID: {employee.id})")
            
            return {
                'success': True,
                'employee_id': employee.id,
                'face_id': enrollment_result['face_id'],
                'error': None
            }
        
        except Exception as e:
            logger.error(f"❌ Enrollment failed: {e}")
            self.db.rollback()
            return {
                'success': False,
                'employee_id': None,
                'face_id': None,
                'error': str(e)
            }
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.state_manager.get_cache_stats()
    
    def clear_identity_cache(self):
        """Clear the identity cache"""
        self.state_manager.clear_cache()
    
    def get_access_logs(self, limit: int = 100, 
                       person_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve access logs.
        
        Args:
            limit: Max number of logs to return
            person_filter: Filter by person name (optional)
        
        Returns:
            List of access log entries
        """
        try:
            from detection_system.models import AccessLog
            
            query = self.db.query(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit)
            
            if person_filter:
                query = query.filter(AccessLog.person_name == person_filter)
            
            logs = query.all()
            
            return [
                {
                    'id': log.id,
                    'track_id': log.track_id,
                    'person_name': log.person_name,
                    'timestamp': log.timestamp.isoformat(),
                    'is_authorized': log.is_authorized,
                    'snapshot_path': log.snapshot_path
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"❌ Error retrieving access logs: {e}")
            return []
    
    def get_access_summary(self, start_time: datetime, end_time: datetime) -> Dict:
        """
        Get access summary for a time period.
        """
        try:
            from detection_system.models import AccessLog
            
            total_accesses = self.db.query(AccessLog).filter(
                AccessLog.timestamp.between(start_time, end_time)
            ).count()
            
            authorized = self.db.query(AccessLog).filter(
                AccessLog.timestamp.between(start_time, end_time),
                AccessLog.is_authorized == True
            ).count()
            
            unauthorized = self.db.query(AccessLog).filter(
                AccessLog.timestamp.between(start_time, end_time),
                AccessLog.is_authorized == False
            ).count()
            
            unknown = self.db.query(AccessLog).filter(
                AccessLog.timestamp.between(start_time, end_time),
                AccessLog.person_name == 'Unknown'
            ).count()
            
            return {
                'total_accesses': total_accesses,
                'authorized': authorized,
                'unauthorized': unauthorized,
                'unknown': unknown,
                'period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"❌ Error computing access summary: {e}")
            return {}


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_identity_service_instance = None

def get_identity_service(db_session: Session) -> IdentityService:
    """Factory function to get or create identity service instance"""
    global _identity_service_instance
    if _identity_service_instance is None:
        _identity_service_instance = IdentityService(db_session)
    return _identity_service_instance
