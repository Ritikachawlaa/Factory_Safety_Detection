"""
Unified Inference Pipeline - YOLOv8 + AWS Rekognition Integration
Combines local fast detection with cloud-based accurate face matching.

Modules:
- Module 1 & 3: Identity & Attendance (Face Detection + AWS Rekognition)
- Module 2: Vehicle & ANPR (Vehicle Detection + EasyOCR)
- Module 4: Occupancy (People Counting + Line Crossing)

Architecture:
Frame → YOLOv8 Detection → Tracking → [Face/Vehicle Crops] → AWS APIs / Local OCR
    ↓
State Management (Track ID Cache, Line Crossing Logic)
    ↓
Database Logging (Check-in, Vehicle Entry, Occupancy)
    ↓
JSON Response to Frontend
"""

import cv2
import base64
import boto3
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Local ML libraries
from ultralytics import YOLO
import easyocr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# AWS REKOGNITION SETUP
# ============================================================================

class AWSFaceRecognition:
    """AWS Rekognition wrapper for face matching and enrollment."""
    
    def __init__(self):
        """Initialize AWS Rekognition client."""
        self.client = boto3.client(
            'rekognition',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.collection_id = os.getenv('AWS_COLLECTION_ID', 'factory-employees')
        self._initialize_collection()
        logger.info(f"✅ AWS Rekognition initialized (Collection: {self.collection_id})")
    
    def _initialize_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.describe_collection(CollectionId=self.collection_id)
            logger.info(f"✅ Collection '{self.collection_id}' exists")
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"📝 Creating collection '{self.collection_id}'...")
            self.client.create_collection(CollectionId=self.collection_id)
            logger.info(f"✅ Collection '{self.collection_id}' created")
    
    def search_face(self, image_bytes: bytes, confidence_threshold: float = 0.85) -> Optional[Dict]:
        """
        Search for a face in the collection.
        
        Args:
            image_bytes: Raw image bytes (JPEG/PNG)
            confidence_threshold: Minimum confidence (0-100)
        
        Returns:
            {
                'employee_id': str,
                'employee_name': str,
                'confidence': float,
                'matched': bool
            }
        """
        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=confidence_threshold
            )
            
            if response['FaceMatches']:
                match = response['FaceMatches'][0]
                face_id = match['Face']['FaceId']
                confidence = match['Similarity']
                
                # Get employee info from ExternalImageId
                # Format: "employee_id|name"
                external_id = match['Face'].get('ExternalImageId', 'unknown')
                
                logger.info(f"✅ Face match found: {external_id} ({confidence:.2f}%)")
                
                try:
                    employee_id, employee_name = external_id.split('|')
                except:
                    employee_id = external_id
                    employee_name = "Unknown"
                
                return {
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'confidence': confidence,
                    'matched': True,
                    'face_id': face_id
                }
            else:
                logger.info("⚠️ No face match found")
                return {
                    'employee_id': None,
                    'employee_name': 'Unknown',
                    'confidence': 0,
                    'matched': False,
                    'face_id': None
                }
        
        except Exception as e:
            logger.error(f"❌ AWS Rekognition error: {e}")
            return {
                'employee_id': None,
                'employee_name': 'Error',
                'confidence': 0,
                'matched': False,
                'error': str(e)
            }
    
    def enroll_employee(self, image_bytes: bytes, employee_id: str, employee_name: str) -> bool:
        """
        Enroll a new employee face.
        
        Args:
            image_bytes: Raw image bytes
            employee_id: Employee ID
            employee_name: Employee name
        
        Returns:
            Success boolean
        """
        try:
            external_id = f"{employee_id}|{employee_name}"
            
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_id,
                DetectionAttributes=['ALL']
            )
            
            if response['FaceRecords']:
                face_id = response['FaceRecords'][0]['Face']['FaceId']
                logger.info(f"✅ Enrolled {employee_name} (ID: {employee_id}, Face ID: {face_id})")
                return True
            else:
                logger.error(f"❌ No face detected in enrollment image")
                return False
        
        except Exception as e:
            logger.error(f"❌ Enrollment error: {e}")
            return False


