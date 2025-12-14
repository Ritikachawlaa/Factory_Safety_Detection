"""
Object Tracking and ID Persistence
Used for loitering detection and auto-tracking feature
"""
import numpy as np
from collections import defaultdict
import time

class ObjectTracker:
    """
    Simple object tracker using centroid tracking
    Tracks objects across frames and maintains IDs
    """
    
    def __init__(self, max_disappeared=30):
        """
        Args:
            max_disappeared: Max frames an object can disappear before being deregistered
        """
        self.next_object_id = 0
        self.objects = {}  # object_id: centroid
        self.disappeared = defaultdict(int)
        self.timestamps = {}  # object_id: first_seen_timestamp
        self.initial_positions = {}  # object_id: first centroid position
        self.max_disappeared = max_disappeared
    
    def register(self, centroid):
        """Register a new object"""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.timestamps[self.next_object_id] = time.time()
        self.initial_positions[self.next_object_id] = centroid
        self.next_object_id += 1
    
    def deregister(self, object_id):
        """Remove an object from tracking"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.timestamps:
            del self.timestamps[object_id]
        if object_id in self.initial_positions:
            del self.initial_positions[object_id]
    
    def update(self, detections):
        """
        Update tracked objects with new detections
        
        Args:
            detections: List of centroids [(x, y), ...]
            
        Returns:
            dict: {object_id: centroid}
        """
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects
        
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for centroid in detections:
                self.register(centroid)
        else:
            # Match existing objects to new detections
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())
            
            # Compute distance matrix
            distances = np.zeros((len(object_centroids), len(detections)))
            for i, obj_centroid in enumerate(object_centroids):
                for j, det_centroid in enumerate(detections):
                    distances[i, j] = np.linalg.norm(
                        np.array(obj_centroid) - np.array(det_centroid)
                    )
            
            # Match using nearest neighbor
            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]
            
            used_rows = set()
            used_cols = set()
            
            # Update matched objects
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                # Distance threshold for matching (50 pixels)
                if distances[row, col] > 50:
                    continue
                
                object_id = object_ids[row]
                self.objects[object_id] = detections[col]
                self.disappeared[object_id] = 0
                
                used_rows.add(row)
                used_cols.add(col)
            
            # Mark unmatched objects as disappeared
            unused_rows = set(range(len(object_centroids))) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            # Register new objects
            unused_cols = set(range(len(detections))) - used_cols
            for col in unused_cols:
                self.register(detections[col])
        
        return self.objects
    
    def get_object_duration(self, object_id):
        """Get how long an object has been tracked (in seconds)"""
        if object_id in self.timestamps:
            return time.time() - self.timestamps[object_id]
        return 0
    
    def get_object_movement(self, object_id):
        """Get total movement distance of object from initial position (in pixels)"""
        if object_id not in self.objects or object_id not in self.initial_positions:
            return 0
        
        current_pos = self.objects[object_id]
        initial_pos = self.initial_positions[object_id]
        
        movement = np.sqrt(
            (current_pos[0] - initial_pos[0])**2 + 
            (current_pos[1] - initial_pos[1])**2
        )
        return movement
