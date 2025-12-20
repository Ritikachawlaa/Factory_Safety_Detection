```
Module 4: People Counting & Occupancy Analytics
Implementation Guide and Technical Reference
Factory Safety Detection AI SaaS Platform
Author: Development Team
Date: 2025

═══════════════════════════════════════════════════════════════════════════════
│ TABLE OF CONTENTS
═══════════════════════════════════════════════════════════════════════════════

1. Module Overview and Architecture
2. Core Components and Responsibilities
3. Line Crossing Detection Algorithm
4. Database Schema and Models
5. Service Layer Implementation
6. API Endpoints Reference
7. Integration Guide
8. Performance Considerations
9. Error Handling and Recovery
10. Testing Strategies


═══════════════════════════════════════════════════════════════════════════════
│ 1. MODULE OVERVIEW AND ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
────────
Module 4 provides real-time people counting and occupancy analytics for factory
environments. It tracks people entering and exiting designated areas through
virtual line crossing detection, maintains occupancy state, and aggregates data
into hourly/daily/monthly summaries for analytics and compliance reporting.

KEY CAPABILITIES
────────────────
✓ Real-time occupancy tracking via virtual line crossing
✓ Directional movement detection (entry vs. exit)
✓ Multi-camera support with facility-wide consolidation
✓ Time-series data aggregation (hourly, daily, monthly)
✓ Capacity alerts and anomaly detection
✓ Historical data APIs for analytics and reporting
✓ Manual calibration for error correction
✓ Live dashboard updates via WebSocket (future)

SYSTEM ARCHITECTURE
───────────────────

┌─────────────────────────────────────────────────────────┐
│          YOLO Person Detection + ByteTrack              │
│       (Generates detections with track_ids)              │
└────────────────────┬────────────────────────────────────┘
                     │ Detection frame data
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Occupancy Service Layer                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Line Crossing Processor                              ││
│  │ - Detects person centroid crossing virtual lines    ││
│  │ - Uses vector math for direction determination       ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │ Occupancy Counter                                    ││
│  │ - Maintains real-time occupancy state               ││
│  │ - Tracks entries/exits                               ││
│  │ - Handles error correction                           ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │ Multi-Camera Aggregator                              ││
│  │ - Consolidates occupancy from multiple cameras       ││
│  │ - Calculates facility-wide occupancy                 ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────────────┘
                     │ Processed occupancy events
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Database Models (SQLAlchemy)                    │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Real-time Tables                                    ││
│  │ - OccupancyLog (1-5 minute periods)                 ││
│  │ - Camera, VirtualLine configurations                ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │ Time-Series Tables (Background Aggregation)         ││
│  │ - HourlyOccupancy (from OccupancyLog)               ││
│  │ - DailyOccupancy (from HourlyOccupancy)             ││
│  │ - MonthlyOccupancy (from DailyOccupancy)            ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │ Alert Table                                          ││
│  │ - OccupancyAlert (capacity exceeded, anomalies)     ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────────────┘
                     │ Structured historical data
                     ▼
┌─────────────────────────────────────────────────────────┐
│          FastAPI Endpoints                               │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Real-time API                                        ││
│  │ /api/occupancy/cameras/{id}/live                    ││
│  │ /api/occupancy/facility/live                        ││
│  │ /api/occupancy/alerts                                ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │ Historical Data APIs                                 ││
│  │ /api/occupancy/cameras/{id}/hourly                  ││
│  │ /api/occupancy/cameras/{id}/daily                   ││
│  │ /api/occupancy/cameras/{id}/monthly                 ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────────────┘
                     │ JSON REST responses
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Frontend / Dashboard / External Systems         │
└─────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
│ 2. CORE COMPONENTS AND RESPONSIBILITIES
═══════════════════════════════════════════════════════════════════════════════

COMPONENT: LineCrossingProcessor
─────────────────────────────────
Purpose: Detects when a person centroid crosses a virtual line
Location: occupancy_service.py

Key Methods:
├── check_line_crossing()
│   └─ Main method that detects line crossings
│   └─ Takes current & previous centroid positions + line definition
│   └─ Returns: "entry", "exit", or None
│
├── get_side_of_line()
│   └─ Determines which side of a line a point is on
│   └─ Uses cross product for side determination
│   └─ Returns: 1 (left), -1 (right), 0 (on line)
│
├── point_to_line_distance()
│   └─ Calculates perpendicular distance from point to line
│   └─ Used for tolerance-based inclusion
│
└── is_point_on_segment()
    └─ Checks if point is on the line segment
    └─ Verifies point is between the two endpoints

Algorithm Details:
  1. Detect previous and current position sides of the line
  2. If points are on opposite sides, trajectory crossed
  3. Verify crossing by checking trajectory-segment intersection
  4. Determine direction based on movement direction


COMPONENT: DirectionAnalyzer
────────────────────────────
Purpose: Analyzes movement direction for entry/exit classification
Location: occupancy_service.py

Key Methods:
├── get_movement_vector()
│   └─ Calculate normalized movement vector
│   └─ Vector = (current_pos - previous_pos) / magnitude
│
├── dot_product()
│   └─ Compute dot product of two vectors
│   └─ Used for alignment measurement
│
└── analyze_crossing_direction()
    └─ Determine if crossing is entry or exit
    └─ Uses dot product with line perpendicular
    └─ Threshold-based (±0.3 for ±30% alignment)

Direction Logic:
  • dot > 0.3  → Entry (moving in positive direction)
  • dot < -0.3 → Exit (moving in negative direction)
  • |dot| ≤ 0.3 → Ambiguous (ignored)


COMPONENT: OccupancyCounter
──────────────────────────
Purpose: Maintains real-time occupancy count for a single camera
Location: occupancy_service.py

State Variables:
├── current_occupancy: int
│   └─ Current number of people in the area (entries - exits)
│   └─ Never goes below 0 (error correction)
│
├── total_entries: int
│   └─ Cumulative count of all entries since startup
│
├── total_exits: int
│   └─ Cumulative count of all exits since startup
│
├── tracked_persons: Set[int]
│   └─ Set of track_ids currently in the area
│   └─ Used for unique person counting
│
└── entry_log, exit_log: List[LineCrossingData]
    └─ Temporary storage of crossing events
    └─ Cleared after periodic save to database

Key Methods:
├── record_entry()    → Increment counters
├── record_exit()     → Decrement counters (floor at 0)
├── manual_calibration() → Set occupancy to specific value
└── get_state()       → Return current state snapshot


COMPONENT: MultiCameraAggregator
────────────────────────────────
Purpose: Consolidates occupancy from multiple cameras
Location: occupancy_service.py

Maintains:
├── camera_counters: Dict[camera_id → OccupancyCounter]
│   └─ One counter per registered camera
│
├── facility_occupancy: int
│   └─ Facility-wide current occupancy
│   └─ Sum of all entries - exits across all cameras
│
└── last_updated: datetime
    └─ Last time facility occupancy was updated

Strategy for Multi-Camera:
  • For separate entry-only and exit-only cameras:
    - Entry camera increases occupancy
    - Exit camera decreases occupancy
    - Facility occupancy = sum(all entries) - sum(all exits)
  
  • For overlapping cameras:
    - Manual assignment of which cameras to include
    - Prevent double-counting in same area
    - Use camera location metadata


COMPONENT: TimeSeriesAggregator
───────────────────────────────
Purpose: Aggregates real-time data into time-series tables
Location: occupancy_service.py

Aggregation Pipeline:
  Raw Detections (frames)
        ↓
  OccupancyLog (1-5 minute periods)
        ↓ [Hourly aggregation task]
  HourlyOccupancy (1 hour)
        ↓ [Daily aggregation task]
  DailyOccupancy (24 hours)
        ↓ [Monthly aggregation task]
  MonthlyOccupancy (30-31 days)

Aggregation Functions:
├── aggregate_to_hourly()   → Sum logs for 1 hour
├── aggregate_to_daily()    → Consolidate hourly into daily
├── aggregate_to_monthly()  → Consolidate daily into monthly
├── run_hourly_aggregation()   → Scheduled task for all cameras
├── run_daily_aggregation()    → Scheduled task at midnight
└── run_monthly_aggregation()  → Scheduled task on 1st of month

Scheduled Execution (via APScheduler or Celery):
  • Hourly: Every hour at :00 → aggregate previous hour
  • Daily: Every day at midnight → aggregate previous day
  • Monthly: First of month at 00:00 → aggregate previous month


COMPONENT: OccupancyService (Main Orchestrator)
───────────────────────────────────────────────
Purpose: Coordinates all occupancy tracking components
Location: occupancy_service.py

Initializes:
├── MultiCameraAggregator instance
├── LineCrossingProcessor instance
├── DirectionAnalyzer instance
├── TimeSeriesAggregator instance
└── Occupancy counters for all active cameras

Core Methods:
├── process_frame(camera_id, detections)
│   └─ Called for each frame from detection pipeline
│   └─ Runs line crossing detection for all configured lines
│   └─ Updates occupancy counters
│
├── save_occupancy_log(camera_id, period_seconds)
│   └─ Periodic save to OccupancyLog table
│   └─ Typically called every 1-5 minutes
│
├── manual_calibration(camera_id, occupancy_value)
│   └─ Manual correction after headcount
│
├── check_capacity_alert(camera_id)
│   └─ Check if occupancy exceeds max_capacity
│   └─ Create alert if needed
│
├── get_occupancy_state(camera_id)
│   └─ Return current state for single camera
│
└── get_facility_state()
    └─ Return current facility-wide occupancy


═══════════════════════════════════════════════════════════════════════════════
│ 3. LINE CROSSING DETECTION ALGORITHM
═══════════════════════════════════════════════════════════════════════════════

MATHEMATICAL FOUNDATION
───────────────────────

Virtual Line Definition:
  Line L is defined by two points: P1 = (x1, y1), P2 = (x2, y2)
  These are in pixel coordinates from the camera frame

Person Trajectory:
  For each frame, person centroid moves: Prev = (px, py) → Curr = (cx, cy)
  We need to detect if this path crosses the line L

ALGORITHM: Side-Based Line Crossing
────────────────────────────────────

Step 1: Determine Which Side of the Line Each Point Is On
  Using Cross Product:
    side = (x2 - x1) × (y - y1) - (y2 - y1) × (x - x1)
    
    if side > 0: point is on left side
    if side < 0: point is on right side
    if side = 0: point is on the line

Step 2: Check for Side Change
  prev_side = get_side(Prev, P1, P2)
  curr_side = get_side(Curr, P1, P2)
  
  if prev_side == curr_side: no crossing
  if either side is 0: on the line (edge case, typically ignore)

Step 3: Verify Trajectory Intersection
  To avoid false positives, verify the actual trajectory segment
  intersects the line segment (not just the infinite line):
  
  Using parametric form:
    Point on trajectory: T(t) = Prev + t × (Curr - Prev), t ∈ [0, 1]
    Point on line: L(s) = P1 + s × (P2 - P1), s ∈ [0, 1]
    
    Find intersection and verify both t, s ∈ [0, 1]

Step 4: Determine Direction
  If prev_side = 1 (left) and curr_side = -1 (right):
    → Crossed from left to right → Entry
  If prev_side = -1 (right) and curr_side = 1 (left):
    → Crossed from right to left → Exit

PSEUDOCODE
──────────

function check_line_crossing(curr_pos, prev_pos, line):
    p1 = (line.x1, line.y1)
    p2 = (line.x2, line.y2)
    
    prev_side = get_side_of_line(prev_pos, p1, p2)
    curr_side = get_side_of_line(curr_pos, p1, p2)
    
    // No crossing if same side
    if prev_side == curr_side or prev_side == 0 or curr_side == 0:
        return None
    
    // Verify trajectory intersects segment
    if not trajectory_intersects_segment(prev_pos, curr_pos, p1, p2):
        return None
    
    // Determine direction
    if prev_side == 1 and curr_side == -1:
        return "entry"
    else if prev_side == -1 and curr_side == 1:
        return "exit"
    else:
        return None

function get_side_of_line(point, p1, p2):
    x, y = point
    x1, y1 = p1
    x2, y2 = p2
    
    cross_product = (x2 - x1) × (y - y1) - (y2 - y1) × (x - x1)
    
    if cross_product > 0:
        return 1      // Left
    else if cross_product < 0:
        return -1     // Right
    else:
        return 0      // On line


VISUAL EXAMPLE
──────────────

Frame 1: Person on left side of line
                  Line P1 --- P2
                  |
        Person ◯  |
    
Frame 2: Person on right side of line
                  Line P1 --- P2
                  |
                  |  ◯ Person
    
Result: Crossing detected, direction = Entry (left to right)

Multiple People Example:
  Time T-1          Time T          Action
  ─────────────────────────────────────────
  Person A: ◯       Person A: ◯ │   Crossed line (entry)
             left     right
  
  Person B:    ◯    Person B: ◯ │   No crossing yet
             left      left
  
  Person C: ◯        Person C:     ╳ Left frame (exit)
             right               right
    │ Line crossing               │ Line crossing


═══════════════════════════════════════════════════════════════════════════════
│ 4. DATABASE SCHEMA AND MODELS
═══════════════════════════════════════════════════════════════════════════════

TABLE: cameras_occupancy
────────────────────────
Stores camera configurations for occupancy tracking

Columns:
├── id (Integer, PK)
├── camera_id (String, UNIQUE) — Human-readable ID (e.g., "GATE_A")
├── camera_name (String) — Display name
├── location (String) — Physical location
├── camera_type (String) — "entry_only", "exit_only", "bidirectional"
├── resolution_width, resolution_height (Integer) — Frame dimensions
├── is_active (Boolean, Indexed) — Enable/disable tracking
├── max_occupancy (Integer) — Capacity limit (optional)
├── description (Text)
├── created_at (DateTime)
└── updated_at (DateTime)

Indexes:
├── PK: id
├── UNIQUE: camera_id
├── idx_camera_active: (is_active)

Example:
  ID | camera_id  | location    | max_occupancy | is_active
  ─────────────────────────────────────────────────────────
  1  | GATE_A     | Gate A      | 100           | true
  2  | FLOOR_1_IN | Floor 1     | 200           | true
  3  | FLOOR_1_EX | Floor 1     | NULL          | true


TABLE: virtual_lines
────────────────────
Stores virtual line configurations for crossing detection

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK → cameras_occupancy) — Parent camera
├── line_name (String) — Name (e.g., "Entrance A")
├── x1, y1, x2, y2 (Integer) — Line endpoints in pixels
├── direction (Enum) — "entry", "exit", "bidirectional"
├── positive_direction (String) — Hint for direction (e.g., "top_to_bottom")
├── is_active (Boolean, Indexed)
├── line_color (String) — Hex color for visualization
├── thickness (Integer) — Thickness for visualization
├── confidence_threshold (Float) — Min confidence (0-1)
├── description (Text)
├── created_at (DateTime)
└── updated_at (DateTime)

Indexes:
├── PK: id
├── idx_line_camera_active: (camera_id, is_active)

Example:
  ID | camera_id | line_name     | x1 | y1 | x2  | y2  | direction
  ──────────────────────────────────────────────────────────────────
  1  | 1         | Entrance Line | 0  | 50 | 640 | 50  | entry
  2  | 1         | Exit Line     | 0  | 400| 640 | 400 | exit


TABLE: occupancy_logs
─────────────────────
Real-time occupancy counts (one entry per period, typically 1-5 minutes)
This is the raw data that gets aggregated into hourly/daily/monthly

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK) — Source camera
├── entry_count (Integer) — Entries in this period
├── exit_count (Integer) — Exits in this period
├── net_occupancy (Integer) — Current occupancy (entries - exits)
├── log_timestamp (DateTime, Indexed) — When this period ended
├── period_duration_seconds (Integer) — Duration of this log
├── detection_confidence (Float) — Avg confidence of detections
├── tracked_persons (Integer) — Unique people tracked
├── is_manual_calibration (Boolean) — Manual override?
├── notes (Text)
└── created_at (DateTime)

Indexes:
├── PK: id
├── idx_occupancy_camera_timestamp: (camera_id, log_timestamp)
├── idx_occupancy_timestamp: (log_timestamp)

Retention:
├── Keep for ~30 days
├── Older logs can be archived/deleted
├── Aggregated data retained permanently

Example:
  timestamp         | camera_id | entry_count | exit_count | net_occupancy
  ────────────────────────────────────────────────────────────────────────
  2025-01-15 10:00 | 1         | 5           | 2          | 45
  2025-01-15 10:05 | 1         | 3           | 4          | 44
  2025-01-15 10:10 | 1         | 2           | 1          | 45


TABLE: hourly_occupancy
───────────────────────
Hourly aggregated occupancy (summarized from occupancy_logs)

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK)
├── hour_date (Date) — Which day
├── hour_of_day (Integer) — 0-23
├── total_entries (Integer) — Sum of entries in hour
├── total_exits (Integer) — Sum of exits in hour
├── avg_occupancy (Float) — Average occupancy during hour
├── peak_occupancy (Integer) — Max occupancy in hour
├── min_occupancy (Integer) — Min occupancy in hour
├── avg_detection_confidence (Float)
├── unique_persons_count (Integer)
├── is_complete (Boolean) — Data complete?
├── created_at (DateTime)
└── updated_at (DateTime)

Unique Constraint:
└── (camera_id, hour_date, hour_of_day) UNIQUE

Indexes:
├── idx_hourly_camera_hour: (camera_id, hour_date, hour_of_day)
├── idx_hourly_date: (hour_date)

Example:
  date       | hour | total_entries | total_exits | avg_occupancy | peak
  ────────────────────────────────────────────────────────────────────────
  2025-01-15 | 10   | 15            | 8           | 47.5          | 52
  2025-01-15 | 11   | 12            | 14          | 45.8          | 50


TABLE: daily_occupancy
──────────────────────
Daily aggregated occupancy (summarized from hourly_occupancy)

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK)
├── occupancy_date (Date) — Which day
├── total_entries (Integer)
├── total_exits (Integer)
├── avg_occupancy (Float) — Average across all hours
├── peak_occupancy (Integer) — Max occupancy in day
├── peak_hour (Integer) — Which hour had peak
├── min_occupancy (Integer)
├── avg_detection_confidence (Float)
├── unique_persons_count (Integer)
├── is_weekend (Boolean)
├── is_holiday (Boolean)
├── created_at (DateTime)
└── updated_at (DateTime)

Unique Constraint:
└── (camera_id, occupancy_date) UNIQUE

Indexes:
├── idx_daily_camera_date: (camera_id, occupancy_date)
├── idx_daily_date: (occupancy_date)

Example:
  date       | total_entries | total_exits | avg_occupancy | peak | peak_hour
  ──────────────────────────────────────────────────────────────────────────
  2025-01-15 | 234           | 231         | 46.2          | 65   | 14


TABLE: monthly_occupancy
────────────────────────
Monthly aggregated occupancy (summarized from daily_occupancy)

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK)
├── year (Integer)
├── month (Integer) — 1-12
├── total_entries (Integer) — Sum for month
├── total_exits (Integer)
├── avg_daily_occupancy (Float) — Average across all days
├── peak_day_occupancy (Integer) — Highest day occupancy
├── peak_date (Date) — Which date had peak
├── total_working_days (Integer)
├── total_weekend_days (Integer)
├── total_holiday_days (Integer)
├── avg_detection_confidence (Float)
├── unique_persons_count (Integer)
├── created_at (DateTime)
└── updated_at (DateTime)

Unique Constraint:
└── (camera_id, year, month) UNIQUE

Indexes:
├── idx_monthly_camera_date: (camera_id, year, month)
├── idx_monthly_date: (year, month)

Example:
  year | month | total_entries | total_exits | avg_daily_occupancy | peak
  ──────────────────────────────────────────────────────────────────────────
  2025 | 1     | 5460          | 5430        | 45.3                | 78


TABLE: occupancy_alerts
───────────────────────
Alerts for occupancy anomalies

Columns:
├── id (Integer, PK)
├── camera_id (Integer, FK)
├── alert_type (Enum) — CAPACITY_EXCEEDED, ANOMALY_DETECTED, etc.
├── current_occupancy (Integer)
├── threshold_value (Integer) — What triggered alert
├── message (Text)
├── is_resolved (Boolean, Indexed)
├── alert_timestamp (DateTime, Indexed)
├── resolved_timestamp (DateTime, nullable)
└── created_at (DateTime)

Indexes:
├── idx_alert_camera_timestamp: (camera_id, alert_timestamp)
├── idx_alert_type_resolved: (alert_type, is_resolved)

Example:
  camera_id | alert_type          | current_occupancy | threshold | is_resolved
  ──────────────────────────────────────────────────────────────────────────────
  1         | CAPACITY_EXCEEDED   | 105               | 100       | false
  1         | ANOMALY_DETECTED    | 250               | NULL      | false


═══════════════════════════════════════════════════════════════════════════════
│ 5. SERVICE LAYER IMPLEMENTATION
═══════════════════════════════════════════════════════════════════════════════

INITIALIZATION
───────────────

# In FastAPI app startup:

from detection_system.occupancy_endpoints import init_occupancy_service
from database import SessionLocal

# Initialize service on app startup
db = SessionLocal()
init_occupancy_service(db)


FRAME PROCESSING LOOP
──────────────────────

# Main detection pipeline

while camera_is_running:
    frame = capture_frame()
    
    # YOLOv8 + ByteTrack detection (existing)
    detections = yolo_model.detect(frame)  # Returns track_id for each person
    tracked_people = byte_tracker.update(detections)
    
    # NEW: Occupancy tracking
    detection_data = [
        {
            'track_id': person.track_id,
            'confidence': person.confidence,
            'centroid': person.get_centroid(),
            'prev_centroid': person.get_prev_centroid()  # From ByteTrack
        }
        for person in tracked_people
        if person.class_id == PERSON_CLASS  # Exclude vehicles, etc.
    ]
    
    occupancy_service.process_frame(camera_id, detection_data)
    
    # Periodic save (every minute)
    if frame_count % 1500 == 0:  # 1500 frames ≈ 1 minute at 25 fps
        occupancy_service.save_occupancy_log(camera_id, period_seconds=60)


PERIODIC LOGGING
─────────────────

# Call every 1-5 minutes
def save_occupancy_periodic():
    db = SessionLocal()
    for camera in get_active_cameras():
        occupancy_service.save_occupancy_log(camera.id, period_seconds=60)
    db.close()

# Schedule with APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(save_occupancy_periodic, 'interval', minutes=1)
scheduler.start()


AGGREGATION TASKS
──────────────────

# Hourly aggregation - every hour at :00
def hourly_aggregation():
    db = SessionLocal()
    TimeSeriesAggregator.run_hourly_aggregation(db)
    db.close()

# Daily aggregation - every day at midnight
def daily_aggregation():
    db = SessionLocal()
    TimeSeriesAggregator.run_daily_aggregation(db)
    db.close()

# Monthly aggregation - every month on 1st at 00:00
def monthly_aggregation():
    db = SessionLocal()
    TimeSeriesAggregator.run_monthly_aggregation(db)
    db.close()

# Schedule with APScheduler
scheduler.add_job(hourly_aggregation, 'cron', hour='*', minute=0)
scheduler.add_job(daily_aggregation, 'cron', hour=0, minute=0)
scheduler.add_job(monthly_aggregation, 'cron', day=1, hour=0, minute=0)


ERROR HANDLING AND RECOVERY
────────────────────────────

1. Occupancy Goes Negative
   Problem: More exits than entries (detection error)
   Solution: Clamp to 0 in OccupancyCounter.record_exit()
   Recovery: Manual calibration if continues

2. Camera Goes Offline
   Problem: No detection data for camera
   Solution: Mark camera as inactive
   Recovery: Keep last known state, resume when online

3. Line Misconfiguration
   Problem: Line coordinates invalid (e.g., x1 == x2 AND y1 == y2)
   Solution: Validate on line creation
   Recovery: Log error, mark line as inactive

4. Database Connection Loss
   Problem: Can't save logs to database
   Solution: Queue logs in memory temporarily
   Recovery: Attempt retry, reconnect on recovery


═══════════════════════════════════════════════════════════════════════════════
│ 6. API ENDPOINTS REFERENCE
═══════════════════════════════════════════════════════════════════════════════

BASE PATH: /api/occupancy

CAMERA MANAGEMENT
──────────────────

POST /cameras
  Create new camera
  Request:
    {
      "camera_id": "GATE_A",
      "camera_name": "Gate A Entrance",
      "location": "Main Gate",
      "camera_type": "entry_only",
      "max_occupancy": 100,
      "resolution_width": 1920,
      "resolution_height": 1080
    }
  Response: 201
    {
      "id": 1,
      "camera_id": "GATE_A",
      "camera_name": "Gate A Entrance",
      ...
    }

GET /cameras
  List all active cameras
  Response: 200
    [
      {
        "id": 1,
        "camera_id": "GATE_A",
        ...
      }
    ]

GET /cameras/{camera_id}
  Get camera details
  Response: 200
    { ... camera object ... }

PUT /cameras/{camera_id}
  Update camera
  Response: 200
    { ... updated camera ... }


VIRTUAL LINES
──────────────

POST /lines
  Create virtual line
  Request:
    {
      "camera_id": 1,
      "line_name": "Entrance A",
      "x1": 0, "y1": 50,
      "x2": 640, "y2": 50,
      "direction": "entry",
      "confidence_threshold": 0.5
    }
  Response: 201
    { ... line object ... }

GET /cameras/{camera_id}/lines
  Get lines for camera
  Response: 200
    [ ... line objects ... ]

GET /lines/{line_id}
  Get line details
  Response: 200
    { ... line object ... }

PUT /lines/{line_id}
  Update line configuration
  Response: 200
    { ... updated line ... }


REAL-TIME OCCUPANCY
────────────────────

GET /cameras/{camera_id}/live
  Get current occupancy for camera
  Response: 200
    {
      "camera_id": 1,
      "current_occupancy": 45,
      "total_entries": 1234,
      "total_exits": 1189,
      "unique_persons": 45,
      "last_updated": "2025-01-15T10:30:45Z"
    }

GET /facility/live
  Get facility-wide occupancy
  Response: 200
    {
      "facility_occupancy": 450,
      "total_entries_all_cameras": 12340,
      "total_exits_all_cameras": 11890,
      "cameras_active": 3,
      "last_updated": "2025-01-15T10:30:45Z"
    }

POST /cameras/{camera_id}/calibrate
  Manually set occupancy
  Request:
    {
      "occupancy_value": 50,
      "notes": "Manual headcount performed at 10:30"
    }
  Response: 200
    {
      "status": "success",
      "camera_id": 1,
      "occupancy_set_to": 50,
      "timestamp": "2025-01-15T10:31:00Z"
    }


HISTORICAL DATA - REAL-TIME LOGS
─────────────────────────────────

GET /cameras/{camera_id}/logs?hours=24
  Get recent occupancy logs (1-5 minute periods)
  Query Params:
    - hours: int (default 24) — Last N hours
  Response: 200
    [
      {
        "id": 1001,
        "camera_id": 1,
        "entry_count": 5,
        "exit_count": 2,
        "net_occupancy": 45,
        "timestamp": "2025-01-15T10:00:00Z",
        "tracked_persons": 45
      },
      ...
    ]


HISTORICAL DATA - HOURLY
────────────────────────

GET /cameras/{camera_id}/hourly?days=7
  Get hourly summaries
  Query Params:
    - days: int (default 7) — Last N days
  Response: 200
    [
      {
        "hour": "2025-01-15 10:00",
        "camera_id": 1,
        "entries": 15,
        "exits": 8,
        "avg_occupancy": 47.5,
        "peak_occupancy": 52,
        "unique_persons": 22
      },
      ...
    ]


HISTORICAL DATA - DAILY
────────────────────────

GET /cameras/{camera_id}/daily?days=30
  Get daily summaries
  Query Params:
    - days: int (default 30) — Last N days
  Response: 200
    [
      {
        "date": "2025-01-15",
        "camera_id": 1,
        "entries": 234,
        "exits": 231,
        "avg_occupancy": 46.2,
        "peak_occupancy": 65,
        "peak_hour": 14,
        "unique_persons": 180
      },
      ...
    ]


HISTORICAL DATA - MONTHLY
──────────────────────────

GET /cameras/{camera_id}/monthly?months=12
  Get monthly summaries
  Query Params:
    - months: int (default 12) — Last N months
  Response: 200
    [
      {
        "period": "2025-01",
        "camera_id": 1,
        "entries": 5460,
        "exits": 5430,
        "avg_daily_occupancy": 45.3,
        "peak_occupancy": 78,
        "unique_persons": 1850
      },
      ...
    ]


ALERTS
──────

GET /alerts?camera_id=1
  Get active alerts
  Query Params:
    - camera_id: int (optional) — Filter by camera
  Response: 200
    [
      {
        "id": 1,
        "camera_id": 1,
        "alert_type": "capacity_exceeded",
        "current_occupancy": 105,
        "message": "Occupancy exceeds capacity",
        "is_resolved": false,
        "timestamp": "2025-01-15T10:30:00Z"
      },
      ...
    ]

PUT /alerts/{alert_id}/resolve
  Mark alert as resolved
  Response: 200
    {
      "status": "success",
      "alert_id": 1,
      "resolved_at": "2025-01-15T10:35:00Z"
    }


FACILITY STATISTICS
────────────────────

GET /facility/stats
  Get overall facility statistics
  Response: 200
    {
      "total_cameras": 3,
      "active_cameras": 3,
      "total_persons_in_facility": 450,
      "capacity_utilization": 75.5,
      "active_alerts": 2,
      "timestamp": "2025-01-15T10:30:45Z"
    }


AGGREGATION ADMINISTRATION
────────────────────────────

POST /aggregate
  Trigger time-series aggregation (for testing)
  Request:
    {
      "camera_id": null,
      "aggregation_level": "hourly"
    }
  Response: 202 Accepted
    {
      "status": "aggregation_triggered",
      "level": "hourly",
      "timestamp": "2025-01-15T10:30:45Z"
    }


═══════════════════════════════════════════════════════════════════════════════
│ 7. INTEGRATION GUIDE
═══════════════════════════════════════════════════════════════════════════════

INTEGRATION POINTS
───────────────────

1. WITH YOLO + BYTETRACK DETECTION

The occupancy module receives detection output from the unified detection pipeline.

Expected Format:
  detections = {
      'person_boxes': [
          {
              'track_id': 123,
              'confidence': 0.95,
              'bbox': (x1, y1, x2, y2),
              'centroid': (cx, cy),
              'prev_centroid': (px, py)  # From ByteTrack history
          },
          ...
      ]
  }

Integration Code:
  # In realtime_detector.py or detection_pipeline.py
  
  occupancy_service.process_frame(camera_id, [
      {
          'track_id': det['track_id'],
          'confidence': det['confidence'],
          'centroid': det['centroid'],
          'prev_centroid': det.get('prev_centroid')
      }
      for det in detections['person_boxes']
  ])


2. WITH FASTAPI APPLICATION

Integrate occupancy endpoints into main FastAPI application.

# In main.py or app initialization:

from detection_system.occupancy_endpoints import (
    router as occupancy_router,
    init_occupancy_service
)
from database import SessionLocal

# Include router
app.include_router(occupancy_router)

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    init_occupancy_service(db)
    # ... other startup tasks ...


3. WITH DATABASE INITIALIZATION

Create tables during initial setup.

# In database initialization:

from detection_system.occupancy_models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

# Or with migrations:
# alembic upgrade head


4. WITH SCHEDULED TASKS

Schedule hourly/daily/monthly aggregations.

# In app initialization:

from apscheduler.schedulers.background import BackgroundScheduler
from detection_system.occupancy_service import TimeSeriesAggregator
from database import SessionLocal

def setup_occupancy_tasks():
    scheduler = BackgroundScheduler()
    db = SessionLocal()
    
    scheduler.add_job(
        TimeSeriesAggregator.run_hourly_aggregation,
        'cron',
        hour='*',
        minute=0,
        args=(db,)
    )
    
    scheduler.add_job(
        TimeSeriesAggregator.run_daily_aggregation,
        'cron',
        hour=0,
        minute=0,
        args=(db,)
    )
    
    scheduler.add_job(
        TimeSeriesAggregator.run_monthly_aggregation,
        'cron',
        day=1,
        hour=0,
        minute=0,
        args=(db,)
    )
    
    scheduler.start()

# Call in startup
setup_occupancy_tasks()


5. WITH DASHBOARD FRONTEND

Frontend subscribes to real-time occupancy updates.

# Vue/React component example:

const getOccupancy = async (cameraId) => {
  const response = await fetch(`/api/occupancy/cameras/${cameraId}/live`);
  return await response.json();
};

const getHistoricalData = async (cameraId, range = 'daily') => {
  const response = await fetch(`/api/occupancy/cameras/${cameraId}/${range}`);
  return await response.json();
};

// For real-time updates (WebSocket - future feature):
// const ws = new WebSocket('ws://server/api/occupancy/ws/camera/{id}');


CONFIGURATION EXAMPLE
──────────────────────

# In your settings/config.py:

OCCUPANCY_CONFIG = {
    'min_confidence': 0.5,
    'line_crossing_sensitivity': 0.5,  # 0-1, lower = more sensitive
    'log_period_seconds': 60,  # Save logs every 60 seconds
    'max_occupancy_default': 100,
    'aggregation_hours': [0, 12],  # Run additional aggregations at these hours
    'alert_email_recipients': ['admin@factory.com'],
    'capacity_threshold_warning': 0.8,  # Warn at 80% capacity
}


═══════════════════════════════════════════════════════════════════════════════
│ 8. PERFORMANCE CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════════════

COMPUTATIONAL COMPLEXITY
────────────────────────

Line Crossing Detection (per frame):
  Complexity: O(P × L) where P = persons, L = lines
  
  Per person:
    - Get previous position: O(1) from ByteTrack
    - For each line:
      - Calculate side of line: O(1) math operation
      - Verify intersection: O(1) geometry
      - Determine direction: O(1) math
  
  Typical: 30-50 persons × 4 lines = 120-200 operations per frame
  Performance: < 1ms on modern CPU

Aggregation Tasks (scheduled):
  Complexity: O(C × S) where C = cameras, S = samples in period
  
  Hourly aggregation:
    - Sum 60 logs (1-minute periods) per camera
    - Aggregate 24 hourly to daily
    - Complexity: O(1) per camera
  
  Peak aggregation time: < 100ms for 10 cameras

Database Queries:
  Index optimization critical for historical data queries
  - Hourly query (7 days): 168 rows, indexed → < 10ms
  - Daily query (30 days): 30 rows, indexed → < 5ms
  - Monthly query (12 months): 12 rows, indexed → < 2ms


MEMORY USAGE
─────────────

OccupancyService instances:
  - MultiCameraAggregator: ~5KB per camera
  - OccupancyCounter per camera: ~2KB
  - Total: ~7KB per camera × number of cameras
  
  Example: 10 cameras = 70KB memory

Entry/Exit logs (in memory):
  - Stored temporarily before database save
  - ~200 bytes per crossing event
  - With 500 people/hour: ~100KB per camera
  - Total: 1MB for 10 cameras

Time-series aggregates (database):
  - Hourly records: ~300 bytes each
  - 10 cameras × 24 hours × 365 days = 87,600 records = 26MB
  - Daily records: ~400 bytes = 1.5MB
  - Monthly records: ~500 bytes = 60KB
  - Total annual storage: ~28MB


OPTIMIZATION STRATEGIES
────────────────────────

1. Database Query Performance
   ✓ Use indexes on (camera_id, timestamp) columns
   ✓ Paginate historical queries (limit 100 records per request)
   ✓ Cache recent hourly/daily data in Redis
   
2. Detection Pipeline
   ✓ Process only person detections (filter by class)
   ✓ Skip occupancy check if no line configured
   ✓ Use simplified distance metrics
   
3. Aggregation
   ✓ Batch database inserts for multiple cameras
   ✓ Run aggregation tasks off-peak (e.g., 12:01 AM instead of 12:00 AM)
   ✓ Use connection pooling for database
   
4. API Endpoints
   ✓ Cache facility occupancy (update every 5 seconds)
   ✓ Return aggregated data from tables (pre-calculated)
   ✓ Limit time ranges for log queries


SCALING CONSIDERATIONS
────────────────────────

For 50+ cameras:
  1. Run aggregation tasks in separate process/service
  2. Use Celery with Redis for task queue
  3. Implement data archival (move old logs to separate table)
  4. Consider time-series database (InfluxDB, TimescaleDB)

For 500+ cameras:
  1. Shard database by camera groups
  2. Run detection and occupancy on separate servers
  3. Use Kafka for event streaming
  4. Implement caching layer (Redis) for live occupancy


═══════════════════════════════════════════════════════════════════════════════
│ 9. ERROR HANDLING AND RECOVERY
═══════════════════════════════════════════════════════════════════════════════

COMMON FAILURE SCENARIOS AND SOLUTIONS
───────────────────────────────────────

Scenario 1: Occupancy Count Goes Negative
  Cause: More exits detected than entries (detection error)
  Detection: occupancy < 0 in OccupancyCounter
  Recovery:
    - Automatic: Clamp to 0 (no negative occupancy)
    - Manual: HR uses /calibrate endpoint to set correct count
    - Investigation: Check for false positive exits

Scenario 2: Camera Goes Offline
  Cause: Network/connection issue
  Detection: No detections received for 30 seconds
  Recovery:
    - Keep last known occupancy state
    - Mark camera as offline in status
    - Alert admin to issue
    - Resume tracking when camera comes back online

Scenario 3: Line Misconfiguration
  Cause: Invalid line coordinates or formula
  Detection: During line creation
  Recovery:
    - Validate line endpoints during creation
    - Both x1==x2 AND y1==y2 invalid
    - Log error and reject line creation
    - Guide user to fix coordinates

Scenario 4: Database Connection Loss
  Cause: Network/database server issue
  Detection: Database operation fails
  Recovery:
    - Queue logs in memory (up to 100 entries)
    - Log errors for admin review
    - Attempt reconnection on next operation
    - Skip database write, continue tracking
    - Manual data sync when connection restored

Scenario 5: Aggregation Task Fails
  Cause: Database error, logic issue
  Detection: Aggregation function throws exception
  Recovery:
    - Log full error with context
    - Continue to next camera
    - Mark hourly record as incomplete
    - Operator can manually trigger re-aggregation
    - Check logs: ERROR level in occupancy_service.log

Scenario 6: False Positive Line Crossings
  Cause: Occlusion, trajectory skip, detection instability
  Detection: Occupancy spike/anomaly
  Recovery:
    - Increase confidence_threshold on line
    - Add trajectory smoothing filter
    - Use manual calibration if persistent
    - Review camera angle and line placement

Scenario 7: Capacity Alert Storm
  Cause: Occupancy near limit, oscillating
  Detection: Multiple capacity alerts in short time
  Recovery:
    - Add hysteresis: alert at >capacity, clear at <capacity-10
    - Throttle alerts (max 1 per 5 minutes)
    - Use moving average of occupancy


ERROR LOGGING
───────────────

All errors logged with severity levels:

DEBUG:
  - Frame processing details
  - Individual crossing detections
  - Periodic log saves
  
INFO:
  - Service initialization
  - Camera registration
  - Aggregation completion
  - Manual calibrations
  
WARNING:
  - Occupancy anomalies
  - Alert creation
  - Line misconfigurations
  
ERROR:
  - Database operation failures
  - Aggregation exceptions
  - Service initialization failures
  
CRITICAL:
  - Service crashes
  - Permanent database loss


Log Entry Example:

  2025-01-15 10:30:45 ERROR [occupancy_service.py:Line 234]
  Error saving occupancy log: database connection timeout
  Camera ID: 1, Period: 60 seconds
  Traceback: ... (full stack trace)
  Action taken: Queued in memory, will retry


═══════════════════════════════════════════════════════════════════════════════
│ 10. TESTING STRATEGIES
═══════════════════════════════════════════════════════════════════════════════

UNIT TESTS
───────────

Test Line Crossing Detection:
  test_crossing_entry_left_to_right()
  test_crossing_exit_right_to_left()
  test_no_crossing_same_side()
  test_no_crossing_on_line()
  test_crossing_with_tolerance()

Test OccupancyCounter:
  test_record_entry()
  test_record_exit()
  test_occupancy_never_negative()
  test_manual_calibration()
  test_get_state()

Test TimeSeriesAggregator:
  test_aggregate_to_hourly()
  test_aggregate_to_daily()
  test_aggregate_to_monthly()
  test_missing_data_handling()

Test API Endpoints:
  test_create_camera_200()
  test_create_camera_duplicate_409()
  test_get_live_occupancy_200()
  test_manual_calibration_200()
  test_invalid_aggregation_level_400()


INTEGRATION TESTS
──────────────────

Test Full Pipeline:
  1. Create camera + virtual lines
  2. Process simulated detections
  3. Verify occupancy counter
  4. Save occupancy log
  5. Query via API endpoint
  6. Verify data in database

Test Multi-Camera Aggregation:
  1. Create 3 cameras with overlapping areas
  2. Process detections on each
  3. Verify facility-wide occupancy calculation
  4. Ensure no double-counting

Test Scheduled Aggregation:
  1. Create sample occupancy logs
  2. Run hourly aggregation
  3. Verify HourlyOccupancy table populated
  4. Run daily aggregation
  5. Verify DailyOccupancy table populated


PERFORMANCE TESTS
──────────────────

Test Throughput:
  - Process 100 frames/second with line crossing
  - Verify < 5ms overhead per frame
  - Maintain < 100MB memory usage

Test Database:
  - Insert 1M occupancy logs
  - Query 7-day range: < 100ms
  - Aggregation of 1M logs: < 5 seconds

Test Scalability:
  - 10 cameras: normal load
  - 50 cameras: acceptable latency
  - 100 cameras: plan for optimization


SCENARIO TESTS
───────────────

Test 1: Person Enters and Exits
  Setup: Camera with entry/exit lines
  Actions:
    1. Person at pos (0, 100)
    2. Person moves to pos (100, 100) → crosses entry line
    3. Person moves to pos (100, 200) → crosses exit line
  Expected:
    - Entry count = 1
    - Exit count = 1
    - Current occupancy = 0

Test 2: Capacity Alert
  Setup: Camera with max_occupancy = 50
  Actions:
    1. Process 50 entries
    2. Process 51st entry
  Expected:
    - Alert created with type CAPACITY_EXCEEDED
    - Message includes occupancy and threshold

Test 3: Manual Calibration After Error
  Setup: Erroneous -5 occupancy (impossible)
  Actions:
    1. Verify occupancy clamped to 0
    2. HR performs headcount: 45 people
    3. Call /calibrate with 45
  Expected:
    - Occupancy set to 45
    - Log entry created with is_manual_calibration=true

Test 4: Aggregation Pipeline
  Setup: 1440 occupancy logs (1 per minute for 24 hours)
  Actions:
    1. Run hourly aggregation for 24 hours
    2. Run daily aggregation for 1 day
    3. Run monthly aggregation
  Expected:
    - 24 HourlyOccupancy records
    - 1 DailyOccupancy record
    - 1 MonthlyOccupancy record
    - All sums match


═══════════════════════════════════════════════════════════════════════════════
END OF IMPLEMENTATION GUIDE
═══════════════════════════════════════════════════════════════════════════════
```
