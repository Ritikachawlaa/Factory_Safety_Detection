# 🔄 Complete Data Flow & Integration Specifications

**Version:** 4.0.0  
**All 4 Modules Integrated:** ✅

---

## Complete Frame Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRAME ARRIVES AT /api/process                            │
│                         (Base64 encoded JPEG)                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
                      ┌────────────────────────────┐
                      │   STEP 1: DECODE FRAME    │
                      │  Base64 → OpenCV (BGR)    │
                      └────────────┬───────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────────┐
                  │ STEP 2: YOLO DETECTION & TRACKING  │
                  │ Detects people & vehicles          │
                  │ Assigns track_ids (persistent)     │
                  └──────────────┬─────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌───────────────────────┐  ┌──────────────────────┐
        │   PEOPLE DETECTED     │  │ VEHICLES DETECTED    │
        │   Count: N            │  │ Count: M             │
        └──────────┬────────────┘  └──────────┬───────────┘
                   │                          │
        ┌──────────▼──────────┐      ┌────────▼──────────┐
        │ MODULE 1 & 3:       │      │ MODULE 2:         │
        │ IDENTITY &          │      │ VEHICLE & ANPR    │
        │ ATTENDANCE          │      │                   │
        └──────────┬──────────┘      └────────┬──────────┘
                   │                          │
        ┌──────────▼────────────────────────────────────┐
        │ FOR EACH PERSON:                              │
        │  1. Crop face region from frame              │
        │  2. Check face_cache[track_id]               │
        │     ├─ IF EXISTS & NOT EXPIRED:              │
        │     │  └─ Return cached name + confidence    │
        │     │     (COST: $0, TIME: 1ms) ✅            │
        │     └─ IF MISS OR EXPIRED:                   │
        │        ├─ Convert face to JPEG bytes         │
        │        ├─ Call AWS Rekognition               │
        │        ├─ Get employee_name + confidence     │
        │        └─ Cache for 10 minutes               │
        │           (COST: $0.001, TIME: 150ms) 💾    │
        │  3. Result: {track_id, name, confidence}    │
        │  4. Log to attendance_records table          │
        └──────────┬────────────────────────────────────┘
                   │
        ┌──────────▼────────────────────────────────────┐
        │ FOR EACH VEHICLE:                             │
        │  1. Crop vehicle bounding box                │
        │  2. Run EasyOCR on plate region              │
        │     └─ Extract plate number (e.g., KA01...) │
        │        (COST: $0, TIME: 75ms) 📸             │
        │  3. Result: {track_id, type, plate}         │
        │  4. Log to vehicle_logs table                │
        └──────────┬────────────────────────────────────┘
                   │
        ┌──────────▼────────────────────────────────────┐
        │ MODULE 4: OCCUPANCY COUNTING                 │
        │  1. For each person's centroid:              │
        │     └─ Check if crossed virtual line (y=400) │
        │  2. Entry detected: occupancy += 1           │
        │  3. Exit detected: occupancy -= 1            │
        │  4. Log to occupancy_logs table              │
        └──────────┬────────────────────────────────────┘
                   │
                   ▼
                ┌──────────────────┐
                │  BUILD RESPONSE  │
                │ {success, frame, │
                │  occupancy,      │
                │  entries, exits} │
                └────────┬─────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │ LOG TO SYSTEM_METRICS TABLE   │
        │  - processing_time_ms          │
        │  - aws_calls_made             │
        │  - aws_cost_estimated         │
        └────────────┬───────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  RETURN RESULT  │
            │   TO FRONTEND   │
            └─────────────────┘
```

---

## Complete Request/Response Examples

### Example 1: Frame with Multiple People & Vehicles

**REQUEST:**
```bash
POST /api/process
Content-Type: application/json

