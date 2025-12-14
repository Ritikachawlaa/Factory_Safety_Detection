"""
Loitering Detection Service
Detects people staying in one area for too long (single OR groups)
"""
import numpy as np
from models.tracker import ObjectTracker
import time

class LoiteringDetector:
    """Detect loitering for single person OR groups"""
    
    def __init__(self, time_threshold=5, movement_threshold=25, group_distance=60):
        """
        Args:
            time_threshold: Seconds before flagging as loitering (demo-friendly: 5s)
            movement_threshold: Pixels - max movement allowed without timer reset (25-30px recommended)
            group_distance: Pixels - max distance between people to form a group (60px for webcam)
        """
        # Configuration
        self.TIME_THRESHOLD = time_threshold
        self.MOVEMENT_THRESHOLD = movement_threshold
        self.GROUP_DISTANCE = group_distance
        
        # Object tracker
        self.tracker = ObjectTracker(max_disappeared=30)
        
        # Per-track loitering state
        self.track_states = {}  # track_id: {'start_time': float, 'last_position': (x,y), 'loitering_time': float, 'is_loitering': bool}
        
        # Group tracking
        self.group_states = {}  # frozenset(track_ids): {'start_time': float, 'is_loitering': bool}
        
    def detect(self, people_boxes):
        """
        Detect loitering from people detections with proper tracking-based state management
        
        Loitering triggers when:
          1) A SINGLE person stays in nearly same position for > TIME_THRESHOLD seconds
          2) TWO OR MORE people stay together for > TIME_THRESHOLD seconds
        
        Args:
            people_boxes: List of people bounding boxes with format [{'x1', 'y1', 'x2', 'y2'}, ...]
            
        Returns:
            {
                'loitering_detected': bool,
                'loitering_count': int,
                'groups': int,
                'loitering_ids': list (optional)
            }
        """
        current_time = time.time()
        
        # Handle empty detections
        if not people_boxes:
            self.tracker.update([])
            self._cleanup_missing_tracks([])
            return self._empty_result()
        
        # Extract centroids from bounding boxes
        centroids = []
        for box in people_boxes:
            center_x = (box['x1'] + box['x2']) // 2
            center_y = (box['y1'] + box['y2']) // 2
            centroids.append((center_x, center_y))
        
        # Update tracker and get current tracked objects
        tracked_objects = self.tracker.update(centroids)
        
        # Clean up tracks that disappeared
        self._cleanup_missing_tracks(list(tracked_objects.keys()))
        
        # Update per-track loitering states
        loitering_tracks = set()
        
        for track_id, position in tracked_objects.items():
            # Initialize track state if new
            if track_id not in self.track_states:
                self.track_states[track_id] = {
                    'start_time': current_time,
                    'last_position': position,
                    'loitering_time': 0.0,
                    'is_loitering': False
                }
                print(f"[LOITERING] New track {track_id} registered at {position}")
                continue
            
            # Get track state
            state = self.track_states[track_id]
            last_pos = state['last_position']
            
            # Calculate movement from last known position
            movement_distance = np.sqrt(
                (position[0] - last_pos[0])**2 + 
                (position[1] - last_pos[1])**2
            )
            
            # Check if movement is within tolerance
            if movement_distance <= self.MOVEMENT_THRESHOLD:
                # Person hasn't moved much - accumulate loitering time
                state['loitering_time'] = current_time - state['start_time']
                
                # Check if crossed threshold
                if state['loitering_time'] >= self.TIME_THRESHOLD:
                    if not state['is_loitering']:
                        print(f"[LOITERING] ⚠️ Track {track_id} started loitering (time: {state['loitering_time']:.1f}s)")
                    state['is_loitering'] = True
                    loitering_tracks.add(track_id)
            else:
                # Person moved significantly - reset timer
                if state['is_loitering']:
                    print(f"[LOITERING] ✅ Track {track_id} stopped loitering (moved {movement_distance:.1f}px)")
                
                state['start_time'] = current_time
                state['loitering_time'] = 0.0
                state['is_loitering'] = False
            
            # Update last position
            state['last_position'] = position
        
        # Detect groups (people standing close together)
        groups = self._detect_groups_from_tracks(tracked_objects)
        group_loitering_tracks = self._check_group_loitering(tracked_objects, current_time)
        
        # Combine individual and group loitering
        all_loitering_tracks = loitering_tracks.union(group_loitering_tracks)
        
        loitering_detected = len(all_loitering_tracks) > 0
        loitering_count = len(all_loitering_tracks)
        
        # Debug output
        if loitering_detected:
            print(f"[LOITERING] 🚨 DETECTED: {loitering_count} person(s) loitering (IDs: {list(all_loitering_tracks)})")
        
        return {
            'loitering_detected': loitering_detected,
            'loitering_count': loitering_count,
            'total_people': len(people_boxes),
            'groups': len(groups),
            'loitering_ids': list(all_loitering_tracks)
        }
    
    def _detect_groups_from_tracks(self, tracked_objects):
        """
        Detect groups of people based on proximity
        Returns list of groups, where each group is a set of track IDs
        """
        if len(tracked_objects) < 2:
            return []
        
        track_ids = list(tracked_objects.keys())
        positions = list(tracked_objects.values())
        
        # Build adjacency: which tracks are close to each other
        groups = []
        visited = set()
        
        for i, track_id1 in enumerate(track_ids):
            if track_id1 in visited:
                continue
            
            # Start new group
            current_group = {track_id1}
            visited.add(track_id1)
            
            # Find all tracks within GROUP_DISTANCE
            for j, track_id2 in enumerate(track_ids):
                if track_id2 in visited:
                    continue
                
                pos1 = positions[i]
                pos2 = positions[j]
                distance = np.sqrt(
                    (pos1[0] - pos2[0])**2 + 
                    (pos1[1] - pos2[1])**2
                )
                
                if distance <= self.GROUP_DISTANCE:
                    current_group.add(track_id2)
                    visited.add(track_id2)
            
            # Only add groups with 2+ people
            if len(current_group) >= 2:
                groups.append(current_group)
        
        return groups
    
    def _check_group_loitering(self, tracked_objects, current_time):
        """
        Check if any groups have been together for > TIME_THRESHOLD
        Returns set of track IDs that are part of loitering groups
        """
        if len(tracked_objects) < 2:
            return set()
        
        groups = self._detect_groups_from_tracks(tracked_objects)
        loitering_group_members = set()
        
        for group in groups:
            group_key = frozenset(group)
            
            # Initialize group state if new
            if group_key not in self.group_states:
                self.group_states[group_key] = {
                    'start_time': current_time,
                    'is_loitering': False
                }
                print(f"[LOITERING] New group detected: {list(group)}")
                continue
            
            # Check group duration
            group_state = self.group_states[group_key]
            group_duration = current_time - group_state['start_time']
            
            if group_duration >= self.TIME_THRESHOLD:
                if not group_state['is_loitering']:
                    print(f"[LOITERING] ⚠️ Group {list(group)} started loitering (time: {group_duration:.1f}s)")
                group_state['is_loitering'] = True
                loitering_group_members.update(group)
        
        # Clean up old groups that no longer exist
        current_groups = {frozenset(g) for g in groups}
        old_groups = set(self.group_states.keys()) - current_groups
        for old_group in old_groups:
            if self.group_states[old_group]['is_loitering']:
                print(f"[LOITERING] ✅ Group {list(old_group)} dispersed")
            del self.group_states[old_group]
        
        return loitering_group_members
    
    def _cleanup_missing_tracks(self, active_track_ids):
        """Remove track states for tracks that no longer exist"""
        active_set = set(active_track_ids)
        missing_tracks = set(self.track_states.keys()) - active_set
        
        for track_id in missing_tracks:
            if self.track_states[track_id]['is_loitering']:
                print(f"[LOITERING] ✅ Track {track_id} left frame (was loitering)")
            del self.track_states[track_id]
    
    def _empty_result(self):
        return {
            'loitering_detected': False,
            'loitering_count': 0,
            'total_people': 0,
            'groups': 0
        }
