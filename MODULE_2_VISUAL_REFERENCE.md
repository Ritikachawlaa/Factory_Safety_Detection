# Module 2: Vehicle & Gate Management - Visual Reference & Architecture

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FACTORY GATE SYSTEM                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER (RTSP/USB)                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Camera 1 (Gate A)  │  Camera 2 (Gate B)  │  Camera 3 (Parking)  │  ...   │
│   1080p RTSP        │   4MP RTSP          │   HD USB              │         │
│                                                                              │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER (VehicleGateService)                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 1. YOLO Vehicle Detection (YOLOv8n)                                │  │
│  │    ├─ Input: Frame (BGR)                                           │  │
│  │    ├─ Classes: Car, Truck, Bike, Forklift, Bus                    │  │
│  │    ├─ Output: [bbox, class, confidence]                           │  │
│  │    └─ Time: 30-50ms                                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 2. ByteTrack Vehicle Tracking                                       │  │
│  │    ├─ Input: Detections                                            │  │
│  │    ├─ Output: track_id (persistent)                               │  │
│  │    ├─ Session: {track_id: VehicleSession}                         │  │
│  │    └─ Time: 5-10ms                                                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 3. Gate Zone ROI Check                                              │  │
│  │    ├─ Bottom 30% of frame (configurable)                           │  │
│  │    ├─ Is bbox in zone? YES ──→ Trigger ANPR                       │  │
│  │    ├─                    NO  ──→ Skip OCR (cost saving)            │  │
│  │    └─ Time: <1ms                                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 4. ANPR (Automatic Number Plate Recognition)                       │  │
│  │    ├─ Plate extraction & enhancement                               │  │
│  │    ├─ OCR Engine: EasyOCR or PaddleOCR                            │  │
│  │    ├─ Output: plate_number, confidence                             │  │
│  │    └─ Time: 150-300ms (only on gate zone entry)                   │  │
│  │                                                                    │  │
│  │    Note: RUNS ONCE PER VEHICLE (huge cost saving!)                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 5. Authorization Lookup                                             │  │
│  │    ├─ Query: AuthorizedVehicle table                              │  │
│  │    ├─ Status: allowed / blocked / pending_review                  │  │
│  │    ├─ Category: employee / vendor / guest / contractor            │  │
│  │    └─ Time: <5ms                                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 6. Alert Generation & Snapshot Capture                              │  │
│  │    ├─ BLOCKED ──→ Alert + High-res snapshot                       │  │
│  │    ├─ UNKNOWN ──→ Alert + High-res snapshot                       │  │
│  │    ├─ AUTHORIZED ──→ No alert, no snapshot (save storage)         │  │
│  │    └─ Path: snapshots/vehicles/YYYY-MM-DD/                        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 7. Database Logging (VehicleAccessLog)                              │  │
│  │    ├─ plate_number, vehicle_type, entry_time, status              │  │
│  │    ├─ snapshot_path, plate_confidence, duration                   │  │
│  │    ├─ Indexed queries: <20ms                                      │  │
│  │    └─ 90-day retention policy                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI LAYER (HTTP API)                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  POST /api/module2/process-frame      →  Real-time processing             │
│  POST /api/module2/vehicle/register   →  Register new vehicle             │
│  GET  /api/module2/vehicles           →  List/search vehicles             │
│  PUT  /api/module2/vehicles/{id}/status → Update status                   │
│  GET  /api/module2/access-logs        →  Query access logs                │
│  GET  /api/module2/access-logs/daily-summary → Daily report              │
│  GET  /api/module2/access-logs/monthly-summary → Monthly report          │
│  GET  /api/module2/alerts             →  Recent alerts                    │
│  GET  /api/module2/statistics         →  Real-time statistics             │
│  GET  /api/module2/health             →  Service health                   │
│                                                                              │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER (Dashboard/Alerting)                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Web Dashboard                          Email Alerts                 │  │
│  │ ├─ Real-time vehicle counts           │ BLOCKED vehicle detected   │  │
│  │ ├─ Live camera feeds                  │ Unknown plate detected    │  │
│  │ ├─ Access logs viewer                 │ Gate zone alert          │  │
│  │ ├─ Daily/Monthly reports              └──────────────────────────│  │
│  │ └─ Alert management                                               │  │
│  │                                                                   │  │
│  │ SMS Notifications                      System Logging            │  │
│  │ ├─ Critical alerts only                │ vehicle_gate.log        │  │
│  │ ├─ Gate failures                       │ Error tracking          │  │
│  │ └─ Unauthorized entry                  │ Performance metrics     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline - Detailed Flow

