"""
Box/Production Counting Model Wrapper
Reuses existing YOLOv8 custom box model with tracking
"""
from ultralytics import YOLO
from pathlib import Path
import numpy as np

class BoxDetector:
    """Wrapper for box detection and counting"""
    
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.25
        self.tracker_config = 'bytetrack.yaml'
        
    def load(self):
        """Load the existing box detection model"""
        try:
            BASE_DIR = Path(__file__).parent.parent
            model_path = BASE_DIR / 'models' / 'best_product.pt'
            self.model = YOLO(str(model_path))
            print("✅ Box Detection Model Loaded")
            return True
        except Exception as e:
            print(f"❌ Box model load failed: {e}")
            return False
    
    def detect(self, frame, track=False):
        """
        Detect boxes/products in frame
        
        Args:
            frame: Input image
            track: Whether to use tracking
            
        Returns:
            {
                'box_count': int,
                'boxes': list of detected boxes with tracking IDs
            }
        """
        if self.model is None:
            return self._empty_result()
        
        try:
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
            
            boxes = []
            
            if results.boxes:
                for box in results.boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    box_data = {
                        'x1': int(xyxy[0]),
                        'y1': int(xyxy[1]),
                        'x2': int(xyxy[2]),
                        'y2': int(xyxy[3]),
                        'confidence': conf,
                        'class_id': cls_id,
                        'center_x': int((xyxy[0] + xyxy[2]) / 2),
                        'center_y': int((xyxy[1] + xyxy[3]) / 2)
                    }
                    
                    # Add tracking ID if available
                    if track and hasattr(box, 'id') and box.id is not None:
                        box_data['track_id'] = int(box.id[0])
                    
                    boxes.append(box_data)
            
            return {
                'box_count': len(boxes),
                'boxes': boxes
            }
        except Exception as e:
            print(f"Box detection error: {e}")
            return self._empty_result()
    
    def _empty_result(self):
        return {
            'box_count': 0,
            'boxes': []
        }