{
  "frame": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k..."
}
```

**RESPONSE:**
```json
{
  "success": true,
  "frame_id": 42,
  "timestamp": "2025-12-20T14:30:45.123Z",
  
  "occupancy": 42,
  "entries": 150,
  "exits": 108,
  "entries_this_frame": 2,
  "exits_this_frame": 1,
  
  "faces_recognized": [
    {
      "track_id": 1,
      "name": "John Doe",
      "confidence": 95.5,
      "source": "aws",
      "details": {
        "employee_id": "EMP001",
        "timestamp": "2025-12-20T14:30:44.000Z"
      }
    },
    {
      "track_id": 2,
      "name": "Jane Smith",
      "confidence": 92.3,
      "source": "cache",
      "details": {
        "employee_id": "EMP002",
        "cached_at": "2025-12-20T14:28:15.000Z"
      }
    },
    {
      "track_id": 3,
      "name": "Unknown",
      "confidence": 0,
      "source": "no_match",
      "details": {
        "reason": "No face matched in AWS Rekognition",
        "recommendation": "Enroll this employee"
      }
    }
  ],
  
  "vehicles_detected": [
    {
      "track_id": 100,
      "type": "car",
      "plate": "KA01AB1234",
      "confidence": 0.87,
      "status": "allowed",
      "details": {
        "timestamp": "2025-12-20T14:30:44.500Z",
        "ocr_confidence": 0.92
      }
    },
    {
      "track_id": 101,
      "type": "truck",
      "plate": "TG02XY5678",
      "confidence": 0.85,
      "status": "allowed",
      "details": {
        "timestamp": "2025-12-20T14:30:44.600Z",
        "ocr_confidence": 0.88
      }
    }
  ],
  
  "people_count": 3,
  "vehicle_count": 2,
  "processing_time_ms": 145.32,
  
  "performance": {
    "decoding_time_ms": 5,
    "yolo_inference_ms": 25,
    "face_processing_ms": 85,
    "vehicle_processing_ms": 20,
    "database_write_ms": 15
  }
}
```

---

### Example 2: Empty Frame (No People/Vehicles)

**REQUEST:**
```bash
POST /api/process
{
  "frame": "..."  # Base64 image of empty factory floor
}
```

**RESPONSE:**
```json
{
  "success": true,
  "frame_id": 43,
  "timestamp": "2025-12-20T14:30:50.500Z",
  
  "occupancy": 41,
  "entries": 150,
  "exits": 109,
  "entries_this_frame": 0,
  "exits_this_frame": 0,
  
  "faces_recognized": [],
  "vehicles_detected": [],
  
  "people_count": 0,
  "vehicle_count": 0,
  "processing_time_ms": 32.45,
  
  "note": "Frame processed successfully. No people or vehicles detected."
}
```

---

### Example 3: Person Crossing Entry/Exit Line

**SCENARIO:** Person walks from top of frame (y=300) to bottom (y=450)

**Frame 1 Response:**
```json
{
  "frame_id": 100,
  "occupancy": 10,
  "entries": 50,
  "exits": 40,
  "entries_this_frame": 0,
  "exits_this_frame": 0,
  "faces_recognized": [
    {
      "track_id": 5,
      "name": "John Doe",
      "confidence": 94.2,
      "source": "cache"
    }
  ]
}
```

**Frame 2 Response (centroid moved from y=300 to y=420):**
```json
{
  "frame_id": 101,
  "occupancy": 11,
  "entries": 51,
  "exits": 40,
  "entries_this_frame": 1,
  "exits_this_frame": 0,
  "faces_recognized": [
    {
      "track_id": 5,
      "name": "John Doe",
      "confidence": 94.2,
      "source": "cache"
    }
  ],
  "note": "ENTRY detected for John Doe (track_id=5)"
}
```

---

### Example 4: Face Not Recognized (New Employee)

**REQUEST:**
```bash
POST /api/process
{
  "frame": "..."  # Image with person not in AWS collection
}
```

**RESPONSE:**
```json
{
  "success": true,
  "frame_id": 44,
  "timestamp": "2025-12-20T14:31:00.000Z",
  
  "occupancy": 42,
  "entries": 151,
  "exits": 109,
  
  "faces_recognized": [
    {
      "track_id": 6,
      "name": "Unknown",
      "confidence": 0,
      "source": "no_match",
      "details": {
        "reason": "No matching face in AWS Rekognition collection",
        "track_id_first_seen": 6,
        "recommendation": "Call POST /api/enroll-employee with this person's photo"
      }
    }
  ],
  
  "vehicles_detected": [],
  
  "people_count": 1,
  "vehicle_count": 0,
  "processing_time_ms": 245.67
}
```

**NEXT STEP - Enroll the person:**
```bash
POST /api/enroll-employee
{
  "employee_id": "EMP999",
  "employee_name": "New Employee",
  "frame": "..."  # Base64 face photo
}