```
                    INCOMING FRAME
                          │
                          ▼
           ┌──────────────────────────────┐
           │ YOLO Vehicle Detection       │
           │ (YOLOv8n on GPU/CPU)         │
           └──────────────┬───────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ Extract Detections:                  │
        │ [                                    │
        │   (x1, y1, x2, y2, "car", 0.95),    │
        │   (x1, y1, x2, y2, "truck", 0.87),  │
        │   (x1, y1, x2, y2, "bike", 0.91)    │
        │ ]                                    │
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ ByteTrack Assignment                │
        │ Input: Detections                   │
        │ Output: track_id (persistent)       │
        │                                     │
        │ Example:                            │
        │ track_id=1 → car                    │
        │ track_id=2 → truck                  │
        │ track_id=3 → bike                   │
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────────────────┐
        │ FOR EACH TRACKED VEHICLE:                       │
        │                                                 │
        │ ┌─────────────────────────────────────────────┐ │
        │ │ 1. Check Gate Zone ROI                      │ │
        │ │    Is bbox in bottom 30% of frame?          │ │
        │ └─────────────────────────────────────────────┘ │
        │         │                      │                │
        │       YES                      NO               │
        │         │                      │                │
        │         ▼                      ▼                │
        │   ┌──────────────┐        ┌─────────┐          │
        │   │ Trigger ANPR │        │ Skip    │          │
        │   │ (once only)  │        │ OCR     │          │
        │   └──────┬───────┘        │(save$$) │          │
        │          │                └─────────┘          │
        │          ▼                                      │
        │   ┌──────────────────────┐                     │
        │   │ Extract Plate Region │                     │
        │   │ (from bbox)          │                     │
        │   └──────┬───────────────┘                     │
        │          │                                      │
        │          ▼                                      │
        │   ┌──────────────────────┐                     │
        │   │ Enhance Image        │                     │
        │   │ (CLAHE+filter)       │                     │
        │   └──────┬───────────────┘                     │
        │          │                                      │
        │          ▼                                      │
        │   ┌──────────────────────┐                     │
        │   │ OCR Recognition      │                     │
        │   │ (EasyOCR/PaddleOCR)  │                     │
        │   └──────┬───────────────┘                     │
        │          │                                      │
        │          ▼                                      │
        │   ┌──────────────────────────┐                 │
        │   │ Result:                  │                 │
        │   │ plate="ABC123"           │                 │
        │   │ confidence=0.92          │                 │
        │   └──────┬───────────────────┘                 │
        │          │                                      │
        └──────────┼──────────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────────┐
        │ Query AuthorizedVehicle Table       │
        │                                     │
        │ SELECT * FROM authorized_vehicles  │
        │ WHERE plate_number = "ABC123"       │
        └────────────────┬────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
        FOUND         FOUND        NOT FOUND
        status=       status=
        BLOCKED       ALLOWED
           │             │             │
           ▼             ▼             ▼
        ┌────────┐  ┌────────┐   ┌─────────────┐
        │ ALERT  │  │ SILENT │   │ ALERT       │
        │ + SNAP │  │ PASS   │   │ + SNAP      │
        │ (save) │  │(no snap)    │ (unknown)   │
        └────┬───┘  └────┬───┘   └─────┬───────┘
             │           │            │
             └───────────┼────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ Store in VehicleAccessLog           │
        │                                     │
        │ INSERT INTO vehicle_access_logs:    │
        │ - track_id                          │
        │ - plate_number                      │
        │ - vehicle_type                      │
        │ - entry_time (NOW)                  │
        │ - status (authorized/blocked/unk)   │
        │ - plate_confidence (0.92)           │
        │ - snapshot_path (if blocked/unknown)│
        │ - notes                             │
        └─────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Response:    │
                  │ ├─ sessions  │
                  │ ├─ alerts    │
                  │ └─ counts    │
                  └──────────────┘
```

