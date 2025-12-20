# Factory AI SaaS - Architecture & Data Flow Diagrams

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FACTORY AI SAAS (v4.0.0)                           │
│                    5 Critical Business Logic Modules                        │
└─────────────────────────────────────────────────────────────────────────────┘

                              FastAPI Server (8000)
                                     ↓
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
    ┌────▼────────┐         ┌────────▼────────┐         ┌────────▼────────┐
    │  Frontend    │         │  Background     │         │    External     │
    │  (Angular)   │         │  Scheduler      │         │    Services     │
    │              │         │                │         │                │
    │ - Dashboard  │         │ APScheduler:   │         │ - AWS Rekognition
    │ - Video      │         │ - Hourly Agg   │         │ - RTSP Cameras
    │ - Attendance │         │ - 3 AM Drift   │         │ - Database
    │ - Reports    │         │ - Monthly Sum  │         │
    └──────┬───────┘         └────────────────┘         └────────────────┘
           │
           │ HTTP/REST
           │
    ┌──────▼──────────────────────────────────────────────────────────┐
    │                    MAIN_INTEGRATION.PY                           │
    │                  (FastAPI Application)                           │
    │                                                                  │
    │  Routes:                                                         │
    │  - POST /api/v1/attendance/check-in                             │
    │  - POST /api/v1/vehicle/validate-plate                          │
    │  - GET  /api/v1/occupancy/scheduler-status                      │
    │  - POST /api/v1/identity/cleanup-snapshots                      │
    │  - GET  /api/video_feed                                         │
    │  - GET  /api/health                                             │
    └──────┬──────────────────────────────────────────────────────────┘
           │
           │ Service Injection (Dependency Injection)
           │
    ┌──────┴──────────────────────────────────────────────────────────┐
    │                    5 SERVICE MODULES                             │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Module 1: Identity AWS Retry                            │  │
    │  │  - AWSRetryDecorator (exponential backoff)               │  │
    │  │  - SnapshotCleanupService (90-day retention)             │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Module 2: Vehicle Quality Gate                           │  │
    │  │  - OCR confidence validation (> 0.85)                    │  │
    │  │  - Plate format regex (India std)                        │  │
    │  │  - Blocked vehicle detection + logging                   │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Module 3: Attendance Shift Integrity                    │  │
    │  │  - Grace period logic                                    │  │
    │  │  - Early exit detection                                  │  │
    │  │  - Double-entry prevention (12h cache)                   │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Module 4: Occupancy Scheduler                           │  │
    │  │  - Hourly aggregation (logs → summaries)                 │  │
    │  │  - Drift correction (3 AM reset)                         │  │
    │  │  - Monthly aggregation                                   │  │
    │  │  - APScheduler integration                               │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Module 5: Video RTSP-MJPEG                              │  │
    │  │  - RTSPStreamManager (OpenCV capture)                    │  │
    │  │  - BoundingBoxOverlay (AI predictions)                   │  │
    │  │  - MJPEGStreamEncoder (browser streaming)                │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    └──────┬──────────────────────────────────────────────────────────┘
           │
           │ Database Operations (SQLAlchemy)
           │
    ┌──────▼──────────────────────────────────────────────────────────┐
    │                    DATABASE (PostgreSQL)                         │
    │                                                                  │
    │  Tables:                                                         │
    │  - AttendanceRecord (check-in/out, status, grace_applied)      │
    │  - Shift (shift_name, start_time, end_time, grace_period)      │
    │  - OccupancyLog (current_count, entries, exits per frame)       │
    │  - OccupancyDailyAggregate (hourly summaries)                   │
    │  - OccupancyMonthlyAggregate (monthly trends)                   │
    │  - VehicleLog (plate_number, confidence, status)                │
    │  - AccessLog (employee, entry_time, camera_id)                  │
    │  - Employee (name, shift_id, department)                        │
    │  - UnknownAttendance (unrecognized faces)                        │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Module 1: Identity AWS Retry & Snapshot Cleanup