# Response:
{
  "success": true,
  "message": "Successfully enrolled New Employee",
  "employee_id": "EMP999"
}
```

**THEN:** Re-process frame → Will recognize as "New Employee"

---

## Database Records Created Per Frame

### 1. attendance_records (Module 3)

```python
# Created for each recognized person
{
    'employee_id': 1,                          # From AWS Rekognition
    'check_in_time': datetime(2025, 12, 20, 14, 30, 44),
    'check_out_time': None,                    # Set on exit
    'status': 'PRESENT',                       # PRESENT, LATE, EARLY_EXIT
    'grace_period_used': 0,                    # Minutes
    'aws_face_confidence': 95.5,
    'track_id': 1
}
```

### 2. vehicle_logs (Module 2)

```python
# Created for each detected vehicle
{
    'track_id': 100,
    'plate_number': 'KA01AB1234',
    'vehicle_type': 'car',
    'entry_time': datetime(2025, 12, 20, 14, 30, 44, 500),
    'exit_time': None,
    'ocr_confidence': 0.92,
    'status': 'ALLOWED'
}
```

### 3. occupancy_logs (Module 4)

```python
# Created for every frame
{
    'camera_id': 1,
    'current_occupancy': 42,
    'entries_count': 151,
    'exits_count': 109,
    'people_detected': 3,
    'vehicles_detected': 2,
    'timestamp': datetime(2025, 12, 20, 14, 30, 45, 123)
}
```

### 4. system_metrics (Monitoring)

```python
# Created for every frame
{
    'frame_id': 42,
    'processing_time_ms': 145.32,
    'gpu_memory_used': 0,  # 0 if CPU-only
    'cpu_usage': 45.2,
    'faces_processed': 3,
    'vehicles_processed': 2,
    'aws_calls': 1,  # Only new track_ids
    'aws_cost_estimated': 0.001,
    'cache_hits': 2,
    'cache_misses': 1,
    'timestamp': datetime(2025, 12, 20, 14, 30, 45, 123)
}
```

---

## Cost Analysis Per Frame

### Frame with 3 People (2 cached, 1 new)

| Operation | Count | Cost | Time |
|-----------|-------|------|------|
| YOLOv8 inference | 1 | $0 | 25ms |
| Face cache hits | 2 | $0 | 2ms |
| AWS Rekognition calls | 1 | $0.001 | 150ms |
| EasyOCR vehicle | 2 | $0 | 75ms |
| Database writes | 5 | $0 | 15ms |
| **TOTAL** | | **$0.001** | **267ms** |

### Monthly Cost (7 FPS, 10 hours/day, 30 days)

```
Frames per day:    252,000 (7 FPS × 3600s × 10 hours)
Frames per month:  7,560,000

AWS Calls per frame:  10% (90% cache hit rate)
Total AWS calls:      756,000

AWS Cost per 1000:    $1
Monthly AWS cost:     756,000 / 1000 × $1 = $756

WITH CACHING (90% hit):
AWS calls per frame:  1% (10% miss rate due to new people)
Total AWS calls:      75,600
Monthly AWS cost:     75,600 / 1000 × $1 = $75.60

SAVINGS: $756 - $75.60 = $680.40/month (90% reduction)
```

---

## State Persistence Across Frames

### Known Faces Dictionary (Stateful Tracking)

```python
# This dictionary is maintained in memory while server runs
known_faces = {
    1: {
        'employee_id': 'EMP001',
        'employee_name': 'John Doe',
        'confidence': 95.5,
        'last_seen': datetime(2025, 12, 20, 14, 30, 44),
        'expires_at': datetime(2025, 12, 20, 14, 40, 44)  # 10 min TTL
    },
    2: {
        'employee_id': 'EMP002',
        'employee_name': 'Jane Smith',
        'confidence': 92.3,
        'last_seen': datetime(2025, 12, 20, 14, 30, 45),
        'expires_at': datetime(2025, 12, 20, 14, 40, 45)
    }
}

# When processing frame:
for person in people:
    track_id = person['track_id']
    
    if track_id in known_faces:
        # Check if expired
        if datetime.now() < known_faces[track_id]['expires_at']:
            # Use cached result
            result = known_faces[track_id]  # Cost: $0
        else:
            # Expired, re-query AWS
            result = aws.search_face(...)   # Cost: $0.001
            known_faces[track_id] = result
    else:
        # First time seeing this track_id
        result = aws.search_face(...)       # Cost: $0.001
        known_faces[track_id] = result