---

## VehicleSession State Machine

```
              ┌─────────────────────────┐
              │  SESSION_INITIALIZED    │
              │                         │
              │ track_id assigned       │
              │ vehicle_type detected   │
              │ detected_at = NOW       │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  TRACKING_ACTIVE        │
              │                         │
              │ Visible in frames       │
              │ bbox updated            │
              │ last_seen_frame = i     │
              └────────────┬────────────┘
                           │
                   ┌───────┴────────┐
                   │                │
                NO                 YES (enters gate zone)
              gate_zone            │
                   │                ▼
                   │  ┌─────────────────────────┐
                   │  │ GATE_ZONE_TRIGGERED     │
                   │  │                         │
                   │  │ ocr_triggered = True    │
                   │  │ ANPR runs (one time!)   │
                   │  │ plate_number recognized │
                   │  │ status determined       │
                   │  └──────────┬──────────────┘
                   │             │
        ┌──────────┴─────┬───────┴──────┬───────┐
        │                │              │       │
     AUTHORIZED      BLOCKED       UNKNOWN   UNREADABLE
        │                │              │       │
        ▼                ▼              ▼       ▼
    (SILENT)       ┌─────────┐  ┌─────────┐ ┌──────────┐
                   │ ALERT!  │  │ ALERT!  │ │ ALERT!   │
                   │ SNAPSHOT│  │ SNAPSHOT│ │ SNAPSHOT │
                   │ (save)  │  │ (save)  │ │ (save)   │
                   └─────────┘  └─────────┘ └──────────┘
                   │             │           │       │
                   └─────────────┼───────────┴───────┘
                                 │
                                 ▼
              ┌─────────────────────────────┐
              │ LOGGED_TO_DATABASE          │
              │                             │
              │ VehicleAccessLog created    │
              │ snapshot_path stored        │
              │ entry_time recorded         │
              └────────────┬────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │ SESSION_EXPIRED             │
              │                             │
              │ No updates for 300+ sec     │
              │ Vehicle left area           │
              │ Session removed from memory │
              └─────────────────────────────┘
```

---

## Database Schema Visualization

```
┌─────────────────────────────────────────┐
│      AUTHORIZED_VEHICLES TABLE          │
├─────────────────────────────────────────┤
│                                         │
│  PK: id                                │
│  ├─ plate_number (UNIQUE) ◄────────────┼──┐
│  ├─ owner_name                         │  │
│  ├─ owner_email                        │  │
│  ├─ vehicle_type                       │  │
│  │  └─ (car, truck, bike, bus, fork)   │  │
│  ├─ vehicle_model                      │  │
│  ├─ status                             │  │
│  │  └─ (allowed, blocked, pending...)  │  │
│  ├─ category                           │  │
│  │  └─ (employee, vendor, guest...)    │  │
│  ├─ department                         │  │
│  ├─ phone_number                       │  │
│  ├─ notes (TEXT)                       │  │
│  ├─ snapshot_path                      │  │
│  ├─ is_active (INDEX)                  │  │
│  ├─ created_at (INDEX)                 │  │
│  ├─ updated_at                         │  │
│  └─ last_access                        │  │
│                                         │  │
│  Indexes:                               │  │
│  ├─ idx_plate_status                   │  │
│  ├─ idx_owner_category                 │  │
│  ├─ idx_vehicle_type                   │  │
│  └─ idx_is_active                      │  │
│                                         │  │
└─────────────────────────────────────────┘  │
                    │                        │
        ┌───────────┴────────────────────────┤
        │                                    │
        │ 1:N Relationship                   │
        │ (One vehicle → Many access logs)   │
        │                                    │
        ▼                                    │
┌──────────────────────────────────────────┐│
│   VEHICLE_ACCESS_LOGS TABLE             ││
├──────────────────────────────────────────┤│
│                                          ││
│ PK: id                                   ││
│ FK: vehicle_id ──────────────────────────┘│
│ ├─ plate_number (denormalized)           │
│ ├─ vehicle_type                          │
│ ├─ entry_time (INDEX)                    │
│ ├─ exit_time                             │
│ ├─ duration_seconds                      │
│ ├─ status (INDEX)                        │
│ │  └─ (authorized, blocked, unknown)     │
│ ├─ category (INDEX)                      │
│ │  └─ (employee, vendor, guest...)       │
│ ├─ is_authorized (INDEX)                 │
│ ├─ snapshot_path                         │
│ ├─ full_frame_path                       │
│ ├─ entry_point                           │
│ ├─ location_x, location_y                │
│ ├─ plate_confidence (0-1)                │
│ ├─ notes (TEXT)                          │
│ ├─ flagged (INDEX)                       │
│ │  └─ (for manual review)                │
│ └─ created_at (INDEX)                    │
│                                          │
│ Indexes:                                 │
│ ├─ idx_entry_time                        │
│ ├─ idx_plate_entry_time                  │
│ ├─ idx_status_created                    │
│ ├─ idx_flagged_created                   │
│ └─ idx_vehicle_type_entry                │
│                                          │
│ Constraints:                             │
│ ├─ 90-day retention policy               │
│ └─ ON DELETE SET NULL (vehicle)          │
│                                          │
└──────────────────────────────────────────┘
```

