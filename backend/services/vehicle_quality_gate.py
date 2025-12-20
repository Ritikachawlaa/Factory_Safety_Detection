"""
Module 2: Vehicle Quality Gate & ANPR Validation Service
Implements OCR confidence filtering, plate format validation, and blocked vehicle detection.

Key Features:
- OCR confidence threshold (only accept plates with confidence > 0.85)
- Regex-based plate format validation (India standard: ^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$)
- Blocked vehicle detection with real-time system logging
- Plate status tracking (AUTHORIZED, BLOCKED, UNKNOWN)
"""

import logging
import re
from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlateStatus(str, Enum):
    """License plate authorization status"""
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class PlateFormat(str, Enum):
    """Supported Indian license plate formats"""
    INDIA_STANDARD = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"  # e.g., KA01AB1234
    INDIA_COMMERCIAL = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"  # Same format


class VehicleQualityGate:
    """
    Quality control gate for vehicle license plate recognition.
    Ensures only high-confidence, valid plates trigger gate events.
    """
    
    # Configuration
    OCR_CONFIDENCE_THRESHOLD = 0.85  # 85% minimum confidence
    PLATE_REGEX_PATTERNS = [
        PlateFormat.INDIA_STANDARD.value,
    ]
    
    # In-memory cache for blocked vehicles (plate -> block_info)
    BLOCKED_VEHICLES = {}
    
    def __init__(self, db_session=None, system_logger=None):
        """
        Initialize the vehicle quality gate.
        
        Args:
            db_session: SQLAlchemy database session
            system_logger: System event logger (for recording blocked plate events)
        """
        self.db = db_session
        self.system_logger = system_logger
        logger.info(f"✅ VehicleQualityGate initialized (OCR threshold: {self.OCR_CONFIDENCE_THRESHOLD})")
    
    def validate_plate_recognition(
        self,
        ocr_text: str,
        ocr_confidence: float,
        vehicle_track_id: int,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Main validation gate for license plate recognition.
        
        Checks:
        1. OCR confidence >= 0.85
        2. Plate format matches India standard
        3. Plate is not in blocked list
        
        Args:
            ocr_text: Raw OCR output text
            ocr_confidence: OCR confidence score (0.0 to 1.0)
            vehicle_track_id: Vehicle tracking ID
            timestamp: Timestamp of detection
        
        Returns:
            {
                'valid': bool,
                'plate_number': Optional[str],
                'confidence': float,
                'status': PlateStatus,
                'reason': str,
                'should_trigger_gate_event': bool,
                'requires_manual_review': bool,
                'alert_message': Optional[str]
            }
        """
        timestamp = timestamp or datetime.now()
        
        try:
            logger.info(f"🔍 Validating plate for vehicle {vehicle_track_id}: '{ocr_text}' (confidence: {ocr_confidence:.2%})")
            
            # Step 1: CHECK OCR CONFIDENCE THRESHOLD
            if ocr_confidence < self.OCR_CONFIDENCE_THRESHOLD:
                logger.warning(f"⚠️ Low OCR confidence ({ocr_confidence:.2%}) < {self.OCR_CONFIDENCE_THRESHOLD:.2%} threshold")
                return {
                    'valid': False,
                    'plate_number': None,
                    'confidence': ocr_confidence,
                    'status': PlateStatus.UNKNOWN,
                    'reason': f'Low confidence: {ocr_confidence:.2%}',
                    'should_trigger_gate_event': False,
                    'requires_manual_review': True,
                    'alert_message': f'Low-confidence plate detection: {ocr_text}'
                }
            
            # Step 2: VALIDATE PLATE FORMAT
            cleaned_plate = self._clean_plate_text(ocr_text)
            is_valid_format = self._validate_plate_format(cleaned_plate)
            
            if not is_valid_format:
                logger.warning(f"⚠️ Invalid plate format: '{cleaned_plate}'")
                return {
                    'valid': False,
                    'plate_number': cleaned_plate,
                    'confidence': ocr_confidence,
                    'status': PlateStatus.UNKNOWN,
                    'reason': 'Invalid plate format',
                    'should_trigger_gate_event': False,
                    'requires_manual_review': True,
                    'alert_message': f'Invalid plate format detected: {cleaned_plate}'
                }
            
            # Step 3: CHECK BLOCKED VEHICLE LIST
            plate_status = self._check_plate_status(cleaned_plate)
            
            if plate_status == PlateStatus.BLOCKED:
                logger.error(f"🚨 BLOCKED VEHICLE DETECTED: {cleaned_plate}")
                
                # Trigger real-time system log event
                self._log_blocked_plate_event(cleaned_plate, vehicle_track_id, timestamp)
                
                return {
                    'valid': False,
                    'plate_number': cleaned_plate,
                    'confidence': ocr_confidence,
                    'status': PlateStatus.BLOCKED,
                    'reason': 'Plate is in blocked list',
                    'should_trigger_gate_event': False,
                    'requires_manual_review': True,
                    'alert_message': f'🚨 BLOCKED VEHICLE: {cleaned_plate}',
                    'requires_security_alert': True
                }
            
            # All checks passed!
            logger.info(f"✅ Valid plate detected: {cleaned_plate} (confidence: {ocr_confidence:.2%})")
            
            return {
                'valid': True,
                'plate_number': cleaned_plate,
                'confidence': ocr_confidence,
                'status': plate_status,
                'reason': 'All validation checks passed',
                'should_trigger_gate_event': True,
                'requires_manual_review': False,
                'alert_message': None
            }
        
        except Exception as e:
            logger.error(f"❌ Error validating plate: {e}", exc_info=True)
            return {
                'valid': False,
                'error': str(e),
                'should_trigger_gate_event': False,
                'requires_manual_review': True
            }
    
    def _clean_plate_text(self, raw_text: str) -> str:
        """
        Clean OCR output by removing spaces and normalizing case.
        
        Args:
            raw_text: Raw OCR text
        
        Returns:
            Cleaned plate text
        """
        # Remove spaces and special characters
        cleaned = re.sub(r'[\s\-]', '', raw_text.upper())
        logger.debug(f"Cleaned plate: '{raw_text}' -> '{cleaned}'")
        return cleaned
    
    def _validate_plate_format(self, plate: str) -> bool:
        """
        Validate plate against registered format patterns.
        
        Args:
            plate: Cleaned plate text
        
        Returns:
            True if plate matches any valid format
        """
        for pattern in self.PLATE_REGEX_PATTERNS:
            if re.match(pattern, plate):
                logger.debug(f"✓ Plate format valid: {plate}")
                return True
        
        logger.warning(f"✗ Plate format invalid: {plate}")
        return False
    
    def _check_plate_status(self, plate: str) -> PlateStatus:
        """
        Check if plate is in blocked list or authorized list.
        
        Args:
            plate: Cleaned plate text
        
        Returns:
            PlateStatus (BLOCKED, AUTHORIZED, or UNKNOWN)
        """
        if plate in self.BLOCKED_VEHICLES:
            logger.warning(f"Plate {plate} is BLOCKED")
            return PlateStatus.BLOCKED
        
        # In production, would query database for authorized vehicles
        # For now, return UNKNOWN (needs manual verification)
        logger.debug(f"Plate {plate} status is UNKNOWN (requires database check)")
        return PlateStatus.UNKNOWN
    
    def _log_blocked_plate_event(self, plate: str, vehicle_track_id: int, timestamp: datetime) -> None:
        """
        Trigger a real-time system log event for blocked vehicle.
        
        Args:
            plate: License plate number
            vehicle_track_id: Vehicle tracking ID
            timestamp: Detection timestamp
        """
        event_message = f"BLOCKED VEHICLE DETECTED: {plate} (Track ID: {vehicle_track_id})"
        
        logger.critical(event_message)
        
        # In production, would also call system logger
        if self.system_logger:
            try:
                self.system_logger.log_event(
                    log_type='vehicle',
                    severity='critical',
                    message=event_message,
                    details={
                        'plate_number': plate,
                        'vehicle_track_id': vehicle_track_id,
                        'timestamp': timestamp.isoformat(),
                        'event_type': 'blocked_vehicle_detection'
                    }
                )
                logger.info(f"✅ Blocked plate event logged to system")
            except Exception as e:
                logger.error(f"❌ Failed to log blocked plate event: {e}")
    
    def register_blocked_vehicle(self, plate: str, reason: str, reported_by: Optional[str] = None) -> None:
        """
        Add a vehicle plate to the blocked list.
        
        Args:
            plate: License plate number
            reason: Reason for blocking (e.g., "Stolen", "Not authorized")
            reported_by: Name of person reporting the block
        """
        cleaned_plate = self._clean_plate_text(plate)
        self.BLOCKED_VEHICLES[cleaned_plate] = {
            'reason': reason,
            'blocked_at': datetime.now(),
            'reported_by': reported_by
        }
        logger.warning(f"🚩 Vehicle {cleaned_plate} added to blocked list: {reason}")
    
    def unblock_vehicle(self, plate: str) -> None:
        """
        Remove a vehicle from the blocked list.
        
        Args:
            plate: License plate number
        """
        cleaned_plate = self._clean_plate_text(plate)
        if cleaned_plate in self.BLOCKED_VEHICLES:
            del self.BLOCKED_VEHICLES[cleaned_plate]
            logger.info(f"✓ Vehicle {cleaned_plate} removed from blocked list")
        else:
            logger.warning(f"⚠️ Vehicle {cleaned_plate} not in blocked list")
    
    def get_gate_statistics(self) -> Dict:
        """
        Get statistics about plates processed through the quality gate.
        
        Returns:
            {
                'total_blocked_vehicles': int,
                'confidence_rejections': int,
                'format_rejections': int,
                'authorized_plates': int
            }
        """
        return {
            'total_blocked_vehicles': len(self.BLOCKED_VEHICLES),
            'blocked_plate_list': list(self.BLOCKED_VEHICLES.keys()),
            'ocr_threshold': self.OCR_CONFIDENCE_THRESHOLD,
            'supported_formats': [fmt.value for fmt in PlateFormat]
        }


# ============================================================================
# FastAPI Integration Helper
# ============================================================================

def get_vehicle_quality_gate(db_session=None, system_logger=None) -> VehicleQualityGate:
    """
    Factory function to create VehicleQualityGate instance.
    Can be used as FastAPI dependency.
    """
    return VehicleQualityGate(db_session=db_session, system_logger=system_logger)
