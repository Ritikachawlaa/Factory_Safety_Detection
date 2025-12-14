"""
Vehicle Detection using YOLO COCO pretrained model
Detects cars, trucks, buses, motorcycles
"""
from ultralytics import YOLO
from pathlib import Path

class VehicleDetector:
    """Vehicle detection using YOLO pretrained on COCO dataset"""
    
    # COCO vehicle class IDs
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle', 
        5: 'bus',
        7: 'truck'
    }
    
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.5
        
    def load(self):
        """Load YOLO pretrained model"""
        try:
            BASE_DIR = Path(__file__).parent.parent
            # Try to use yolo11n.pt if available, otherwise download yolov8n
            model_path = BASE_DIR / 'models' / 'yolo11n.pt'
            if not model_path.exists():
                model_path = BASE_DIR / 'models' / 'yolov8n.pt'
            
            self.model = YOLO(str(model_path))
            print("✅ Vehicle Detection Model Loaded")
            return True
        except Exception as e:
            print(f"❌ Vehicle model load failed: {e}")
            return False
    
    def detect(self, frame):
        """
        Detect vehicles in frame
        
        Returns:
            {
                'vehicle_count': int,
                'vehicles': list of detected vehicles with type
            }
        """
        if self.model is None:
            return self._empty_result()
        
        try:
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]
            
            vehicles = []
            
            if results.boxes:
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    
                    # Only process vehicle classes
                    if cls_id in self.VEHICLE_CLASSES:
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        
                        vehicles.append({
                            'type': self.VEHICLE_CLASSES[cls_id],
                            'x1': int(xyxy[0]),
                            'y1': int(xyxy[1]),
                            'x2': int(xyxy[2]),
                            'y2': int(xyxy[3]),
                            'confidence': conf,
                            'center_x': int((xyxy[0] + xyxy[2]) / 2),
                            'center_y': int((xyxy[1] + xyxy[3]) / 2)
                        })
            
            return {
                'vehicle_count': len(vehicles),
                'vehicles': vehicles
            }
        except Exception as e:
            print(f"Vehicle detection error: {e}")
            return self._empty_result()
    
    def _empty_result(self):
        return {
            'vehicle_count': 0,
            'vehicles': []
        }
