"""
Helmet/PPE Detection Model Wrapper
Reuses existing YOLOv8 custom helmet model with tracking
"""
from ultralytics import YOLO
from pathlib import Path
import numpy as np

class HelmetDetector:
    """Wrapper for helmet detection using existing custom YOLO model"""
    
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.5
        self.tracker_config = "bytetrack.yaml"  # ByteTrack for stable tracking
        
    def load(self):
        """Load the existing helmet model"""
        try:
            BASE_DIR = Path(__file__).parent.parent
            model_path = BASE_DIR / 'models' / 'best_helmet.pt'
            self.model = YOLO(str(model_path))
            print("✅ Helmet Detection Model Loaded")
            return True
        except Exception as e:
            print(f"❌ Helmet model load failed: {e}")
            return False
    
    def detect(self, frame, track=True):
        """
        Detect people, helmets, and violations
        
        Args:
            frame: Input image
            track: Whether to use tracking for stable IDs
        
        Returns:
            {
                'people_count': int,
                'helmet_count': int,
                'violation_count': int,
                'people_boxes': list,
                'helmet_boxes': list,
                'violation_boxes': list
            }
        """
        if self.model is None:
            return self._empty_result()
        
        try:
            # Use YOLO tracking if enabled, otherwise standard detection
            if track:
                results = self.model.track(
                    frame,
                    conf=self.confidence_threshold,
                    persist=True,
                    tracker=self.tracker_config,
                    verbose=False
                )[0]
            else:
                results = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]
            
            people_boxes = []
            helmet_boxes = []
            violation_boxes = []
            
            if results.boxes:
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    
                    center_x = int((xyxy[0] + xyxy[2]) / 2)
                    center_y = int((xyxy[1] + xyxy[3]) / 2)
                    
                    box_data = {
                        'x1': int(xyxy[0]),
                        'y1': int(xyxy[1]),
                        'x2': int(xyxy[2]),
                        'y2': int(xyxy[3]),
                        'confidence': conf,
                        'class_id': cls_id,
                        'center_x': center_x,
                        'center_y': center_y
                    }
                    
                    # Add tracking ID if available (from YOLO tracking)
                    if track and hasattr(box, 'id') and box.id is not None:
                        box_data['track_id'] = int(box.id[0])
                    
                    # Class mapping: 0=head (no helmet), 1=hardhat, 2=person
                    if cls_id == 0:  # head without helmet - VIOLATION
                        violation_boxes.append(box_data)
                    elif cls_id == 1:  # hardhat - COMPLIANT
                        helmet_boxes.append(box_data)
                    elif cls_id == 2:  # person
                        people_boxes.append(box_data)
            
            return {
                'people_count': len(people_boxes) + len(helmet_boxes) + len(violation_boxes),
                'helmet_count': len(helmet_boxes),
                'violation_count': len(violation_boxes),
                'people_boxes': people_boxes,
                'helmet_boxes': helmet_boxes,
                'violation_boxes': violation_boxes
            }
        except Exception as e:
            print(f"Helmet detection error: {e}")
            return self._empty_result()
    
    def _empty_result(self):
        return {
            'people_count': 0,
            'helmet_count': 0,
            'violation_count': 0,
            'people_boxes': [],
            'helmet_boxes': [],
            'violation_boxes': []
        }