# ============================================================================
# OCRCLE - LOCAL OCR FOR PLATE READING
# ============================================================================

class PlateOCR:
    """Local OCR for license plate reading using EasyOCR."""
    
    def __init__(self):
        """Initialize OCR reader."""
        logger.info("📚 Initializing EasyOCR...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        logger.info("✅ EasyOCR initialized")
    
    def read_plate(self, image: np.ndarray, confidence_threshold: float = 0.3) -> Optional[str]:
        """
        Read license plate from image.
        
        Args:
            image: OpenCV image (BGR)
            confidence_threshold: Minimum OCR confidence
        
        Returns:
            Plate number or None
        """
        try:
            results = self.reader.readtext(image, detail=1)
            
            if not results:
                return None
            
            # Filter by confidence and concatenate text
            plate_text = ''.join([
                result[1].upper() 
                for result in results 
                if result[2] > confidence_threshold
            ]).replace(' ', '')
            
            # Validate plate format (basic)
            if len(plate_text) >= 5:
                logger.info(f"📸 Plate detected: {plate_text}")
                return plate_text
            else:
                logger.debug(f"❌ Invalid plate format: {plate_text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ OCR error: {e}")
            return None


# ============================================================================
# YOLO DETECTION & TRACKING
# ============================================================================

class YOLODetector:
    """YOLOv8 nano model for fast detection and tracking."""
    
    def __init__(self, model_name: str = 'yolov8n.pt'):
        """
        Initialize YOLO detector.
        
        Args:
            model_name: Model to load (yolov8n is nano/fastest)
        """
        logger.info(f"🎯 Loading YOLO model: {model_name}...")
        self.model = YOLO(model_name)
        logger.info("✅ YOLO model loaded")
        
        # Class names we care about
        self.person_class = 0
        self.vehicle_classes = {
            2: 'car',
            5: 'bus',
            7: 'truck',
            3: 'motorcycle'
        }
    
    def detect_and_track(self, frame: np.ndarray) -> Tuple[List[Dict], List[Dict]]:
        """
        Run YOLO detection and tracking.
        
        Args:
            frame: OpenCV image (BGR)
        
        Returns:
            (people_detections, vehicle_detections)
            Each detection: {
                'track_id': int,
                'bbox': [x1, y1, x2, y2],
                'centroid': [cx, cy],
                'confidence': float,
                'type': str
            }
        """
        try:
            # Run YOLO with tracking
            results = self.model.track(frame, persist=True, verbose=False)
            
            people = []
            vehicles = []
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Get bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Get track ID
                    track_id = int(box.id[0]) if box.id is not None else -1
                    
                    detection = {
                        'track_id': track_id,
                        'bbox': [x1, y1, x2, y2],
                        'centroid': [cx, cy],
                        'confidence': confidence,
                        'width': x2 - x1,
                        'height': y2 - y1
                    }
                    
                    # Classify as person or vehicle
                    if class_id == self.person_class:
                        detection['type'] = 'person'
                        people.append(detection)
                    elif class_id in self.vehicle_classes:
                        detection['type'] = self.vehicle_classes[class_id]
                        vehicles.append(detection)
            
            return people, vehicles
        
        except Exception as e:
            logger.error(f"❌ YOLO detection error: {e}")
            return [], []


# ============================================================================
# STATEFUL TRACKING & CACHING
# ============================================================================

class StatefulTracker:
    """Manages tracking state, caching, and line-crossing logic."""
    
    def __init__(self, cache_ttl_seconds: int = 600):
        """
        Initialize tracker.
        
        Args:
            cache_ttl_seconds: Cache time-to-live (default: 10 minutes)
        """
        # Track ID → Face Info Cache
        self.face_cache: Dict[int, Dict] = {}
        self.face_cache_time: Dict[int, datetime] = {}
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        
        # Line crossing state
        self.line_y = 350  # Virtual line Y coordinate
        self.previous_centroids: Dict[int, Tuple[int, int]] = {}
        
        # Counters
        self.entry_count = 0
        self.exit_count = 0
        self.occupancy_current = 0
        
        # Vehicle tracking
        self.vehicle_cache: Dict[int, Dict] = {}
        
        logger.info("✅ StatefulTracker initialized")
    
    def update_face_cache(self, track_id: int, face_info: Dict) -> None:
        """Update or add face to cache."""
        self.face_cache[track_id] = face_info
        self.face_cache_time[track_id] = datetime.now()
    
    def get_cached_face(self, track_id: int) -> Optional[Dict]:
        """Get face from cache if not expired."""
        if track_id not in self.face_cache:
            return None
        
        # Check if cache is still valid
        if datetime.now() - self.face_cache_time[track_id] > self.cache_ttl:
            del self.face_cache[track_id]
            del self.face_cache_time[track_id]
            return None
        
        return self.face_cache[track_id]
    
    def process_line_crossing(self, people: List[Dict]) -> Dict:
        """
        Detect line crossings (entry/exit).
        
        Returns:
            {
                'entries': int,
                'exits': int,
                'occupancy': int
            }
        """
        entries_this_frame = 0
        exits_this_frame = 0
        
        for person in people:
            track_id = person['track_id']
            cx, cy = person['centroid']
            
            if track_id in self.previous_centroids:
                prev_x, prev_y = self.previous_centroids[track_id]
                
                # Check if centroid crossed the line
                if prev_y <= self.line_y < cy:
                    # Moving downward (entering)
                    self.entry_count += 1
                    entries_this_frame += 1
                    self.occupancy_current += 1
                    logger.info(f"👤 Entry detected (Track ID: {track_id})")
                
                elif prev_y > self.line_y >= cy:
                    # Moving upward (exiting)
                    self.exit_count += 1
                    exits_this_frame += 1
                    self.occupancy_current = max(0, self.occupancy_current - 1)
                    logger.info(f"👤 Exit detected (Track ID: {track_id})")
            
            # Update previous centroid
            self.previous_centroids[track_id] = (cx, cy)
        
        # Clean up old track IDs not seen in this frame
        tracked_ids = set(p['track_id'] for p in people)
        self.previous_centroids = {
            tid: pos for tid, pos in self.previous_centroids.items()
            if tid in tracked_ids
        }
        
        return {
            'entries_this_frame': entries_this_frame,
            'exits_this_frame': exits_this_frame,
            'total_entries': self.entry_count,
            'total_exits': self.exit_count,
            'occupancy': self.occupancy_current
        }


# ============================================================================
# UNIFIED INFERENCE ENGINE
# ============================================================================

class UnifiedInferenceEngine:
    """Main inference engine combining all modules."""
    
    def __init__(self):
        """Initialize all components."""
        logger.info("=" * 80)
        logger.info("🚀 Initializing Unified Inference Engine")
        logger.info("=" * 80)
        
        # Initialize components
        self.yolo = YOLODetector(model_name='yolov8n.pt')
        self.aws_face = AWSFaceRecognition()
        self.ocr = PlateOCR()
        self.tracker = StatefulTracker()
        
        # Frame counter
        self.frame_count = 0
        
        logger.info("=" * 80)
        logger.info("✅ All components initialized")
        logger.info("=" * 80)
    
    def process_frame(self, frame_base64: str) -> Dict:
        """
        Process a single frame through the entire pipeline.
        
        Args:
            frame_base64: Base64 encoded image
        
        Returns:
            {
                'success': bool,
                'frame_id': int,
                'timestamp': str,
                'occupancy': int,
                'entries': int,
                'exits': int,
                'faces_recognized': [
                    {'track_id': int, 'name': str, 'confidence': float}
                ],
                'vehicles_detected': [
                    {'track_id': int, 'type': str, 'plate': str}
                ],
                'processing_time_ms': float
            }
        """
        start_time = datetime.now()
        self.frame_count += 1
        
        try:
            # Decode frame
            frame_data = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise ValueError("Failed to decode frame")
            
            logger.info(f"📹 Processing frame #{self.frame_count}")
            
            # YOLO Detection & Tracking
            people, vehicles = self.yolo.detect_and_track(frame)
            
            # Process people (Module 1 & 3: Identity & Attendance)
            recognized_faces = []
            for person in people:
                track_id = person['track_id']
                
                # Check cache first (save AWS costs)
                cached_face = self.tracker.get_cached_face(track_id)
                if cached_face:
                    logger.info(f"💾 Using cached face for Track ID {track_id}")
                    recognized_faces.append({
                        'track_id': track_id,
                        'name': cached_face['employee_name'],
                        'confidence': cached_face['confidence'],
                        'source': 'cache'
                    })
                    continue
                
                # Crop face region from frame
                x1, y1, x2, y2 = person['bbox']
                face_crop = frame[y1:y2, x1:x2]
                
                # Convert to JPEG bytes for AWS
                _, face_jpeg = cv2.imencode('.jpg', face_crop)
                face_bytes = face_jpeg.tobytes()
                
                # Query AWS Rekognition
                face_result = self.aws_face.search_face(face_bytes)
                
                if face_result['matched']:
                    # Cache the result
                    self.tracker.update_face_cache(track_id, face_result)
                    
                    recognized_faces.append({
                        'track_id': track_id,
                        'name': face_result['employee_name'],
                        'confidence': face_result['confidence'],
                        'source': 'aws'
                    })
                    
                    logger.info(f"✅ Face recognized: {face_result['employee_name']} (Track {track_id})")
                else:
                    logger.info(f"⚠️ Unknown face detected (Track {track_id})")
            
            # Process vehicles (Module 2: Vehicle & ANPR)
            detected_vehicles = []
            for vehicle in vehicles:
                track_id = vehicle['track_id']
                vehicle_type = vehicle['type']
                
                x1, y1, x2, y2 = vehicle['bbox']
                vehicle_crop = frame[y1:y2, x1:x2]
                
                # Try to read license plate
                plate = self.ocr.read_plate(vehicle_crop)
                
                detected_vehicles.append({
                    'track_id': track_id,
                    'type': vehicle_type,
                    'plate': plate or 'Not detected',
                    'confidence': vehicle['confidence']
                })
            
            # Process line crossing (Module 4: Occupancy)
            occupancy_data = self.tracker.process_line_crossing(people)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response = {
                'success': True,
                'frame_id': self.frame_count,
                'timestamp': datetime.now().isoformat(),
                'occupancy': occupancy_data['occupancy'],
                'entries': occupancy_data['total_entries'],
                'exits': occupancy_data['total_exits'],
                'entries_this_frame': occupancy_data['entries_this_frame'],
                'exits_this_frame': occupancy_data['exits_this_frame'],
                'faces_recognized': recognized_faces,
                'vehicles_detected': detected_vehicles,
                'people_count': len(people),
                'vehicle_count': len(vehicles),
                'processing_time_ms': round(processing_time, 2)
            }
            
            logger.info(f"✅ Frame processed in {response['processing_time_ms']}ms")
            return response
        
        except Exception as e:
            logger.error(f"❌ Frame processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def enroll_employee_from_base64(self, image_base64: str, employee_id: str, employee_name: str) -> bool:
        """
        Enroll a new employee from base64 image.
        
        Args:
            image_base64: Base64 encoded image
            employee_id: Employee ID
            employee_name: Employee name
        
        Returns:
            Success boolean
        """
        try:
            frame_data = base64.b64decode(image_base64)
            return self.aws_face.enroll_employee(frame_data, employee_id, employee_name)
        except Exception as e:
            logger.error(f"❌ Enrollment error: {e}")
            return False


# ============================================================================
# GLOBAL INSTANCE (Singleton)
# ============================================================================

# Initialize on module load
try:
    inference_engine = UnifiedInferenceEngine()
    logger.info("✅ Inference engine ready")
except Exception as e:
    logger.error(f"❌ Failed to initialize inference engine: {e}")
    inference_engine = None
