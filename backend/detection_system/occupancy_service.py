"""
Module 4: People Counting & Occupancy Analytics
Occupancy Tracking Service with Virtual Line Crossing Detection
Author: Factory Safety Detection Team
Date: 2025
"""

from datetime import datetime, timedelta, date
from typing import Dict, Optional, List, Tuple, Set
import logging
import math
from collections import defaultdict

from sqlalchemy.orm import Session

from .occupancy_models import (
    Camera, VirtualLine, OccupancyLog, HourlyOccupancy, DailyOccupancy, MonthlyOccupancy,
    OccupancyAlert, LineCrossingData, OccupancyState, LineDirection, OccupancyAlertType,
    CameraDAO, VirtualLineDAO, OccupancyLogDAO, HourlyOccupancyDAO, DailyOccupancyDAO,
    MonthlyOccupancyDAO, OccupancyAlertDAO
)

logger = logging.getLogger(__name__)


# ============================================================================
# Line Crossing Processor
# ============================================================================

class LineCrossingProcessor:
    """
    Detects when a person centroid crosses a virtual line
    Uses vector math to determine direction of crossing
    """

    @staticmethod
    def point_to_line_distance(point: Tuple[float, float], line_p1: Tuple[float, float], 
                               line_p2: Tuple[float, float]) -> float:
        """
        Calculate perpendicular distance from point to line
        Using formula: |ax + by + c| / sqrt(a^2 + b^2)
        """
        x, y = point
        x1, y1 = line_p1
        x2, y2 = line_p2

        numerator = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
        denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)

        if denominator == 0:
            return float('inf')
        
        return numerator / denominator

    @staticmethod
    def is_point_on_segment(point: Tuple[float, float], line_p1: Tuple[float, float], 
                           line_p2: Tuple[float, float], tolerance: float = 5.0) -> bool:
        """
        Check if point is on the line segment (with tolerance)
        By checking if point is between the two endpoints
        """
        x, y = point
        x1, y1 = line_p1
        x2, y2 = line_p2

        # Calculate distance from point to both endpoints
        dist_to_p1 = math.sqrt((x - x1)**2 + (y - y1)**2)
        dist_to_p2 = math.sqrt((x - x2)**2 + (y - y2)**2)
        line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Point is on segment if sum of distances equals line length (within tolerance)
        return abs(dist_to_p1 + dist_to_p2 - line_length) < tolerance

    @staticmethod
    def get_side_of_line(point: Tuple[float, float], line_p1: Tuple[float, float], 
                        line_p2: Tuple[float, float]) -> int:
        """
        Determine which side of the line the point is on
        Returns: 1 (left), -1 (right), 0 (on line)
        Uses cross product
        """
        x, y = point
        x1, y1 = line_p1
        x2, y2 = line_p2

        cross_product = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)

        if cross_product > 0:
            return 1  # Left
        elif cross_product < 0:
            return -1  # Right
        else:
            return 0  # On line

    @staticmethod
    def check_line_crossing(current_pos: Tuple[float, float], previous_pos: Tuple[float, float],
                           line: VirtualLine) -> Optional[str]:
        """
        Check if a person crossed the virtual line
        Returns: "entry" if crossed left-to-right, "exit" if right-to-left, None if no crossing
        
        The algorithm checks if the path from previous_pos to current_pos crosses the line segment
        """
        line_p1 = (line.x1, line.y1)
        line_p2 = (line.x2, line.y2)

        # Get sides before and after
        prev_side = LineCrossingProcessor.get_side_of_line(previous_pos, line_p1, line_p2)
        curr_side = LineCrossingProcessor.get_side_of_line(current_pos, line_p1, line_p2)

        # No crossing if on same side
        if prev_side == curr_side or prev_side == 0 or curr_side == 0:
            return None

        # Verify crossing by checking if trajectory intersects line segment
        if LineCrossingProcessor._trajectory_intersects_segment(previous_pos, current_pos, 
                                                               line_p1, line_p2):
            # Determine direction based on which side it came from
            # If came from left (1) to right (-1): entry
            # If came from right (-1) to left (1): exit
            if prev_side == 1 and curr_side == -1:
                return "entry"
            elif prev_side == -1 and curr_side == 1:
                return "exit"

        return None

    @staticmethod
    def _trajectory_intersects_segment(p1: Tuple[float, float], p2: Tuple[float, float],
                                      s1: Tuple[float, float], s2: Tuple[float, float]) -> bool:
        """
        Check if line segment p1-p2 intersects line segment s1-s2
        """
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        return ccw(p1, s1, s2) != ccw(p2, s1, s2) and ccw(p1, p2, s1) != ccw(p1, p2, s2)