---

## Gate Zone ROI Visualization

```
                    1080p Camera Frame
    ┌───────────────────────────────────────────────┐
    │                                               │  H=1080
    │                                               │
    │                  TRAFFIC SCENE                │
    │                  (Parking, Street, etc)       │
    │                                               │
    │         [Car1]    [Truck]    [Car2]           │
    │                                               │
    │                                               │  y = 0
    │ ┌─────────────────────────────────────────┐  │
    │ │                                         │  │
    │ │         NOT IN GATE ZONE                │  │
    │ │         (No OCR triggered)              │  │
    │ │                                         │  │
    │ │                                         │  │
    │ └─────────────────────────────────────────┘  │  y = 756 (70%)
    │ ┌─────────────────────────────────────────┐  │
    │ │                                         │  │
    │ │      GATE ZONE (bottom 30%)             │  │
    │ │      ◄─ OCR TRIGGERED HERE ─►           │  │
    │ │                                         │  │
    │ │   [License Plates Visible]              │  │
    │ │   ANPR runs when bbox enters            │  │
    │ │                                         │  │
    │ └─────────────────────────────────────────┘  │  y = 1080 (100%)
    │                                               │
    │  W=1920 ─────────────────────────────────────│
    └───────────────────────────────────────────────┘

Configuration:
└─ zone_percentage = 0.3
└─ start_y = 1080 * (1 - 0.3) = 756
└─ end_y = 1080
└─ start_x = 0
└─ end_x = 1920

Cost Saving: ~85% reduction in OCR calls!
```

---

## Real-time Performance Metrics

```
TYPICAL PROCESSING TIMELINE (1080p frame):

Frame Received
    │
    ├─ 0ms ────────────────────────────────────┐
    │                                          │
    ├─ YOLO Detection: 30-50ms                 │ YOLO
    │                                          │
    ├─ 50ms ────────────────────────────────────┐
    │                                          │
    ├─ ByteTrack: 5-10ms                       │ Tracking
    │                                          │
    ├─ 60ms ────────────────────────────────────┐
    │                                          │
    ├─ ROI Check: <1ms × 3 vehicles = 0-3ms   │ Geometry
    │                                          │
    ├─ 63ms ────────────────────────────────────┐
    │                                          │
    ├─ Plate Extraction: 2-5ms (1 vehicle)     │ Image ops
    │                                          │
    ├─ 68ms ────────────────────────────────────┐
    │                                          │
    ├─ ANPR Recognition: 150-300ms (1 vehicle) │ OCR
    │ (Only 1 of 3 vehicles enters gate zone)  │
    │                                          │
    ├─ 368ms ────────────────────────────────────┐
    │                                          │
    ├─ DB Query & Insert: 10-20ms              │ Database
    │                                          │
    └─ 388ms ────────────────────────────────────┘

Total: ~70-120ms per frame
Effective FPS: 8-14 FPS (with OCR)
Without OCR: 50-70ms (15-20 FPS)

Optimization: Process in parallel
- YOLO on GPU thread
- OCR on separate thread
- Database on async task

Result: 20-30 FPS possible!
```

