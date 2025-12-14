"""
Line Crossing Detection Service
Tracks objects crossing a VERTICAL line (left→right only)
"""

class LineCrossingDetector:
    """Detect objects crossing a vertical line (left→right)"""
    
    def __init__(self, line_position=0.5):
        """
        Args:
            line_position: Horizontal position of line (0-1, default 0.5 = middle)
        """
        self.line_position = line_position
        self.crossed_ids = set()  # Track which IDs have crossed (left→right only)
        self.object_positions = {}  # Track last X position of each object
        
    def detect(self, boxes, frame_width, line_x=None):
        """
        Detect line crossings (left→right only)
        
        Args:
            boxes: List of boxes with tracking IDs and coordinates
            frame_width: Width of frame in pixels
            line_x: Exact X position of line (overrides line_position if provided)
            
        Returns:
            {
                'line_crossed': bool - True if any new crossings detected
                'total_crossings': int - Total count of crossings
                'crossing_ids': list - IDs that crossed in this frame
                'boxes': list - Boxes with track_id for frontend visualization
            }
        """
        # Calculate line X position
        if line_x is not None:
            line_x_pos = int(line_x)
        else:
            line_x_pos = int(frame_width * self.line_position)
        
        new_crossings = []
        output_boxes = []
        
        for box in boxes:
            if 'track_id' not in box:
                continue
            
            track_id = box['track_id']
            
            # Calculate centroid X
            x1 = box.get('x1', 0)
            x2 = box.get('x2', 0)
            center_x = (x1 + x2) / 2
            
            # Add box to output with track_id for visualization
            output_boxes.append({
                'x1': int(x1),
                'y1': int(box.get('y1', 0)),
                'x2': int(x2),
                'y2': int(box.get('y2', 0)),
                'track_id': track_id
            })
            
            # Check for LEFT → RIGHT crossing
            if track_id in self.object_positions:
                prev_x = self.object_positions[track_id]
                
                # Detect crossing: moved from left to right across line
                if prev_x < line_x_pos and center_x >= line_x_pos:
                    if track_id not in self.crossed_ids:
                        self.crossed_ids.add(track_id)
                        new_crossings.append(track_id)
                        print(f"🚶 Line Crossing: Track {track_id} crossed LEFT→RIGHT")
            
            # Update position
            self.object_positions[track_id] = center_x
        
        return {
            'line_crossed': len(new_crossings) > 0,
            'total_crossings': len(self.crossed_ids),
            'crossing_ids': new_crossings,
            'line_position': line_x_pos,
            'boxes': output_boxes
        }
    
    def reset(self):
        """Reset crossing counter"""
        self.crossed_ids.clear()
        self.object_positions.clear()
        self.crossing_history.clear()