# ============================================================================
# Direction Analyzer
# ============================================================================

class DirectionAnalyzer:
    """
    Analyzes direction of movement to classify as entry or exit
    Uses movement vector and line orientation
    """

    @staticmethod
    def get_movement_vector(prev_pos: Tuple[float, float], curr_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Get normalized movement vector"""
        dx = curr_pos[0] - prev_pos[0]
        dy = curr_pos[1] - prev_pos[1]
        magnitude = math.sqrt(dx**2 + dy**2)

        if magnitude == 0:
            return (0, 0)

        return (dx / magnitude, dy / magnitude)

    @staticmethod
    def dot_product(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        """Calculate dot product of two vectors"""
        return v1[0] * v2[0] + v1[1] * v2[1]

    @staticmethod
    def analyze_crossing_direction(movement_vector: Tuple[float, float],
                                   line: VirtualLine) -> Optional[str]:
        """
        Analyze crossing direction using line direction
        
        Args:
            movement_vector: Normalized movement direction
            line: Virtual line configuration
            
        Returns:
            "entry", "exit", or None based on dot product with line normal
        """
        line_vector = line.get_line_vector()
        perp_vector = line.get_perpendicular_vector()

        # Dot product with perpendicular vector tells us direction
        dot = DirectionAnalyzer.dot_product(movement_vector, perp_vector)

        # If dot > 0, movement is in direction of perpendicular (one direction)
        # If dot < 0, movement is opposite (other direction)
        if dot > 0.3:  # Threshold to require >30% alignment
            return "entry"
        elif dot < -0.3:
            return "exit"

        return None


# ============================================================================
# Occupancy Counter
# ============================================================================

class OccupancyCounter:
    """
    Maintains real-time occupancy count for a camera
    Handles entry/exit counting with error correction
    """

    def __init__(self, camera_id: int):
        """Initialize counter"""
        self.camera_id = camera_id
        self.current_occupancy = 0
        self.total_entries = 0
        self.total_exits = 0
        self.tracked_persons: Set[int] = set()  # Set of active track_ids
        self.last_updated = datetime.utcnow()
        self.entry_log: List[LineCrossingData] = []
        self.exit_log: List[LineCrossingData] = []

    def record_entry(self, crossing_data: LineCrossingData) -> None:
        """Record a person entry"""
        self.total_entries += 1
        self.current_occupancy += 1
        self.tracked_persons.add(crossing_data.track_id)
        self.entry_log.append(crossing_data)
        self.last_updated = datetime.utcnow()
        logger.debug(f"Camera {self.camera_id}: Entry recorded. Current occupancy: {self.current_occupancy}")

    def record_exit(self, crossing_data: LineCrossingData) -> None:
        """Record a person exit"""
        self.total_exits += 1
        self.current_occupancy = max(0, self.current_occupancy - 1)
        self.tracked_persons.discard(crossing_data.track_id)
        self.exit_log.append(crossing_data)
        self.last_updated = datetime.utcnow()
        logger.debug(f"Camera {self.camera_id}: Exit recorded. Current occupancy: {self.current_occupancy}")

    def manual_calibration(self, occupancy_value: int) -> None:
        """
        Manually set occupancy (for error correction/calibration)
        Used when manual headcount is performed
        """
        self.current_occupancy = max(0, occupancy_value)
        self.last_updated = datetime.utcnow()
        logger.info(f"Camera {self.camera_id}: Manual calibration to {occupancy_value}")

    def get_state(self) -> OccupancyState:
        """Get current counter state"""
        return OccupancyState(
            camera_id=self.camera_id,
            current_occupancy=self.current_occupancy,
            total_entries=self.total_entries,
            total_exits=self.total_exits,
            last_updated=self.last_updated,
            unique_persons=self.tracked_persons.copy()
        )

    def reset_logs(self) -> None:
        """Clear entry/exit logs after saving to database"""
        self.entry_log.clear()
        self.exit_log.clear()


# ============================================================================
# Multi-Camera Aggregator
# ============================================================================

class MultiCameraAggregator:
    """
    Consolidates occupancy data from multiple cameras
    Prevents double-counting across different camera views
    """

    def __init__(self):
        """Initialize aggregator"""
        self.camera_counters: Dict[int, OccupancyCounter] = {}
        self.facility_occupancy = 0
        self.last_updated = datetime.utcnow()

    def register_camera(self, camera_id: int) -> OccupancyCounter:
        """Register a camera for tracking"""
        counter = OccupancyCounter(camera_id)
        self.camera_counters[camera_id] = counter
        return counter

    def get_camera_counter(self, camera_id: int) -> Optional[OccupancyCounter]:
        """Get counter for camera"""
        return self.camera_counters.get(camera_id)

    def update_facility_occupancy(self) -> int:
        """
        Update facility-wide occupancy by summing all cameras
        For entry-only and exit-only cameras, combine intelligently
        """
        # Strategy: sum entries and exits from all cameras to get net occupancy
        total_entries = sum(c.total_entries for c in self.camera_counters.values())
        total_exits = sum(c.total_exits for c in self.camera_counters.values())
        self.facility_occupancy = max(0, total_entries - total_exits)
        self.last_updated = datetime.utcnow()
        return self.facility_occupancy

    def get_facility_occupancy(self) -> Dict:
        """Get facility-wide occupancy"""
        return {
            'facility_occupancy': self.facility_occupancy,
            'total_entries_all_cameras': sum(c.total_entries for c in self.camera_counters.values()),
            'total_exits_all_cameras': sum(c.total_exits for c in self.camera_counters.values()),
            'cameras_active': len([c for c in self.camera_counters.values() if c.current_occupancy >= 0]),
            'last_updated': self.last_updated.isoformat()
        }


# ============================================================================
# Time-Series Aggregation Service
# ============================================================================

class TimeSeriesAggregator:
    """
    Aggregates real-time occupancy logs into hourly/daily/monthly summaries
    Typically runs as a background task every hour
    """

    @staticmethod
    def aggregate_to_hourly(session: Session, camera_id: int, 
                           hour_date: date, hour_of_day: int) -> Optional[HourlyOccupancy]:
        """
        Aggregate logs for the past hour into HourlyOccupancy table
        
        Args:
            session: Database session
            camera_id: Camera database ID
            hour_date: Date of the hour
            hour_of_day: Hour (0-23)
        """
        try:
            # Define time range for the hour
            hour_start = datetime.combine(hour_date, __import__('datetime').time(hour_of_day, 0, 0))
            hour_end = hour_start + timedelta(hours=1) - timedelta(seconds=1)

            # Get logs for this hour
            logs = OccupancyLogDAO.get_time_range(session, camera_id, hour_start, hour_end)

            if not logs:
                logger.debug(f"No logs found for camera {camera_id} at {hour_date} {hour_of_day:02d}:00")
                return None

            # Aggregate
            total_entries = sum(log.entry_count for log in logs)
            total_exits = sum(log.exit_count for log in logs)
            occupancies = [log.net_occupancy for log in logs]
            confidences = [log.detection_confidence for log in logs]
            persons = sum(log.tracked_persons for log in logs)

            aggregated_data = {
                'total_entries': total_entries,
                'total_exits': total_exits,
                'avg_occupancy': sum(occupancies) / len(occupancies) if occupancies else 0,
                'peak_occupancy': max(occupancies) if occupancies else 0,
                'min_occupancy': min(occupancies) if occupancies else 0,
                'avg_detection_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'unique_persons_count': persons,
                'is_complete': True
            }

            hourly = HourlyOccupancyDAO.create_or_update(session, camera_id, hour_date, hour_of_day, aggregated_data)
            logger.info(f"Aggregated hourly occupancy: camera {camera_id}, {hour_date} {hour_of_day:02d}:00")
            return hourly

        except Exception as e:
            logger.error(f"Error aggregating to hourly: {str(e)}")
            return None

    @staticmethod
    def aggregate_to_daily(session: Session, camera_id: int, occupancy_date: date) -> Optional[DailyOccupancy]:
        """
        Aggregate hourly data into daily summary
        
        Args:
            session: Database session
            camera_id: Camera database ID
            occupancy_date: Date to aggregate
        """
        try:
            # Get all hourly records for the day
            hourly_records = HourlyOccupancyDAO.get_by_hour(session, camera_id, occupancy_date)

            if not hourly_records:
                logger.debug(f"No hourly records found for camera {camera_id} on {occupancy_date}")
                return None

            # Aggregate
            total_entries = sum(h.total_entries for h in hourly_records)
            total_exits = sum(h.total_exits for h in hourly_records)
            occupancies = [h.avg_occupancy for h in hourly_records]
            peaks = [h.peak_occupancy for h in hourly_records]
            peak_occupancy = max(peaks)
            peak_hour = hourly_records[peaks.index(peak_occupancy)].hour_of_day if peaks else None
            confidences = [h.avg_detection_confidence for h in hourly_records]

            # Determine if weekend/holiday (simplified)
            weekday = occupancy_date.weekday()
            is_weekend = weekday >= 5

            aggregated_data = {
                'total_entries': total_entries,
                'total_exits': total_exits,
                'avg_occupancy': sum(occupancies) / len(occupancies) if occupancies else 0,
                'peak_occupancy': peak_occupancy,
                'peak_hour': peak_hour,
                'min_occupancy': min(occupancies) if occupancies else 0,
                'avg_detection_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'is_weekend': is_weekend,
                'is_holiday': False  # Could be enhanced with holiday calendar
            }

            daily = DailyOccupancyDAO.create_or_update(session, camera_id, occupancy_date, aggregated_data)
            logger.info(f"Aggregated daily occupancy: camera {camera_id}, {occupancy_date}")
            return daily

        except Exception as e:
            logger.error(f"Error aggregating to daily: {str(e)}")
            return None

    @staticmethod
    def aggregate_to_monthly(session: Session, camera_id: int, year: int, month: int) -> Optional[MonthlyOccupancy]:
        """
        Aggregate daily data into monthly summary
        
        Args:
            session: Database session
            camera_id: Camera database ID
            year: Year
            month: Month (1-12)
        """
        try:
            # Get all daily records for the month
            daily_records = DailyOccupancyDAO.get_month(session, camera_id, year, month)

            if not daily_records:
                logger.debug(f"No daily records found for camera {camera_id} in {year}-{month:02d}")
                return None

            # Aggregate
            total_entries = sum(d.total_entries for d in daily_records)
            total_exits = sum(d.total_exits for d in daily_records)
            occupancies = [d.avg_occupancy for d in daily_records]
            peaks = [d.peak_occupancy for d in daily_records]
            peak_occupancy = max(peaks)
            peak_date = daily_records[peaks.index(peak_occupancy)].occupancy_date if peaks else None
            confidences = [d.avg_detection_confidence for d in daily_records]

            # Count day types
            working_days = sum(1 for d in daily_records if not d.is_weekend and not d.is_holiday)
            weekend_days = sum(1 for d in daily_records if d.is_weekend)
            holiday_days = sum(1 for d in daily_records if d.is_holiday)

            aggregated_data = {
                'total_entries': total_entries,
                'total_exits': total_exits,
                'avg_daily_occupancy': sum(occupancies) / len(occupancies) if occupancies else 0,
                'peak_day_occupancy': peak_occupancy,
                'peak_date': peak_date,
                'total_working_days': working_days,
                'total_weekend_days': weekend_days,
                'total_holiday_days': holiday_days,
                'avg_detection_confidence': sum(confidences) / len(confidences) if confidences else 0
            }

            monthly = MonthlyOccupancyDAO.create_or_update(session, camera_id, year, month, aggregated_data)
            logger.info(f"Aggregated monthly occupancy: camera {camera_id}, {year}-{month:02d}")
            return monthly

        except Exception as e:
            logger.error(f"Error aggregating to monthly: {str(e)}")
            return None

    @staticmethod
    def run_hourly_aggregation(session: Session) -> None:
        """
        Run hourly aggregation for all cameras
        Should be scheduled as a background task
        """
        try:
            logger.info("Starting hourly aggregation task")
            
            # Get all active cameras
            cameras = session.query(Camera).filter(Camera.is_active == True).all()
            
            # Aggregate the previous hour for each camera
            now = datetime.utcnow()
            prev_hour = now - timedelta(hours=1)
            hour_date = prev_hour.date()
            hour_of_day = prev_hour.hour

            for camera in cameras:
                TimeSeriesAggregator.aggregate_to_hourly(session, camera.id, hour_date, hour_of_day)

            logger.info("Hourly aggregation completed")

        except Exception as e:
            logger.error(f"Error in hourly aggregation: {str(e)}")

    @staticmethod
    def run_daily_aggregation(session: Session) -> None:
        """
        Run daily aggregation for all cameras
        Should be scheduled as a background task at midnight
        """
        try:
            logger.info("Starting daily aggregation task")
            
            # Get all active cameras
            cameras = session.query(Camera).filter(Camera.is_active == True).all()
            
            # Aggregate the previous day for each camera
            yesterday = datetime.utcnow().date() - timedelta(days=1)

            for camera in cameras:
                TimeSeriesAggregator.aggregate_to_daily(session, camera.id, yesterday)

            logger.info("Daily aggregation completed")

        except Exception as e:
            logger.error(f"Error in daily aggregation: {str(e)}")

    @staticmethod
    def run_monthly_aggregation(session: Session) -> None:
        """
        Run monthly aggregation for all cameras
        Should be scheduled as a background task on the first of each month
        """
        try:
            logger.info("Starting monthly aggregation task")
            
            # Get all active cameras
            cameras = session.query(Camera).filter(Camera.is_active == True).all()
            
            # Aggregate the previous month for each camera
            now = datetime.utcnow()
            if now.month == 1:
                prev_month_year = now.year - 1
                prev_month = 12
            else:
                prev_month_year = now.year
                prev_month = now.month - 1

            for camera in cameras:
                TimeSeriesAggregator.aggregate_to_monthly(session, camera.id, prev_month_year, prev_month)

            logger.info("Monthly aggregation completed")

        except Exception as e:
            logger.error(f"Error in monthly aggregation: {str(e)}")


# ============================================================================
# Main Occupancy Service
# ============================================================================

class OccupancyService:
    """
    Main service orchestrating occupancy tracking
    Integrates line crossing detection, counting, and aggregation
    """

    def __init__(self, session: Session):
        """Initialize service"""
        self.session = session
        self.aggregator = MultiCameraAggregator()
        self.line_processor = LineCrossingProcessor()
        self.direction_analyzer = DirectionAnalyzer()
        self.timeseries_aggregator = TimeSeriesAggregator()
        
        # Initialize counters for all active cameras
        self._initialize_cameras()

    def _initialize_cameras(self) -> None:
        """Initialize occupancy counters for all active cameras"""
        try:
            cameras = CameraDAO.get_all_active(self.session)
            for camera in cameras:
                self.aggregator.register_camera(camera.id)
            logger.info(f"Initialized occupancy service for {len(cameras)} cameras")
        except Exception as e:
            logger.error(f"Error initializing cameras: {str(e)}")

    def process_frame(self, camera_id: int, detections: List[Dict]) -> None:
        """
        Process frame detections for occupancy
        
        Args:
            camera_id: Camera database ID
            detections: List of person detections with format:
                {
                    'track_id': int,
                    'confidence': float,
                    'centroid': (x, y),
                    'prev_centroid': (x, y)  # Optional
                }
        """
        try:
            counter = self.aggregator.get_camera_counter(camera_id)
            if not counter:
                logger.warning(f"No counter found for camera {camera_id}")
                return

            # Get active lines for this camera
            camera_obj = CameraDAO.get_by_id(self.session, camera_id)
            if not camera_obj:
                return

            lines = VirtualLineDAO.get_by_camera(self.session, camera_id)
            if not lines:
                logger.debug(f"No active lines configured for camera {camera_id}")
                return

            # Process each detection
            for detection in detections:
                track_id = detection.get('track_id')
                confidence = detection.get('confidence', 0.0)
                centroid = detection.get('centroid')
                prev_centroid = detection.get('prev_centroid')

                if not centroid or not prev_centroid:
                    continue

                # Check each virtual line
                for line in lines:
                    crossing_direction = self.line_processor.check_line_crossing(
                        centroid, prev_centroid, line
                    )

                    if crossing_direction:
                        # Create crossing event
                        crossing_event = LineCrossingData(
                            track_id=track_id,
                            timestamp=datetime.utcnow(),
                            direction=crossing_direction,
                            confidence=confidence,
                            centroid_position=centroid,
                            line_id=line.id
                        )

                        # Record based on line configuration
                        if line.direction.value == LineDirection.ENTRY.value:
                            counter.record_entry(crossing_event)
                        elif line.direction.value == LineDirection.EXIT.value:
                            counter.record_exit(crossing_event)
                        elif line.direction.value == LineDirection.BIDIRECTIONAL.value:
                            if crossing_direction == "entry":
                                counter.record_entry(crossing_event)
                            else:
                                counter.record_exit(crossing_event)

                        logger.debug(f"Line crossing detected: camera {camera_id}, "
                                   f"track {track_id}, direction {crossing_direction}")

        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")

    def save_occupancy_log(self, camera_id: int, period_seconds: int = 60) -> Optional[OccupancyLog]:
        """
        Save current occupancy to database
        Should be called periodically (every minute)
        
        Args:
            camera_id: Camera database ID
            period_seconds: Duration this log covers
        """
        try:
            counter = self.aggregator.get_camera_counter(camera_id)
            if not counter:
                return None

            log_data = {
                'camera_id': camera_id,
                'entry_count': len(counter.entry_log),
                'exit_count': len(counter.exit_log),
                'net_occupancy': counter.current_occupancy,
                'period_duration_seconds': period_seconds,
                'detection_confidence': sum(e.confidence for e in counter.entry_log + counter.exit_log) / 
                                        (len(counter.entry_log) + len(counter.exit_log))
                                        if (counter.entry_log or counter.exit_log) else 0.0,
                'tracked_persons': len(counter.tracked_persons)
            }

            log = OccupancyLogDAO.create(self.session, log_data)
            counter.reset_logs()
            return log

        except Exception as e:
            logger.error(f"Error saving log: {str(e)}")
            return None

    def manual_calibration(self, camera_id: int, occupancy_value: int) -> None:
        """
        Manually set occupancy (for correction after manual headcount)
        
        Args:
            camera_id: Camera database ID
            occupancy_value: Manual count
        """
        try:
            counter = self.aggregator.get_camera_counter(camera_id)
            if counter:
                counter.manual_calibration(occupancy_value)
                
                # Log calibration
                log_data = {
                    'camera_id': camera_id,
                    'entry_count': 0,
                    'exit_count': 0,
                    'net_occupancy': occupancy_value,
                    'is_manual_calibration': True
                }
                OccupancyLogDAO.create(self.session, log_data)
                logger.info(f"Manual calibration applied: camera {camera_id} = {occupancy_value}")

        except Exception as e:
            logger.error(f"Error in manual calibration: {str(e)}")

    def check_capacity_alert(self, camera_id: int) -> Optional[OccupancyAlert]:
        """
        Check if camera occupancy exceeds capacity
        Create alert if needed
        """
        try:
            camera = CameraDAO.get_by_id(self.session, camera_id)
            counter = self.aggregator.get_camera_counter(camera_id)

            if not camera or not counter or not camera.max_occupancy:
                return None

            # Check for capacity exceeded
            if counter.current_occupancy > camera.max_occupancy:
                # Check if alert already exists
                active_alerts = OccupancyAlertDAO.get_active_alerts(self.session, camera_id)
                capacity_alert_exists = any(
                    a.alert_type == OccupancyAlertType.CAPACITY_EXCEEDED for a in active_alerts
                )

                if not capacity_alert_exists:
                    alert_data = {
                        'camera_id': camera_id,
                        'alert_type': OccupancyAlertType.CAPACITY_EXCEEDED,
                        'current_occupancy': counter.current_occupancy,
                        'threshold_value': camera.max_occupancy,
                        'message': f"Occupancy ({counter.current_occupancy}) exceeds capacity ({camera.max_occupancy})"
                    }
                    alert = OccupancyAlertDAO.create(self.session, alert_data)
                    return alert

        except Exception as e:
            logger.error(f"Error checking capacity: {str(e)}")

        return None

    def get_occupancy_state(self, camera_id: int) -> Optional[Dict]:
        """Get current occupancy state for a camera"""
        try:
            counter = self.aggregator.get_camera_counter(camera_id)
            if counter:
                return counter.get_state().to_dict()
        except Exception as e:
            logger.error(f"Error getting occupancy state: {str(e)}")

        return None

    def get_facility_state(self) -> Dict:
        """Get facility-wide occupancy state"""
        self.aggregator.update_facility_occupancy()
        return self.aggregator.get_facility_occupancy()