```
┌─────────────────────────────────────────────────────────────────┐
│                   AWS REKOGNITION CALL                          │
│                                                                 │
│  Function: search_faces_by_image(image_bytes)                  │
│            ↓                                                    │
│  @AWSRetryDecorator(max_retries=3, strategy=EXPONENTIAL)       │
│                                                                 │
│  Attempt 1: ──→ Call AWS API                                   │
│             ✓ Success ──→ Return result                        │
│             ✗ TimeoutError                                     │
│                                                                 │
│  Attempt 2: Wait 1s ──→ Retry AWS API                          │
│             ✓ Success ──→ Return result                        │
│             ✗ ThrottlingException                              │
│                                                                 │
│  Attempt 3: Wait 2s ──→ Retry AWS API                          │
│             ✓ Success ──→ Return result                        │
│             ✗ ServiceUnavailable                               │
│                                                                 │
│  Attempt 4: Wait 4s ──→ Retry AWS API                          │
│             ✓ Success ──→ Return result                        │
│             ✗ Fatal error ──→ Raise exception                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              SNAPSHOT CLEANUP JOB (Scheduled)                    │
│                                                                  │
│  Trigger: Daily at 02:00 AM (maintenance window)                │
│                                                                  │
│  1. Scan /data/snapshots/unknown/                               │
│     for_each_file:                                              │
│       if file.modified_date < (today - 90 days):                │
│         delete_file                                             │
│         total_freed += file.size_mb                             │
│                                                                  │
│  2. Report Results                                              │
│     {                                                           │
│       'files_deleted': 247,                                     │
│       'disk_space_freed_mb': 5120.45,                           │
│       'success': true                                           │
│     }                                                           │
│                                                                  │
│  3. Log to Database                                             │
│     INSERT INTO system_logs (...)                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Module 2: Vehicle Quality Gate & ANPR

```
┌──────────────────────────────────────────────────────────────────────┐
│                    VEHICLE DETECTION PIPELINE                        │
│                                                                      │
│  RTSP Camera Stream                                                  │
│      ↓                                                               │
│  OpenCV Video Capture                                               │
│      ↓                                                               │
│  YOLO Vehicle Detector                                              │
│      ↓ (bounding box for vehicle)                                   │
│  Crop & Send to OCR                                                 │
│      ↓                                                               │
│  EasyOCR / PaddleOCR                                                │
│      ↓ (raw text: "KA 01 AB 1234", confidence: 0.92)               │
│      │                                                               │
│      └──→ QUALITY GATE ──────────────┐                             │
│                                      │                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │          3-LAYER VALIDATION GATE                            │   │
│  │                                                             │   │
│  │  Layer 1: OCR Confidence Check                             │   │
│  │  ├─ Threshold: 0.85 (85%)                                  │   │
│  │  ├─ Test: confidence > 0.85?                               │   │
│  │  ├─ PASS (0.92) ──→ Continue                               │   │
│  │  └─ FAIL (0.75) ──→ REJECT (manual review)                 │   │
│  │                                                             │   │
│  │  Layer 2: Plate Format Validation                          │   │
│  │  ├─ Regex: ^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$           │   │
│  │  ├─ Clean: Remove spaces → "KA01AB1234"                    │   │
│  │  ├─ Test: matches regex?                                   │   │
│  │  ├─ PASS ──→ Continue                                      │   │
│  │  └─ FAIL ──→ REJECT (invalid format)                       │   │
│  │                                                             │   │
│  │  Layer 3: Blocked Vehicle Check                            │   │
│  │  ├─ Lookup: plate in blocked_list?                         │   │
│  │  ├─ PASS (not blocked) ──→ ALLOW                           │   │
│  │  └─ FAIL (blocked) ──→ TRIGGER ALERT                       │   │
│  │         └─ Log to database                                 │   │
│  │         └─ Send security alert                             │   │
│  │         └─ Record snapshot                                 │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                               │
│      ↓                                                               │
│  Response:                                                          │
│  {                                                                  │
│    'valid': true,                                                   │
│    'plate_number': 'KA01AB1234',                                    │
│    'confidence': 0.92,                                              │
│    'status': 'UNKNOWN',                                             │
│    'should_trigger_gate_event': true,                              │
│    'alert_message': None                                            │
│  }                                                                  │
│                                                                      │
│  → Trigger gate relay                                               │
│  → Log to vehicle_log table                                         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Module 3: Attendance Shift Integrity

