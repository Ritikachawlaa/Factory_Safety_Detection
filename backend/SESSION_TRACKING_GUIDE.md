# 🎯 Session-Based Face Tracking System - Complete Guide

## Overview
The system has been converted from **per-frame face tracking** to **session-based persistent tracking** with database logging.

## Key Changes Implemented

### 1. Backend Refactoring (main_unified.py)

#### Session Management System
```python
# BEFORE: Per-frame tracking
face_tracking = {}  # New ID every frame
face_counter = 0
FACE_TIMEOUT = 5

# AFTER: Session-based tracking
face_sessions = {}  # {track_id: {name, employee_id, first_seen, last_seen, is_known}}
track_id_counter = 0
FACE_SESSION_TIMEOUT = 30  # Sessions live for 30 seconds after last detection
```

#### Database Table for Session Logging
```sql
CREATE TABLE face_sessions (
    session_id INTEGER PRIMARY KEY,
    track_id INTEGER,
    name TEXT,
    employee_id TEXT,
    is_known BOOLEAN,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    session_duration INTEGER,
    camera_id TEXT,
    snapshot_path TEXT
)
```

### 2. New Helper Functions

#### `get_next_track_id()`
- Returns unique persistent `track_id` for each face
- Increments global counter
- **Never reused** for same face session

#### `cleanup_expired_sessions()`
- Called at start of every `/api/detect` request
- Checks all active sessions
- If session hasn't been detected for 30+ seconds:
  - Logs session to database via `log_face_session()`
  - Removes from active memory
- **Prevents per-frame logging** - only logs when session expires

#### `log_face_session(session)`
- Inserts completed session into `face_sessions` table
- Records:
  - `track_id`: Persistent identifier
  - `name`: Person's name (or "Unknown_X")
  - `employee_id`: From employee database (if matched)
  - `is_known`: Boolean (True if employee, False if unknown)
  - `first_seen`: Session start timestamp
  - `last_seen`: Session end timestamp
  - `session_duration`: Duration in seconds
  - `snapshot_path`: Path to captured image (for unknowns)

#### `match_face_with_employee(face_name)`
- Queries `employees` table for matching face
- Returns employee record if found
- Returns `None` if not found
- **Used to populate `employee_id` field**

#### `update_face_session(face_name, is_known, confidence, bbox)`
- Core session management function
- **Reuses `track_id`** if same face detected again
- Creates new session with new `track_id` if new face
- Updates `last_seen` timestamp (keeps session alive)
- Matches with employee database if `is_known=True`

### 3. API Response Model Update

```python
# BEFORE
class DetectedFace(BaseModel):
    face_id: int  # ❌ Per-frame ID, changes every frame
    name: str
    confidence: float
    bbox: Optional[Dict[str, int]]
    recognized: bool

# AFTER
class DetectedFace(BaseModel):
    track_id: int  # ✅ Persistent across session
    name: str
    employee_id: Optional[str]  # ✅ From employee database
    confidence: float
    bbox: Optional[Dict[str, int]]
    is_known: bool  # ✅ Renamed from 'recognized'
```

### 4. /api/detect Endpoint Updates

```python
@app.post("/api/detect")
async def unified_detection(request: DetectionRequest):
    # 1. Cleanup expired sessions (logs to DB)
    cleanup_expired_sessions()
    
    # 2. Detect faces in frame
    result = pipeline.process_frame(frame, features_dict)
    
    # 3. For each detected face:
    #    - Call update_face_session() to get persistent track_id
    #    - If known: fetch employee_id from database
    #    - Add to response with track_id (NOT face_id)
    
    # 4. Return detected_faces with track_id field
```

### 5. Frontend Updates

#### WebcamFeed.tsx
```typescript
// Canvas drawing label
const labelText = `Track ID: ${face.track_id} - ${face.name}`;  // ✅ Updated

// Drawing color based on recognition status
const color = face.is_known ? '#00ff00' : '#ff8800';  // ✅ Uses is_known
```

#### PersonIdentityModule.tsx
```typescript
// Detection cards
face.track_id  // ✅ Display persistent ID
face.is_known  // ✅ Check if known/unknown
face.employee_id  // ✅ Show employee info if matched
```

#### useSmartFaceDetection.ts Hook
```typescript
interface DetectedFace {
  track_id: number;  // ✅ Was face_id
  name: string;
  is_known: boolean;  // ✅ Was recognized
  bbox?: { x: number; y: number; w: number; h: number };
}

// Track by track_id instead of face_id
const currentFacesMap = new Map(currentFaces.map(f => [f.track_id, f]));
```

