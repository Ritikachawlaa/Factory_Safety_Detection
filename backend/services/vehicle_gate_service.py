"""
Vehicle & Gate Management Service
Handles YOLO vehicle detection, ByteTrack stateful tracking, and license plate recognition (ANPR).

Key Features:
- Vehicle classification: Car, Truck, Bike, Forklift, Bus
- Stateful ANPR logic (OCR only triggered at gate zone entry)
- ByteTrack integration for persistent vehicle tracking
- Gate access authorization checks
- Snapshot capture for blocked/unknown vehicles
- Real-time vehicle count by type
- 90-day data retention policy
"""

import os
import cv2
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict

try:
    import easyocr
    OCR_ENGINE = "easyocr"
except ImportError:
    try:
        from paddleocr import PaddleOCR
        OCR_ENGINE = "paddleocr"
    except ImportError:
        OCR_ENGINE = None

from ultralytics import YOLO
from bytetrack import ByteTrack

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VehicleGateService - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VehicleType(str, Enum):
    """Supported vehicle types for classification."""
    CAR = "car"
    TRUCK = "truck"
    BIKE = "bike"
    FORKLIFT = "forklift"
    BUS = "bus"
    UNKNOWN = "unknown"


class PlateStatus(str, Enum):
    """License plate authorization status."""
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class GateAlertType(str, Enum):
    """Types of gate alerts that trigger warnings."""
    BLOCKED_VEHICLE = "blocked_vehicle"
    UNKNOWN_VEHICLE = "unknown_vehicle"
    INVALID_PLATE = "invalid_plate"
    UNAUTHORIZED_TYPE = "unauthorized_type"