```

---

## Centroid Tracking for Line Crossing

### Previous Centroids Dictionary

```python
# Tracks position of each person across frames
previous_centroids = {
    1: (640, 300),  # John Doe at (x=640, y=300)
    2: (500, 450),  # Jane Smith at (x=500, y=450)
    3: (800, 200)   # Unknown at (x=800, y=200)
}

# Line defined at y = 400
LINE_Y = 400

# Frame N: Detect person with track_id=1 at y=420
new_centroid = (640, 420)

# Check if line was crossed:
prev_y = previous_centroids[1][1]  # 300
new_y = new_centroid[1]             # 420

if prev_y <= LINE_Y < new_y:
    # ENTRY: moved from above line to below line
    occupancy += 1
    entries += 1
    print(f"✅ ENTRY: John Doe")
elif prev_y > LINE_Y >= new_y:
    # EXIT: moved from below line to above line
    occupancy -= 1
    exits += 1
    print(f"✅ EXIT: John Doe")

# Update for next frame
previous_centroids[1] = new_centroid
```

---

## Error Handling & Fallbacks

### Invalid Frame

```json
{
  "success": false,
  "error": "Failed to decode frame. Ensure base64 is valid JPEG/PNG.",
  "timestamp": "2025-12-20T14:30:45.123Z"
}
```

### AWS API Error

```json
{
  "success": true,
  "frame_id": 45,
  "timestamp": "2025-12-20T14:31:00.000Z",
  
  "faces_recognized": [
    {
      "track_id": 7,
      "name": "Unknown",
      "confidence": 0,
      "source": "error",
      "details": {
        "error": "AWS Rekognition unavailable",
        "cached_from_earlier": true,
        "fallback": "Used previous recognition"
      }
    }
  ],
  
  "warning": "AWS service temporarily unavailable. Using cached results."
}
```

### Uninitialized Pipeline

```json
{
  "success": false,
  "error": "Pipeline not initialized. Check AWS credentials in .env file.",
  "details": {
    "check_items": [
      "AWS_ACCESS_KEY_ID in .env",
      "AWS_SECRET_ACCESS_KEY in .env",
      "AWS_REGION in .env",
      "AWS_COLLECTION_ID in .env",
      "Internet connectivity to AWS"
    ]
  }
}
```

---

## 📊 Summary: How All 4 Modules Work Together

```
SINGLE FRAME PROCESSING:

┌──────────────────────────────────────────────────┐
│ FRAME INPUT (Base64 JPEG)                        │
└─────────────────┬────────────────────────────────┘
                  │
                  ├─────────────────────────────────────────┐
                  │                                         │
                  ▼                                         ▼
        ┌─────────────────┐                    ┌──────────────────┐
        │ MODULE 1 & 3:   │                    │ MODULE 2:        │
        │ IDENTITY &      │                    │ VEHICLE & ANPR   │
        │ ATTENDANCE      │                    │                  │
        │                 │                    │                  │
        │ ✅ YOLOv8 detect│                    │ ✅ YOLOv8 detect│
        │ ✅ Face crop    │                    │ ✅ Plate crop   │
        │ ✅ AWS search   │                    │ ✅ EasyOCR read │
        │ ✅ Cache check  │                    │ ✅ Log to DB    │
        │ ✅ Log to DB    │                    │                  │
        │                 │                    │                  │
        │ Output:         │                    │ Output:          │
        │ faces_recognized│                    │ vehicles_detected│
        └────────┬────────┘                    └─────────┬────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ MODULE 4:            │
                          │ OCCUPANCY COUNTING   │
                          │                      │
                          │ ✅ Centroid track   │
                          │ ✅ Line crossing    │
                          │ ✅ Entry/exit count │
                          │ ✅ Log to DB        │
                          │                      │
                          │ Output:              │
                          │ occupancy            │
                          │ entries, exits       │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ COMBINE RESULTS      │
                          │ Build JSON response  │
                          │ Log to system_metrics│
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ RESPONSE TO FRONTEND │
                          │ All 4 modules data   │
                          │ in single JSON       │
                          └──────────────────────┘
```

---

**🎉 Complete integration of 4 production modules in single frame!**