---

## Alert Flow Diagram

```
Vehicle detected at gate
         │
         ▼
Check authorization status
    │        │         │
 ALLOWED  BLOCKED   UNKNOWN
    │        │         │
    NO      YES       YES
   ALERT    ALERT    ALERT
    │        │         │
    ▼        ▼         ▼
 ┌────────────────────────┐
 │ Generate FrameGateAlert│
 ├────────────────────────┤
 │ - alert_type          │
 │ - track_id            │
 │ - vehicle_type        │
 │ - plate_number        │
 │ - timestamp           │
 │ - confidence          │
 │ - message             │
 └────────────────────────┘
           │
           ▼
 ┌────────────────────────┐
 │ Save High-res Snapshot │
 │ Path: snapshots/       │
 │ vehicles/YYYY-MM-DD/   │
 │ vehicle_123_BLOCKED.jpg│
 └────────────────────────┘
           │
           ▼
 ┌────────────────────────┐
 │ Append to Alert Queue  │
 │ (in-memory list)       │
 └────────────────────────┘
           │
           ▼
 ┌────────────────────────┐
 │ Get /api/module2/alerts│
 │ (HTTP endpoint)        │
 └────────────────────────┘
           │
           ▼
 ┌──────────────────────────────┐
 │ Client Notification System    │
 ├──────────────────────────────┤
 │ ├─ Email to security team    │
 │ ├─ SMS alert (critical only) │
 │ ├─ Dashboard notification    │
 │ ├─ Audio/visual alarm        │
 │ └─ Log for audit trail       │
 └──────────────────────────────┘
```

---

## Data Retention & Cleanup Policy

```
DAY 1-30: HOT DATA
├─ VehicleAccessLog entries: Active queries
├─ Snapshots: Available in fast storage
└─ Performance: Optimized for speed

DAY 31-90: WARM DATA
├─ VehicleAccessLog entries: Archived queries
├─ Snapshots: Available but slower access
└─ Performance: May require indices

DAY 91+: COLD DATA (DELETED)
├─ VehicleAccessLog entries: Permanently deleted
├─ Snapshots: File system cleanup
└─ Compliance: 90-day audit requirement satisfied

Cleanup Script (runs daily):
┌─────────────────────────────────────┐
│ DELETE FROM vehicle_access_logs     │
│ WHERE created_at < NOW() - 90 days  │
│                                     │
│ Result: ~100-500 records/day        │
│ Storage savings: ~10-50MB/day       │
└─────────────────────────────────────┘
```

---

## Vehicle Classification Examples

```
YOLO Detection Examples:

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Car        │    │   Truck      │    │   Bus        │
│   ████████   │    │   ████████   │    │   ████████   │
│   ████████   │    │   ████████   │    │   ████████   │
│   ██    ██   │    │   ████████   │    │   ██    ██   │
│              │    │   ████████   │    │              │
│ confidence:  │    │              │    │ confidence:  │
│ 0.97         │    │ confidence:  │    │ 0.89         │
└──────────────┘    │ 0.94         │    └──────────────┘
                    └──────────────┘

┌──────────────┐    ┌──────────────┐
│   Bike       │    │   Forklift   │
│    ░░        │    │   ████████   │
│   ░░░░░░     │    │   ████  ████ │
│    ░░░░      │    │   ████████   │
│     ░░       │    │   ████████   │
│              │    │              │
│ confidence:  │    │ confidence:  │
│ 0.85         │    │ 0.92         │
└──────────────┘    └──────────────┘
```

---

End of Visual Reference Guide