@dataclass
class VehicleSession:
    """In-memory session for tracking vehicle detection state."""
    track_id: int
    vehicle_type: VehicleType
    detected_at: float
    plate_number: Optional[str] = None
    plate_confidence: float = 0.0
    status: PlateStatus = PlateStatus.UNKNOWN
    gate_zone_entered_at: Optional[float] = None
    ocr_triggered: bool = False
    last_seen_frame: int = 0
    snapshot_path: Optional[str] = None
    full_frame_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if vehicle session has expired (not seen for timeout_seconds)."""
        return (time.time() - self.detected_at) > timeout_seconds


@dataclass
class FrameGateAlert:
    """Alert triggered for blocked or unknown vehicles at gate."""
    alert_type: GateAlertType
    track_id: int
    vehicle_type: VehicleType
    plate_number: Optional[str]
    timestamp: datetime
    frame_index: int
    snapshot_path: Optional[str] = None
    confidence: float = 0.0
    message: str = ""


class GateZoneROI:
    """
    Defines Region of Interest (ROI) for gate zone.
    Optimizes performance by only running OCR when vehicle enters gate zone.
    """
    
    def __init__(self, frame_height: int, frame_width: int, zone_percentage: float = 0.3):
        """
        Initialize gate zone ROI (default: bottom 30% of frame).
        
        Args:
            frame_height: Height of frame
            frame_width: Width of frame
            zone_percentage: Percentage of frame height for gate zone (0.0-1.0)
        """
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.zone_percentage = min(max(zone_percentage, 0.0), 1.0)
        
        # Define ROI: bottom section of frame
        self.start_y = int(frame_height * (1.0 - self.zone_percentage))
        self.end_y = frame_height
        self.start_x = 0
        self.end_x = frame_width
    
    def is_point_in_zone(self, x: float, y: float) -> bool:
        """Check if point (x, y) is within gate zone."""
        return self.start_x <= x <= self.end_x and self.start_y <= y <= self.end_y
    
    def is_bbox_in_zone(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if bounding box enters gate zone."""
        # Check if bottom of bbox is in zone
        bbox_center_y = (y1 + y2) / 2
        return self.is_point_in_zone(x1, bbox_center_y) or \
               self.is_point_in_zone(x2, bbox_center_y) or \
               self.is_point_in_zone((x1 + x2) / 2, y2)
    
    def draw_zone(self, frame: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """Draw gate zone overlay on frame for visualization."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.start_x, self.start_y), (self.end_x, self.end_y), color, -1)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        cv2.rectangle(frame, (self.start_x, self.start_y), (self.end_x, self.end_y), color, thickness)
        return frame


class ANPRProcessor:
    """License Plate Recognition (ANPR) processor using EasyOCR or PaddleOCR."""
    
    def __init__(self, 
                 engine: str = "easyocr",
                 confidence_threshold: float = 0.6,
                 use_gpu: bool = True):
        """
        Initialize ANPR processor.
        
        Args:
            engine: OCR engine ("easyocr" or "paddleocr")
            confidence_threshold: Minimum confidence for plate recognition
            use_gpu: Use GPU acceleration if available
        """
        self.engine_name = engine
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu
        self.ocr = None
        self.init_time = time.time()
        
        try:
            if engine == "easyocr":
                self.ocr = easyocr.Reader(['en'], gpu=use_gpu)
                logger.info("✓ EasyOCR initialized for ANPR")
            elif engine == "paddleocr":
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=use_gpu)
                logger.info("✓ PaddleOCR initialized for ANPR")
            else:
                logger.warning(f"Unknown OCR engine: {engine}")
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine {engine}: {e}")
            self.ocr = None
    
    def extract_plate_region(self, 
                            frame: np.ndarray, 
                            bbox: Tuple[float, float, float, float],
                            pad_ratio: float = 0.1) -> Optional[np.ndarray]:
        """
        Extract license plate region from frame using bounding box.
        
        Args:
            frame: Input frame
            bbox: Bounding box (x1, y1, x2, y2)
            pad_ratio: Padding ratio around bbox
            
        Returns:
            Cropped plate region or None
        """
        try:
            x1, y1, x2, y2 = bbox
            h, w = frame.shape[:2]
            
            # Apply padding
            pad_x = int((x2 - x1) * pad_ratio)
            pad_y = int((y2 - y1) * pad_ratio)
            
            x1 = max(0, int(x1) - pad_x)
            y1 = max(0, int(y1) - pad_y)
            x2 = min(w, int(x2) + pad_x)
            y2 = min(h, int(y2) + pad_y)
            
            plate_region = frame[y1:y2, x1:x2]
            
            # Validate extraction
            if plate_region.size == 0:
                logger.warning("Empty plate region extracted")
                return None
            
            return plate_region
        except Exception as e:
            logger.error(f"Error extracting plate region: {e}")
            return None
    
    def enhance_plate_image(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Enhance license plate image for better OCR accuracy.
        Especially important for night-time/IR images.
        
        Args:
            plate_image: Extracted plate region
            
        Returns:
            Enhanced plate image
        """
        try:
            # Convert to grayscale
            if len(plate_image.shape) == 3:
                gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_image
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Bilateral filtering to reduce noise while preserving edges
            enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Thresholding for better contrast
            _, enhanced = cv2.threshold(enhanced, 100, 255, cv2.THRESH_BINARY)
            
            return enhanced
        except Exception as e:
            logger.warning(f"Error enhancing plate image: {e}")
            return plate_image
    
    def recognize_plate(self, plate_image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize license plate from image.
        
        Args:
            plate_image: Plate region image
            
        Returns:
            (plate_number, confidence) tuple
        """
        if self.ocr is None:
            logger.warning("OCR engine not initialized")
            return None, 0.0
        
        try:
            # Enhance image for better accuracy
            enhanced = self.enhance_plate_image(plate_image)
            
            if self.engine_name == "easyocr":
                results = self.ocr.readtext(enhanced, detail=1)
                if results:
                    # Concatenate all detected text
                    plate_text = ''.join([item[1] for item in results])
                    confidence = np.mean([item[2] for item in results])
                else:
                    plate_text = None
                    confidence = 0.0
            
            elif self.engine_name == "paddleocr":
                results = self.ocr.ocr(enhanced, cls=True)
                if results and results[0]:
                    plate_text = ''.join([item[1][0] for item in results[0]])
                    confidence = np.mean([item[1][1] for item in results[0]])
                else:
                    plate_text = None
                    confidence = 0.0
            else:
                return None, 0.0
            
            # Filter confidence threshold
            if confidence >= self.confidence_threshold:
                # Clean up plate text: remove spaces, convert to uppercase
                plate_text = plate_text.replace(' ', '').upper() if plate_text else None
                logger.debug(f"Recognized plate: {plate_text} (confidence: {confidence:.2f})")
                return plate_text, confidence
            else:
                logger.debug(f"Low confidence for plate: {confidence:.2f}")
                return None, confidence
                
        except Exception as e:
            logger.error(f"Error recognizing plate: {e}")
            return None, 0.0


class VehicleDetector:
    """YOLO-based vehicle detection and classification."""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize vehicle detector.
        
        Args:
            model_path: Path to YOLOv8 model
            confidence_threshold: Minimum confidence for detection
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.vehicle_classes = {
            'car': VehicleType.CAR,
            'truck': VehicleType.TRUCK,
            'motorcycle': VehicleType.BIKE,
            'bike': VehicleType.BIKE,
            'bus': VehicleType.BUS,
            'forklift': VehicleType.FORKLIFT,
        }
        logger.info(f"✓ YOLOv8 vehicle detector initialized: {model_path}")
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Tuple[Tuple[float, float, float, float], VehicleType, float]]:
        """
        Detect vehicles in frame.
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            List of (bbox, vehicle_type, confidence) tuples
        """
        try:
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            detections = []
            
            for result in results:
                for box in result.boxes:
                    # Extract bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id].lower()
                    
                    # Map to vehicle type
                    vehicle_type = self.vehicle_classes.get(class_name, VehicleType.UNKNOWN)
                    
                    detections.append(((x1, y1, x2, y2), vehicle_type, confidence))
            
            return detections
        
        except Exception as e:
            logger.error(f"Error detecting vehicles: {e}")
            return []


class VehicleGateService:
    """
    Main service orchestrating vehicle detection, ANPR, gate access, and logging.
    
    Architecture:
    1. YOLO detects vehicles → returns bboxes + class
    2. ByteTrack assigns track_ids
    3. Gate zone ROI checks if vehicle entered gate
    4. ANPR triggers (only once per track_id at gate entry)
    5. Database lookup for authorization
    6. Alert generation if blocked/unknown
    7. Snapshot capture for blocked/unknown vehicles
    8. Access logging to database
    """
    
    def __init__(self,
                 model_path: str = "yolov8n.pt",
                 ocr_engine: str = "easyocr",
                 confidence_threshold: float = 0.5,
                 ocr_confidence: float = 0.6,
                 snapshot_dir: str = "snapshots/vehicles",
                 use_gpu: bool = True,
                 frame_width: int = 1920,
                 frame_height: int = 1080,
                 gate_zone_percentage: float = 0.3,
                 session_timeout: int = 300):
        """
        Initialize Vehicle Gate Service.
        
        Args:
            model_path: YOLO model path
            ocr_engine: OCR engine ("easyocr" or "paddleocr")
            confidence_threshold: YOLO detection confidence
            ocr_confidence: OCR plate recognition confidence
            snapshot_dir: Directory for saving snapshots
            use_gpu: Enable GPU acceleration
            frame_width: Frame width for ROI calculation
            frame_height: Frame height for ROI calculation
            gate_zone_percentage: Gate zone size (0.0-1.0)
            session_timeout: Vehicle session timeout in seconds
        """
        self.detector = VehicleDetector(model_path, confidence_threshold)
        self.anpr = ANPRProcessor(ocr_engine, ocr_confidence, use_gpu)
        self.tracker = ByteTrack()
        
        # Gate zone ROI
        self.gate_zone = GateZoneROI(frame_height, frame_width, gate_zone_percentage)
        
        # Vehicle sessions tracking
        self.sessions: Dict[int, VehicleSession] = {}
        self.session_timeout = session_timeout
        self.sessions_lock = threading.Lock()
        
        # Real-time vehicle counts by type
        self.vehicle_counts: Dict[VehicleType, int] = defaultdict(int)
        self.counts_lock = threading.Lock()
        
        # Alerts
        self.alerts: List[FrameGateAlert] = []
        self.alerts_lock = threading.Lock()
        
        # Snapshot configuration
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.frame_count = 0
        self.total_vehicles_detected = 0
        self.total_plates_recognized = 0
        
        logger.info(f"✓ VehicleGateService initialized")
        logger.info(f"  - Gate zone: bottom {gate_zone_percentage*100}% of frame")
        logger.info(f"  - OCR engine: {ocr_engine}")
        logger.info(f"  - Session timeout: {session_timeout}s")
    
    def _cleanup_expired_sessions(self):
        """Remove expired vehicle sessions."""
        with self.sessions_lock:
            expired_ids = [
                track_id for track_id, session in self.sessions.items()
                if session.is_expired(self.session_timeout)
            ]
            
            for track_id in expired_ids:
                session = self.sessions.pop(track_id)
                with self.counts_lock:
                    self.vehicle_counts[session.vehicle_type] -= 1
                logger.debug(f"Session expired: track_id={track_id}")
    
    def _save_snapshot(self, frame: np.ndarray, label: str, track_id: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Save high-resolution snapshots for audit purposes.
        
        Args:
            frame: Input frame
            label: Label for snapshot (e.g., "blocked", "unknown")
            track_id: Vehicle track ID
            
        Returns:
            (plate_snapshot_path, full_frame_path) tuple
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create subdirectory by date
            date_dir = self.snapshot_dir / datetime.now().strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save full frame
            full_frame_filename = f"vehicle_{track_id}_{label}_{timestamp}_full.jpg"
            full_frame_path = date_dir / full_frame_filename
            cv2.imwrite(str(full_frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.info(f"Snapshot saved: {full_frame_path}")
            return None, str(full_frame_path)
        
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            return None, None
    
    def process_frame(self, 
                     frame: np.ndarray, 
                     frame_index: int,
                     get_authorized_plates_func=None) -> Tuple[Dict[int, VehicleSession], List[FrameGateAlert]]:
        """
        Main processing pipeline for a single frame.
        
        Args:
            frame: Input frame (BGR)
            frame_index: Frame index/counter
            get_authorized_plates_func: Callable to get authorized plates from DB
            
        Returns:
            (vehicle_sessions, alerts) tuple
        """
        self.frame_count += 1
        
        # Step 1: Detect vehicles
        detections = self.detector.detect_vehicles(frame)
        
        # Step 2: Track vehicles
        track_detections = []
        for bbox, vehicle_type, confidence in detections:
            x1, y1, x2, y2 = bbox
            track_detections.append([x1, y1, x2, y2, confidence])
        
        online_targets = self.tracker.update(np.array(track_detections)) if track_detections else []
        
        # Update vehicle counts
        current_types = defaultdict(int)
        frame_alerts = []
        
        # Step 3-7: Process each tracked vehicle
        for target in online_targets:
            track_id = int(target.track_id)
            x1, y1, x2, y2 = target.tlbr
            
            # Find matching detection for vehicle type
            vehicle_type = VehicleType.UNKNOWN
            for bbox, vtype, conf in detections:
                if self._bbox_iou(bbox, (x1, y1, x2, y2)) > 0.5:
                    vehicle_type = vtype
                    break
            
            # Create or update session
            with self.sessions_lock:
                if track_id not in self.sessions:
                    session = VehicleSession(
                        track_id=track_id,
                        vehicle_type=vehicle_type,
                        detected_at=time.time(),
                        last_seen_frame=frame_index
                    )
                    self.sessions[track_id] = session
                    self.total_vehicles_detected += 1
                    logger.debug(f"New vehicle: track_id={track_id}, type={vehicle_type}")
                else:
                    session = self.sessions[track_id]
                    session.last_seen_frame = frame_index
            
            current_types[vehicle_type] += 1
            
            # Check if vehicle entered gate zone
            in_gate_zone = self.gate_zone.is_bbox_in_zone(x1, y1, x2, y2)
            
            if in_gate_zone and not session.ocr_triggered:
                # Step 4: Trigger ANPR (only once per track_id)
                session.gate_zone_entered_at = time.time()
                
                # Extract and recognize plate
                plate_image = self.anpr.extract_plate_region(frame, (x1, y1, x2, y2))
                if plate_image is not None:
                    plate_number, plate_confidence = self.anpr.recognize_plate(plate_image)
                    
                    if plate_number:
                        session.plate_number = plate_number
                        session.plate_confidence = plate_confidence
                        self.total_plates_recognized += 1
                        logger.info(f"Plate recognized: {plate_number} (confidence: {plate_confidence:.2f})")
                    else:
                        session.plate_number = "UNREADABLE"
                        session.plate_confidence = plate_confidence
                        logger.warning(f"Failed to recognize plate (confidence: {plate_confidence:.2f})")
                
                session.ocr_triggered = True
                
                # Step 5-6: Check authorization and generate alerts
                if session.plate_number:
                    authorized_plates = get_authorized_plates_func() if get_authorized_plates_func else {}
                    
                    if session.plate_number in authorized_plates:
                        plate_data = authorized_plates[session.plate_number]
                        if plate_data.get('status') == 'blocked':
                            session.status = PlateStatus.BLOCKED
                            alert = FrameGateAlert(
                                alert_type=GateAlertType.BLOCKED_VEHICLE,
                                track_id=track_id,
                                vehicle_type=vehicle_type,
                                plate_number=session.plate_number,
                                timestamp=datetime.now(),
                                frame_index=frame_index,
                                confidence=plate_confidence,
                                message=f"BLOCKED: {session.plate_number} - {plate_data.get('owner_name', 'Unknown')}"
                            )
                            frame_alerts.append(alert)
                            
                            # Save snapshot
                            _, full_frame_path = self._save_snapshot(frame, "blocked", track_id)
                            session.full_frame_path = full_frame_path
                        else:
                            session.status = PlateStatus.AUTHORIZED
                    else:
                        session.status = PlateStatus.UNKNOWN
                        alert = FrameGateAlert(
                            alert_type=GateAlertType.UNKNOWN_VEHICLE,
                            track_id=track_id,
                            vehicle_type=vehicle_type,
                            plate_number=session.plate_number,
                            timestamp=datetime.now(),
                            frame_index=frame_index,
                            confidence=plate_confidence,
                            message=f"UNKNOWN: {session.plate_number}"
                        )
                        frame_alerts.append(alert)
                        
                        # Save snapshot
                        _, full_frame_path = self._save_snapshot(frame, "unknown", track_id)
                        session.full_frame_path = full_frame_path
                else:
                    # Plate not readable
                    session.status = PlateStatus.UNKNOWN
                    alert = FrameGateAlert(
                        alert_type=GateAlertType.INVALID_PLATE,
                        track_id=track_id,
                        vehicle_type=vehicle_type,
                        plate_number=None,
                        timestamp=datetime.now(),
                        frame_index=frame_index,
                        confidence=0.0,
                        message=f"UNREADABLE PLATE: {session.plate_number if session.plate_number == 'UNREADABLE' else 'No plate detected'}"
                    )
                    frame_alerts.append(alert)
                    
                    # Save snapshot
                    _, full_frame_path = self._save_snapshot(frame, "unreadable", track_id)
                    session.full_frame_path = full_frame_path
        
        # Update vehicle counts
        with self.counts_lock:
            self.vehicle_counts = current_types
        
        # Cleanup expired sessions
        self._cleanup_expired_sessions()
        
        # Store alerts
        with self.alerts_lock:
            self.alerts.extend(frame_alerts)
        
        return self.sessions.copy(), frame_alerts
    
    def get_vehicle_counts(self) -> Dict[str, int]:
        """Get current real-time vehicle counts by type."""
        with self.counts_lock:
            return {vtype.value: count for vtype, count in self.vehicle_counts.items()}
    
    def get_active_sessions(self) -> List[VehicleSession]:
        """Get all active vehicle sessions."""
        with self.sessions_lock:
            return list(self.sessions.values())
    
    def get_recent_alerts(self, limit: int = 100) -> List[FrameGateAlert]:
        """Get recent gate alerts."""
        with self.alerts_lock:
            return self.alerts[-limit:]
    
    def clear_alerts(self):
        """Clear all alerts."""
        with self.alerts_lock:
            self.alerts.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "frame_count": self.frame_count,
            "total_vehicles_detected": self.total_vehicles_detected,
            "total_plates_recognized": self.total_plates_recognized,
            "active_sessions": len(self.sessions),
            "vehicle_counts": self.get_vehicle_counts(),
            "pending_alerts": len(self.alerts),
            "ocr_engine": self.anpr.engine_name,
        }
    
    def _bbox_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate IoU between two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        inter_x1 = max(x1_1, x1_2)
        inter_y1 = max(y1_1, y1_2)
        inter_x2 = min(x2_1, x2_2)
        inter_y2 = min(y2_1, y2_2)
        
        if inter_x2 < inter_x1 or inter_y2 < inter_y1:
            return 0.0
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0


class VehicleReportingUtility:
    """Utility for generating vehicle traffic reports (daily/monthly summaries)."""
    
    @staticmethod
    def generate_daily_summary(logs: List[Dict[str, Any]], 
                              date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate daily traffic summary from access logs.
        
        Args:
            logs: List of vehicle access logs
            date: Date to summarize (default: today)
            
        Returns:
            Summary dictionary with statistics
        """
        if date is None:
            date = datetime.now()
        
        daily_logs = [log for log in logs if log['entry_time'].date() == date.date()]
        
        summary = {
            "date": date.strftime("%Y-%m-%d"),
            "total_vehicles": len(daily_logs),
            "by_type": defaultdict(int),
            "by_status": defaultdict(int),
            "authorized_count": 0,
            "blocked_count": 0,
            "unknown_count": 0,
            "peak_hour": None,
            "peak_hour_count": 0,
        }
        
        hourly_counts = defaultdict(int)
        
        for log in daily_logs:
            vehicle_type = log.get('vehicle_type', 'unknown')
            status = log.get('status', 'unknown')
            
            summary["by_type"][vehicle_type] += 1
            summary["by_status"][status] += 1
            
            if status == 'authorized':
                summary["authorized_count"] += 1
            elif status == 'blocked':
                summary["blocked_count"] += 1
            else:
                summary["unknown_count"] += 1
            
            hour = log['entry_time'].hour
            hourly_counts[hour] += 1
        
        # Find peak hour
        if hourly_counts:
            peak_hour = max(hourly_counts, key=hourly_counts.get)
            summary["peak_hour"] = f"{peak_hour:02d}:00-{peak_hour+1:02d}:00"
            summary["peak_hour_count"] = hourly_counts[peak_hour]
        
        return summary
    
    @staticmethod
    def generate_monthly_summary(logs: List[Dict[str, Any]], 
                                year: int, 
                                month: int) -> Dict[str, Any]:
        """
        Generate monthly traffic summary.
        
        Args:
            logs: List of vehicle access logs
            year: Year
            month: Month (1-12)
            
        Returns:
            Summary dictionary with statistics
        """
        monthly_logs = [
            log for log in logs
            if log['entry_time'].year == year and log['entry_time'].month == month
        ]
        
        summary = {
            "period": f"{year}-{month:02d}",
            "total_vehicles": len(monthly_logs),
            "by_type": defaultdict(int),
            "by_status": defaultdict(int),
            "authorized_count": 0,
            "blocked_count": 0,
            "unknown_count": 0,
            "daily_average": 0,
            "employee_vehicles": 0,
            "vendor_vehicles": 0,
        }
        
        daily_counts = defaultdict(int)
        
        for log in monthly_logs:
            vehicle_type = log.get('vehicle_type', 'unknown')
            status = log.get('status', 'unknown')
            category = log.get('category', 'unknown')
            
            summary["by_type"][vehicle_type] += 1
            summary["by_status"][status] += 1
            
            if status == 'authorized':
                summary["authorized_count"] += 1
            elif status == 'blocked':
                summary["blocked_count"] += 1
            else:
                summary["unknown_count"] += 1
            
            if category == 'employee':
                summary["employee_vehicles"] += 1
            elif category == 'vendor':
                summary["vendor_vehicles"] += 1
            
            day = log['entry_time'].date()
            daily_counts[day] += 1
        
        summary["daily_average"] = len(monthly_logs) / len(daily_counts) if daily_counts else 0
        
        return summary


if __name__ == "__main__":
    # Example usage
    print("Vehicle Gate Service initialized successfully")