```
┌──────────────────────────────────────────────────────────────────┐
│                    FACE RECOGNITION CHECK-IN                      │
│                                                                  │
│  Camera detects face                                            │
│       ↓                                                         │
│  AWS Rekognition (with retry decorator)                         │
│       ↓                                                         │
│  Employee matched: John Smith (ID: 123)                         │
│       ↓                                                         │
│  check_in_time = 08:03:45                                       │
│       ↓                                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │    SHIFT INTEGRITY PROCESSING                          │    │
│  │                                                        │    │
│  │  Step 1: DOUBLE-ENTRY CHECK                           │    │
│  │  Is employee in cache (checked in last 12 hours)?      │    │
│  │  NO → Continue                                         │    │
│  │  YES → Skip (return skipped_duplicate: true)           │    │
│  │                                                        │    │
│  │  Step 2: RECORD CHECK-IN                              │    │
│  │  employee_id: 123 → Add to cache with timestamp        │    │
│  │                                                        │    │
│  │  Step 3: GRACE PERIOD CALCULATION                      │    │
│  │  shift.start_time = 08:00:00                           │    │
│  │  shift.grace_period_minutes = 5                        │    │
│  │  grace_time = 08:05:00                                 │    │
│  │                                                        │    │
│  │  Step 4: COMPARE CHECK-IN WITH GRACE                  │    │
│  │  check_in_time (08:03:45) < grace_time (08:05:00)?    │    │
│  │  YES → ON_TIME                                         │    │
│  │  NO → LATE                                             │    │
│  │                                                        │    │
│  │  Step 5: EARLY EXIT DETECTION                          │    │
│  │  (if check_out provided)                               │    │
│  │  check_out_time (16:45:00) < shift.end_time (17:00)?  │    │
│  │  YES → EARLY_EXIT (flagged for review)                 │    │
│  │                                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│       ↓                                                         │
│  Result:                                                        │
│  {                                                              │
│    'status': 'PRESENT',                                         │
│    'is_late': false,                                            │
│    'is_early_exit': false,                                      │
│    'grace_period_applied': false,                               │
│    'flagged_for_review': false,                                 │
│    'skipped_duplicate': false                                   │
│  }                                                              │
│       ↓                                                         │
│  Store in database:                                             │
│  INSERT INTO attendance_record (                                │
│    employee_id=123,                                             │
│    check_in_time='08:03:45',                                    │
│    status='PRESENT',                                            │
│    grace_period_applied=false                                   │
│  )                                                              │
│       ↓                                                         │
│  Dashboard shows: ✓ On Time                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Module 4: Occupancy Scheduler

```
┌──────────────────────────────────────────────────────────────────┐
│               APSCHEDULER BACKGROUND JOBS                        │
│                                                                  │
│  app.on_event("startup"):                                       │
│    scheduler = OccupancyScheduler()                             │
│    scheduler.start()                                            │
│                                                                  │
│  ╔════════════════════════════════════════════════════════════╗ │
│  ║  JOB 1: HOURLY AGGREGATION                                ║ │
│  ║  Trigger: CronTrigger(minute=0)                           ║ │
│  ║  Runs: Every hour at :00 (08:00, 09:00, 10:00, ...)       ║ │
│  ║                                                            ║ │
│  ║  Logic:                                                   ║ │
│  ║  1. Query raw logs from past hour:                        ║ │
│  ║     SELECT * FROM occupancy_log                           ║ │
│  ║     WHERE timestamp >= (now - 1 hour)                     ║ │
│  ║     AND timestamp < now                                   ║ │
│  ║                                                            ║ │
│  ║  2. Calculate statistics:                                 ║ │
│  ║     avg_occupancy = MEAN(current_count)                   ║ │
│  ║     max_occupancy = MAX(current_count)                    ║ │
│  ║     min_occupancy = MIN(current_count)                    ║ │
│  ║     total_entries = SUM(entries)                          ║ │
│  ║     total_exits = SUM(exits)                              ║ │
│  ║                                                            ║ │
│  ║  3. Store aggregate:                                      ║ │
│  ║     INSERT INTO occupancy_daily_aggregate (               ║ │
│  ║       camera_id, occupancy_date, hour,                    ║ │
│  ║       avg_occupancy, max_occupancy, min_occupancy,        ║ │
│  ║       total_entries, total_exits                          ║ │
│  ║     )                                                      ║ │
│  ║                                                            ║ │
│  ║  Result: Database has hourly summary for charting         ║ │
│  ╚════════════════════════════════════════════════════════════╝ │
│                                                                  │
│  ╔════════════════════════════════════════════════════════════╗ │
│  ║  JOB 2: DRIFT CORRECTION                                  ║ │
│  ║  Trigger: CronTrigger(hour=3, minute=0)                   ║ │
│  ║  Runs: Every day at 03:00 AM                              ║ │
│  ║                                                            ║ │
│  ║  Logic:                                                   ║ │
│  ║  1. Get all active cameras:                               ║ │
│  ║     SELECT * FROM camera WHERE is_active = true           ║ │
│  ║                                                            ║ │
│  ║  2. For each camera, reset occupancy:                     ║ │
│  ║     FOR camera IN cameras:                                ║ │
│  ║       INSERT INTO occupancy_log (                          ║ │
│  ║         camera_id, current_count=0, entries=0, exits=0    ║ │
│  ║       )                                                    ║ │
│  ║                                                            ║ │
│  ║  Why 3 AM? Factory is closed, safe to reset               ║ │
│  ║  Benefit: Prevents count drift from accumulating          ║ │
│  ║                                                            ║ │
│  ║  Example: If one person was missed on exit at 2 PM,       ║ │
│  ║  count would stay "1" forever. At 3 AM, resets to "0".    ║ │
│  ╚════════════════════════════════════════════════════════════╝ │
│                                                                  │
│  ╔════════════════════════════════════════════════════════════╗ │
│  ║  JOB 3: MONTHLY AGGREGATION                               ║ │
│  ║  Trigger: CronTrigger(day=1, hour=0, minute=0)            ║ │
│  ║  Runs: 1st of every month at 00:00                        ║ │
│  ║                                                            ║ │
│  ║  Logic:                                                   ║ │
│  ║  1. Get all daily aggregates for previous month:          ║ │
│  ║     SELECT * FROM occupancy_daily_aggregate               ║ │
│  ║     WHERE YEAR(date)=2025 AND MONTH(date)=12              ║ │
│  ║                                                            ║ │
│  ║  2. Calculate monthly stats:                              ║ │
│  ║     avg_occupancy = MEAN(daily.avg_occupancy)             ║ │
│  ║     total_entries = SUM(daily.total_entries)              ║ │
│  ║     total_exits = SUM(daily.total_exits)                  ║ │
│  ║                                                            ║ │
│  ║  3. Store monthly summary:                                ║ │
│  ║     INSERT INTO occupancy_monthly_aggregate (...)         ║ │
│  ║                                                            ║ │
│  ║  Result: Monthly trends for capacity planning             ║ │
│  ╚════════════════════════════════════════════════════════════╝ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Module 5: Video RTSP-to-MJPEG