## Behavioral Changes

### Session Lifecycle

```
Frame 1: Face detected → create session with track_id=1
Frame 2: Same face → reuse track_id=1, update last_seen
Frame 3: Same face → reuse track_id=1, update last_seen
...
Frame 30s later: No face detected, session expires
  → log_face_session() writes 1 record to DB
  → Remove from active memory
  
Next occurrence: Same face re-detected → create new session with track_id=2
```

### Database Logging

**BEFORE (❌ Wrong):**
- Every frame → 1 database entry
- 30 FPS = 30 entries per second per person
- Massive log bloat, difficult to analyze

**AFTER (✅ Correct):**
- Per session → 1 database entry
- 30-second session = 1 entry
- Clean logs showing person presence time window
- Easy to analyze: "Person was here from 10:05:32 to 10:06:02"

### Unknown Face Handling

```
First detection of unknown face:
  → track_id=1, is_known=False
  → name="Unknown_0"
  → snapshot saved to disk
  → session created

Next detection of same unknown face:
  → Reuse track_id=1 (same person!)
  → is_known=False (still unknown)
  → name="Unknown_0" (consistent)
  → NO new snapshot taken
  → session last_seen updated

After 30s timeout:
  → Log 1 session with snapshot_path populated
```

## Testing Checklist

- [ ] Face detection works with persistent track_id
- [ ] Same face in consecutive frames reuses track_id
- [ ] Different faces get different track_ids
- [ ] Canvas displays "Track ID: X - Name" labels
- [ ] Unknown faces create snapshots only once
- [ ] Database logging shows 1 entry per session (not per frame)
- [ ] Frontend shows detection history in table
- [ ] Session cleanup runs properly (no memory leaks)

## Important Notes

1. **Track ID Persistence**: Same track_id used throughout 30-second session
2. **Database Logging**: Only happens when session expires (via cleanup_expired_sessions)
3. **Employee Matching**: Happens via match_face_with_employee() using face name
4. **Snapshot Capture**: Should only happen on first unknown face detection
5. **Session Timeout**: 30 seconds - adjust FACE_SESSION_TIMEOUT if needed

## API Response Example

### Request
```json
{
  "frame": "base64_encoded_image",
  "enabled_features": {
    "face_detection": true,
    "face_recognition": true
  }
}
```

### Response
```json
{
  "detected_faces": [
    {
      "track_id": 1,
      "name": "Ritika",
      "employee_id": "EMP001",
      "confidence": 0.95,
      "bbox": {"x": 442, "y": 325, "w": 258, "h": 258},
      "is_known": true
    },
    {
      "track_id": 2,
      "name": "Unknown_0",
      "employee_id": null,
      "confidence": 0.85,
      "bbox": {"x": 100, "y": 150, "w": 80, "h": 80},
      "is_known": false
    }
  ],
  "active_sessions": 2,
  "faces_detected": 2,
  "faces_recognized": 1
}
```

## Frontend Display

### Canvas Overlay
```
┌─────────────────────────────────────────┐
│ Track ID: 1 - Ritika                    │ ← Green label (known)
│  ┌───────────────────────┐              │
│  │                       │              │
│  │   [Face Detected]     │              │
│  │                       │              │
│  └───────────────────────┘              │
│                                         │
│ Track ID: 2 - Unknown_0                 │ ← Orange label (unknown)
│  ┌─────────────────┐                    │
│  │   [Unknown Face]│                    │
│  └─────────────────┘                    │
└─────────────────────────────────────────┘
```

### Detection History Table
| Track ID | Name | Type | Confidence | Last Seen | Status |
|----------|------|------|-----------|-----------|--------|
| 1 | Ritika | Employee | 95.0% | 10:05:45 | Authorized |
| 2 | Unknown_0 | Unknown | 85.0% | 10:05:42 | Unknown |

## Troubleshooting

**Issue: Track IDs keep changing every frame**
- Check: `/api/detect` response should have same track_id for consecutive frames
- Fix: Ensure update_face_session() is reusing track_ids

**Issue: Database has too many entries**
- Check: Sessions should expire after 30 seconds
- Fix: Verify cleanup_expired_sessions() is being called

**Issue: Bounding boxes not showing**
- Check: face_bboxes array is being returned from pipeline
- Fix: Verify pipeline returns proper bbox format: {x, y, w, h}

**Issue: Unknown faces have multiple snapshots**
- Check: Snapshot logic in update_face_session()
- Fix: Only save on is_known=False for new sessions, not on updates
