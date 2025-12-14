"""
Unified Detection Pipeline
Processes one frame through all enabled features
"""
import cv2
import numpy as np
from models.helmet_model import HelmetDetector
from models.box_model import BoxDetector
from models.face_model import FaceRecognizer
from models.vehicle_detector import VehicleDetector
from services.loitering import LoiteringDetector
from services.line_crossing import LineCrossingDetector
from services.motion import MotionDetector
from services.crowd_detector import CrowdDetector

class DetectionPipeline:
    """Unified pipeline for processing frames with multiple AI features"""
    
    def __init__(self):
        """Initialize all detectors"""
        # Core detectors
        self.helmet_detector = HelmetDetector()
        self.box_detector = BoxDetector()
        self.face_detector = FaceRecognizer()
        self.vehicle_detector = VehicleDetector()
        
        # Service detectors
        self.loitering_detector = LoiteringDetector(time_threshold=5)
        self.line_crossing_detector = LineCrossingDetector(line_position=0.5)
        self.motion_detector = MotionDetector(threshold=500)
        self.crowd_detector = CrowdDetector(density_threshold=5)
        
        self.models_loaded = False
        
    def load_models(self):
        """Load all ML models at startup"""
        print("\n" + "="*60)
        print("🚀 Loading AI Models...")
        print("="*60)
        
        success = True
        success &= self.helmet_detector.load()
        success &= self.box_detector.load()
        success &= self.face_detector.load()
        success &= self.vehicle_detector.load()
        
        self.models_loaded = success
        
        if success:
            print("="*60)
            print("✅ All Models Loaded Successfully")
            print("="*60 + "\n")
        else:
            print("⚠️ Some models failed to load")
        
        return success
    
    def process_frame(self, frame, enabled_features, line_x=None):
        """
        Process a single frame through all enabled features
        
        Args:
            frame: numpy array (BGR image)
            enabled_features: dict of feature flags
            line_x: Optional X position for vertical line crossing
            
        Returns:
            dict with all detection results
        """
        if not self.models_loaded:
            return self._empty_result()
        
        frame_height, frame_width = frame.shape[:2]
        
        # Initialize result
        result = {
            'frame_width': frame_width,
            'frame_height': frame_height,
            'timestamp': self._get_timestamp()
        }
        
        # Track all detected people boxes (for crowd and loitering)
        all_people_boxes = []
        
        # Feature 1 & 3: Human Detection & Helmet Detection
        if enabled_features.get('helmet', False) or enabled_features.get('human', False):
            helmet_result = self.helmet_detector.detect(frame, track=True)
            
            # Combine all people detections
            all_people_boxes.extend(helmet_result['people_boxes'])
            all_people_boxes.extend(helmet_result['helmet_boxes'])
            all_people_boxes.extend(helmet_result['violation_boxes'])
            
            result['people_count'] = helmet_result['people_count']
            result['helmet_violations'] = helmet_result['violation_count']
            result['helmet_compliant'] = helmet_result['helmet_count']
            result['ppe_compliance_rate'] = (
                (helmet_result['helmet_count'] / max(helmet_result['people_count'], 1)) * 100
            )
        else:
            # Set default values if helmet/human detection not enabled
            result['people_count'] = 0
            result['helmet_violations'] = 0
            result['helmet_compliant'] = 0
            result['ppe_compliance_rate'] = 0.0
        
        # Feature 2: Vehicle Detection
        if enabled_features.get('vehicle', False):
            vehicle_result = self.vehicle_detector.detect(frame)
            result['vehicle_count'] = vehicle_result['vehicle_count']
        else:
            result['vehicle_count'] = 0
        
        # Feature 4: Loitering Detection
        if enabled_features.get('loitering', False):
            loitering_result = self.loitering_detector.detect(all_people_boxes)
            result['loitering_detected'] = loitering_result['loitering_detected']
            result['loitering_count'] = loitering_result['loitering_count']
            result['people_groups'] = loitering_result['groups']
        else:
            result['loitering_detected'] = False
            result['loitering_count'] = 0
            result['people_groups'] = 0
        
        # Feature 5: Labour/People Count (already calculated above)
        result['labour_count'] = len(all_people_boxes)
        
        # Feature 6: Crowd Density Detection
        if enabled_features.get('crowd', False):
            crowd_result = self.crowd_detector.detect(all_people_boxes, frame_width, frame_height)
            result['crowd_detected'] = crowd_result['crowd_detected']
            result['crowd_density'] = crowd_result['density_level']
            result['occupied_area'] = crowd_result['occupied_area']
        else:
            result['crowd_detected'] = False
            result['crowd_density'] = "none"
            result['occupied_area'] = 0.0
        
        # Feature 7 & 8: Box Counting & Line Crossing (using human tracking, not boxes)
        if enabled_features.get('line_crossing', False):
            # Use tracked people boxes for line crossing
            line_result = self.line_crossing_detector.detect(
                all_people_boxes, 
                frame_width,
                line_x
            )
            result['line_crossed'] = line_result['line_crossed']
            result['total_crossings'] = line_result['total_crossings']
            result['boxes'] = line_result.get('boxes', [])
        else:
            result['line_crossed'] = False
            result['total_crossings'] = 0
            result['boxes'] = []
        
        # Box counting (separate from line crossing)
        if enabled_features.get('box_count', False):
            box_result = self.box_detector.detect(frame, track=True)
            result['box_count'] = box_result['box_count']
        else:
            result['box_count'] = 0
        
        # Feature 9: Auto Tracking (uses same tracking as people)
        if enabled_features.get('tracking', False) or enabled_features.get('line_crossing', False):
            tracked_boxes = [b for b in all_people_boxes if 'track_id' in b]
            result['tracked_objects'] = len(tracked_boxes)
            # Return boxes for visualization if tracking is specifically enabled
            if enabled_features.get('tracking', False):
                result['boxes'] = tracked_boxes
        else:
            result['tracked_objects'] = 0
            if 'boxes' not in result:
                result['boxes'] = []
        
        # Feature 10: Smart Motion Detection
        if enabled_features.get('motion', False):
            total_objects = len(all_people_boxes) + result.get('vehicle_count', 0)
            motion_result = self.motion_detector.detect(frame, total_objects)
            result['motion_detected'] = motion_result['motion_detected']
            result['motion_intensity'] = motion_result['motion_intensity']
            result['motion_ai_validated'] = motion_result['ai_validated']
        else:
            result['motion_detected'] = False
            result['motion_intensity'] = 0.0
            result['motion_ai_validated'] = False
        
        # Feature 11 & 12: Face Detection & Recognition
        # Auto-enable face detection if face recognition is requested
        if enabled_features.get('face_detection', False) or enabled_features.get('face_recognition', False):
            print("\n[PIPELINE] Running face detection...")
            face_result = self.face_detector.detect_faces(frame)
            result['faces_detected'] = face_result['face_count']
            print(f"[PIPELINE] Detected {face_result['face_count']} faces")
            
            if enabled_features.get('face_recognition', False):
                print("[PIPELINE] Running face recognition...")
                recognition_result = self.face_detector.recognize_faces(frame)
                result['faces_recognized'] = recognition_result['recognized']
                result['unknown_faces'] = recognition_result['unknown_count']
                result['registered_faces_count'] = recognition_result.get('registered_faces_count', 0)
                print(f"[PIPELINE] Recognition done: recognized={result['faces_recognized']}, unknown={result['unknown_faces']}")
            else:
                result['faces_recognized'] = []
                result['unknown_faces'] = 0
                result['registered_faces_count'] = len(self.face_detector.embeddings_cache)
        else:
            result['faces_detected'] = 0
            result['faces_recognized'] = []
            result['unknown_faces'] = 0
            result['registered_faces_count'] = 0
        
        return result
    
    def _empty_result(self):
        """Return empty result when models not loaded"""
        return {
            'error': 'Models not loaded',
            'people_count': 0,
            'vehicle_count': 0,
            'helmet_violations': 0,
            'box_count': 0,
            'faces_detected': 0
        }
    
    @staticmethod
    def _get_timestamp():
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