```
┌────────────────────────────────────────────────────────────────────┐
│                   RTSP STREAM CAPTURE FLOW                         │
│                                                                    │
│  GET /api/video_feed                                              │
│       ↓                                                            │
│  StreamingResponse(video_service.generate_video_stream())         │
│       ↓                                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  FRAME GENERATION LOOP                                       │ │
│  │  while True:                                                 │ │
│  │                                                              │ │
│  │    1. CAPTURE FRAME                                          │ │
│  │       cap.read() → frame (BGR, 1920x1080)                    │ │
│  │       if not connected:                                      │ │
│  │         try_reconnect()                                      │ │
│  │                                                              │ │
│  │    2. RUN DETECTION (Optional)                               │ │
│  │       if detection_model:                                    │ │
│  │         detections = model.predict(frame)                    │ │
│  │         [                                                    │ │
│  │           {'bbox': [100, 200, 300, 400],                    │ │
│  │            'class_name': 'person',                           │ │
│  │            'confidence': 0.95},                              │ │
│  │           {'bbox': [500, 100, 700, 300],                    │ │
│  │            'class_name': 'helmet',                           │ │
│  │            'confidence': 0.87}                               │ │
│  │         ]                                                    │ │
│  │                                                              │ │
│  │    3. DRAW OVERLAYS                                          │ │
│  │       for each detection:                                    │ │
│  │         draw_bounding_box(frame, detection)                  │ │
│  │         draw_label(frame, detection)                         │ │
│  │         → Frame now has colored boxes + confidence scores    │ │
│  │                                                              │ │
│  │    4. DRAW INFO PANEL                                        │ │
│  │       draw_panel(frame, {                                    │ │
│  │         timestamp: '14:32:45',                               │ │
│  │         fps: 29.8,                                           │ │
│  │         detections: 2,                                       │ │
│  │         camera_id: 'CAM-MAIN'                                │ │
│  │       })                                                     │ │
│  │       → Frame now has info at bottom                         │ │
│  │                                                              │ │
│  │    5. ENCODE TO JPEG                                         │ │
│  │       jpeg_bytes = cv2.imencode('.jpg', frame, quality=80)  │ │
│  │                                                              │ │
│  │    6. YIELD MJPEG CHUNK                                      │ │
│  │       yield (                                                │ │
│  │         b'--frame\r\n' +                                    │ │
│  │         b'Content-Type: image/jpeg\r\n' +                   │ │
│  │         b'Content-Length: ' + str(len(jpeg)).encode() +     │ │
│  │         b'\r\n\r\n' +                                        │ │
│  │         jpeg_bytes +                                         │ │
│  │         b'\r\n'                                              │ │
│  │       )                                                      │ │
│  │                                                              │ │
│  │    7. FRAME RATE CONTROL                                     │ │
│  │       sleep(1/30)  # 30 FPS                                  │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│       ↓                                                            │
│  Browser receives multipart/x-mixed-replace stream               │
│  Content-Type: multipart/x-mixed-replace; boundary=frame         │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ MJPEG in Browser                                             │ │
│  │                                                              │ │
│  │ <img src="http://localhost:8000/api/video_feed" />          │ │
│  │                                                              │ │
│  │ Renders live stream with:                                   │ │
│  │ ✓ Bounding boxes (green for person, blue for vehicle)      │ │
│  │ ✓ Confidence scores (95%, 87%, etc.)                        │ │
│  │ ✓ Info panel (FPS, timestamp, object count)                 │ │
│  │ ✓ Auto-reconnect if camera drops                            │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Data Models (Database Schema)

```
┌──────────────────────────────────────┐
│         ATTENDANCE_RECORD            │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ employee_id: INT (FK)                │
│ attendance_date: DATE                │
│ check_in_time: DATETIME              │
│ check_out_time: DATETIME (nullable)  │
│ status: ENUM (PRESENT, LATE, ABSENT) │
│ grace_period_applied: BOOL           │
│ is_early_exit: BOOL                  │
│ created_at: DATETIME                 │
└──────────────────────────────────────┘
         ↑
         │ FK (employee_id)
         │
