"""
Crowd Density Detection Service
Detects crowded areas and triggers alerts
"""

class CrowdDetector:
    """Detect crowd density and trigger alerts"""
    
    def __init__(self, density_threshold=5, area_threshold=0.2):
        """
        Args:
            density_threshold: Number of people to trigger crowd alert
            area_threshold: Fraction of frame area occupied to trigger
        """
        self.density_threshold = density_threshold
        self.area_threshold = area_threshold
        
    def detect(self, people_boxes, frame_width, frame_height):
        """
        Detect crowd density
        
        Args:
            people_boxes: List of people bounding boxes
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            
        Returns:
            {
                'crowd_detected': bool,
                'people_count': int,
                'density_level': str (low/medium/high),
                'occupied_area': float (0-1)
            }
        """
        people_count = len(people_boxes)
        
        if people_count == 0:
            return {
                'crowd_detected': False,
                'people_count': 0,
                'density_level': 'none',
                'occupied_area': 0.0
            }
        
        # Calculate occupied area
        frame_area = frame_width * frame_height
        total_box_area = 0
        
        for box in people_boxes:
            width = box['x2'] - box['x1']
            height = box['y2'] - box['y1']
            total_box_area += (width * height)
        
        occupied_ratio = min(total_box_area / frame_area, 1.0)
        
        # Determine density level
        if people_count >= self.density_threshold * 2:
            density_level = 'high'
        elif people_count >= self.density_threshold:
            density_level = 'medium'
        else:
            density_level = 'low'
        
        # Crowd alert if count exceeds threshold OR area exceeds threshold
        crowd_detected = (
            people_count >= self.density_threshold or 
            occupied_ratio >= self.area_threshold
        )
        
        return {
            'crowd_detected': crowd_detected,
            'people_count': people_count,
            'density_level': density_level,
            'occupied_area': float(occupied_ratio)
        }