┌──────────────────────────────────────┐
│           EMPLOYEE                   │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ name: VARCHAR(100)                   │
│ email: VARCHAR(100)                  │
│ shift_id: INT (FK)                   │
│ department_id: INT (FK)              │
│ is_active: BOOL                      │
└──────────────────────────────────────┘
         ↑
         │ FK (shift_id)
         │
┌──────────────────────────────────────┐
│           SHIFT                      │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ shift_name: VARCHAR(50)              │
│ start_time: TIME                     │
│ end_time: TIME                       │
│ grace_period_minutes: INT            │
│ is_active: BOOL                      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│       OCCUPANCY_LOG                  │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ camera_id: VARCHAR(50)               │
│ current_count: INT                   │
│ entries: INT                         │
│ exits: INT                           │
│ timestamp: DATETIME                  │
└──────────────────────────────────────┘
         ↓ (aggregate)
┌──────────────────────────────────────┐
│   OCCUPANCY_DAILY_AGGREGATE          │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ camera_id: VARCHAR(50)               │
│ occupancy_date: DATE                 │
│ hour: INT (0-23)                     │
│ avg_occupancy: FLOAT                 │
│ max_occupancy: INT                   │
│ min_occupancy: INT                   │
│ total_entries: INT                   │
│ total_exits: INT                     │
│ created_at: DATETIME                 │
└──────────────────────────────────────┘
         ↓ (monthly summary)
┌──────────────────────────────────────┐
│  OCCUPANCY_MONTHLY_AGGREGATE         │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ camera_id: VARCHAR(50)               │
│ year: INT                            │
│ month: INT                           │
│ avg_occupancy: FLOAT                 │
│ total_entries: INT                   │
│ total_exits: INT                     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        VEHICLE_LOG                   │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ plate_number: VARCHAR(20)            │
│ ocr_confidence: FLOAT                │
│ vehicle_type: VARCHAR(50)            │
│ status: ENUM (AUTHORIZED, BLOCKED)   │
│ timestamp: DATETIME                  │
│ camera_id: VARCHAR(50)               │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        ACCESS_LOG                    │
├──────────────────────────────────────┤
│ id: INT (PK)                         │
│ employee_id: INT (FK)                │
│ camera_id: VARCHAR(50)               │
│ entry_time: DATETIME                 │
│ confidence: FLOAT                    │
│ face_id: VARCHAR(100)                │
│ snapshot_path: VARCHAR(255)          │
└──────────────────────────────────────┘
```

---

This diagram shows how all 5 modules work together to create a complete Factory AI SaaS system.
