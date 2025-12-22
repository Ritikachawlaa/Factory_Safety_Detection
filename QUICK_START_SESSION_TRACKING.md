# 🚀 Quick Start: Session-Based Face Detection System

## System Requirements
- Python 3.8+ with FastAPI
- Node.js 16+ with npm
- OpenCV + DeepFace models loaded
- SQLite database (auto-created)
- Webcam access

---

## 📦 Installation

### Backend Setup
```bash
cd "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\backend"

# Install dependencies (if needed)
pip install -r requirements.txt

# Run the backend
python main_unified.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Frontend Setup
```bash
cd "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\frontend"

# Install dependencies (if needed)
npm install

# Run dev server
npm run dev
```

**Expected output:**
```
VITE v5.4.19  ready in 123 ms

➜  Local:   http://localhost:5174/
```

---

## 🎮 Using the System

### Step 1: Open Browser
Navigate to: **http://localhost:5174**

### Step 2: Enable Face Detection
Click on "Person Identity Module" (or main face detection view)

### Step 3: Allow Camera Access
Browser will ask for camera permission → Click "Allow"

### Step 4: Show Your Face to Camera
You should see:
- ✅ Bounding box around face
- ✅ Label: `Track ID: 1 - Ritika`
- ✅ Color: Green (if in employee database) or Orange (if unknown)
- ✅ Confidence: 95.0%

### Step 5: Move Face Around (Stay in View)
- Same track_id should persist for 30 seconds
- When you leave the frame:
  - After 30 seconds: Session ends, 1 database entry created
  - Re-entering frame: New track_id assigned (e.g., Track ID: 2)

---

## 📊 Real-Time Monitoring

### Watch Backend Logs
```
📥 /api/detect REQUEST
   face_detection=True
   face_recognition=True
   Frame shape: (720, 1280, 3)

[PIPELINE] Detected 1 faces
[PIPELINE] Running face recognition...
✅ RECOGNIZED: Ritika

📤 /api/detect RESPONSE: faces=1, active_sessions=1
   ├─ Track ID: 1, Name: Ritika, Known: True
```

### Check Database
```bash
# Open database in new terminal
sqlite3 "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\backend\factory_ai.db"

# View all recorded sessions
SELECT track_id, name, is_known, first_seen, last_seen, session_duration FROM face_sessions;

# View only unknown faces
SELECT * FROM face_sessions WHERE is_known = 0;

# Count sessions per person
SELECT name, COUNT(*) as sessions FROM face_sessions GROUP BY name;
```

---

## 🎯 What You Should See

### Canvas Display
```
╔════════════════════════════════════════╗
║  Track ID: 1 - Ritika                  ║ ← Green (known)
║  ┌──────────────────────────────────┐  ║
║  │  Confidence: 95.0%               │  ║
║  │  [Bounding Box around face]      │  ║
║  │                                  │  ║
║  └──────────────────────────────────┘  ║
║                                        ║
║  Track ID: 2 - Unknown_0               ║ ← Orange (unknown)
║  ┌──────────────────┐                  ║
║  │ Confidence: 85%  │                  ║
║  └──────────────────┘                  ║
╚════════════════════════════════════════╝
```

### Detection History Table
```
Track ID | Name       | Type     | Confidence | Last Seen   | Status
---------|------------|----------|------------|-------------|----------
1        | Ritika     | Employee | 95.0%      | 10:05:32    | Authorized
2        | Unknown_0  | Unknown  | 85.0%      | 10:05:42    | Unknown
```

---

## ⏱️ Session Timeline

### Known Face (Ritika)
```
T=0s:    Face enters frame
         → Track ID 1 created
         → Status: ACTIVE

T=5s:    Face still visible
         → Track ID 1 reused
         → last_seen updated
         → Status: ACTIVE

T=15s:   Face leaves frame
         → Status: WAITING (30s timeout)

T=45s:   Timeout reached
         → Log to database:
           {track_id: 1, name: "Ritika", duration: 15s, is_known: true}
         → Status: LOGGED

T=50s:   Face enters again
         → Track ID 2 created (new session!)
         → Status: ACTIVE
```

### Unknown Face
```
T=0s:    Unknown face detected
         → Track ID 2 created
         → Snapshot saved: /snapshots/unknown_0_*.jpg
         → Status: ACTIVE

T=10s:   Face still visible
         → Track ID 2 reused
         → NO new snapshot (only on first detection)
         → Status: ACTIVE

T=40s:   Face leaves
         → Wait 30s timeout
         → Log to database:
           {track_id: 2, name: "Unknown_0", duration: 10s, 
            is_known: false, snapshot_path: "/snapshots/..."}
         → Status: LOGGED
```

---

## 🔧 Configuration

### Change Session Timeout (Advanced)
Edit `backend/main_unified.py`:
```python
FACE_SESSION_TIMEOUT = 30  # Change to 60 for 60 seconds
```

### Change Detection Sensitivity
Edit `backend/services/detection_pipeline.py`:
```python
RECOGNITION_THRESHOLD = 0.6  # Lower = more sensitive, higher = stricter
```

### Change Canvas Colors
Edit `frontend/src/components/WebcamFeed.tsx`:
```typescript
const color = face.is_known ? '#00ff00' : '#ff8800';  // Green/Orange
// Change to:
const color = face.is_known ? '#0099ff' : '#ff6600';  // Blue/Red
```

---

## 🐛 Troubleshooting

### Issue: No Face Detected
**Problem:** Bounding box not showing even with face in view
```
Checklist:
□ Camera permission granted?
□ Lighting adequate?
□ Face centered in frame?
□ Face detection enabled in UI?
→ Check browser console for errors
→ Check backend logs for warnings
```

### Issue: Track ID Changes Every Frame
**Problem:** Should reuse same ID, but changing
```
Check:
□ Call to update_face_session() is working?
□ face_sessions dict being maintained?
□ Response includes proper track_id?
→ Add console.log() in WebcamFeed.tsx
→ Check API response in Network tab
```

### Issue: Database Entry Per Frame (Not Per Session)
**Problem:** Too many entries in face_sessions table
```
Solution:
□ Verify cleanup_expired_sessions() called
□ Check FACE_SESSION_TIMEOUT = 30
□ Ensure log_face_session() only on expiry
→ Query: SELECT COUNT(*) FROM face_sessions
→ Should be ~1 per person per 30 seconds
```

### Issue: Unknown Face Has Multiple Snapshots
**Problem:** Same face saved multiple times
```
Fix in update_face_session():
- Save snapshot only on NEW session (not updates)
- Check: if not existing_track_id and not is_known
- Then: save snapshot to /snapshots/ folder
```

### Issue: Performance Slow (High Latency)
**Problem:** Frames not processing fast enough
```
Optimize:
□ Reduce frame resolution
□ Enable only needed features
□ Check Face Detection settings (aggressive vs standard)
→ Reduce pipeline.py detection resolution
→ Disable unused modules
```

---

## 📈 Performance Metrics

### Expected Performance
- **Frame Rate**: 2-3 FPS per face (500ms latency)
- **Database Insert**: ~10ms per expired session
- **Memory Usage**: ~100MB baseline + 10MB per active session
- **Disk Usage**: ~500KB per unknown face snapshot

### Monitoring
```bash
# Watch memory usage
while ($true) { 
  Get-Process python | Select-Object -Property Name, WorkingSet
  Start-Sleep -Seconds 1
}

# Watch database growth
while ($true) {
  $size = (Get-Item "factory_ai.db").Length / 1MB
  Write-Host "DB Size: $($size) MB"
  Start-Sleep -Seconds 5
}
```

---

## 🧪 Test Scenarios

### Test 1: Persistent Track ID
```
1. Show face for 5 seconds
2. Check: Track ID stays same (e.g., Track ID: 1)
3. Result: ✅ PASS if ID never changes
```

### Test 2: Session Expiration
```
1. Show face
2. Leave frame
3. Wait 30+ seconds
4. Check database: SELECT * FROM face_sessions
5. Result: ✅ PASS if 1 entry with correct duration
```

### Test 3: Multiple Faces
```
1. Show face A (Track ID: 1)
2. Add face B to frame (Track ID: 2)
3. Both visible → both have different IDs
4. Remove face A → Track ID 1 times out after 30s
5. Result: ✅ PASS if proper isolation and timeouts
```

### Test 4: Unknown Face Tracking
```
1. Show unknown face
2. Check for snapshot saved
3. Leave frame 30s
4. Check database for snapshot_path
5. Result: ✅ PASS if snapshot exists and path recorded
```

### Test 5: Employee Matching
```
1. Show known face (Ritika)
2. Check: is_known = true, color = green
3. Check: employee_id populated
4. Check: employee_id matches employee database
5. Result: ✅ PASS if all employee data correct
```

---

## 📝 API Testing with CURL

### Test Face Detection
```bash
# Get a test frame first (or use real frame)
curl -X POST http://localhost:8000/api/detect \
  -H "Content-Type: application/json" \
  -d '{
    "frame": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "enabled_features": {
      "face_detection": true,
      "face_recognition": true
    }
  }' | jq '.detected_faces'
```

### Check Status
```bash
curl http://localhost:8000/api/diagnostic | jq '.modules.module_1'
```

### Reset System
```bash
curl -X POST http://localhost:8000/api/reset
```

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/main_unified.py` | API endpoints + face session management |
| `backend/services/detection_pipeline.py` | Face detection/recognition pipeline |
| `backend/database_models.py` | Database schema definitions |
| `frontend/src/components/WebcamFeed.tsx` | Canvas drawing + label display |
| `frontend/src/pages/PersonIdentityModule.tsx` | Detection history + cards |
| `frontend/src/hooks/useSmartFaceDetection.ts` | Track ID persistence logic |

---

## ✅ Verification Checklist

Before considering the system "working":

- [ ] Backend starts without errors
- [ ] Frontend builds without TypeScript errors
- [ ] Camera works in browser
- [ ] Face detected with bounding box
- [ ] Track ID shows above bounding box
- [ ] Track ID persists for consecutive frames
- [ ] Track ID changes when person leaves and returns
- [ ] Canvas color: Green for known, Orange for unknown
- [ ] Detection history table updates
- [ ] Database has 1 entry per session (check after 30s)
- [ ] Employee names show for known faces
- [ ] Unknown faces display "Unknown_X"

---

## 🎓 Learning Resources

- **Session Management**: See SESSION_TRACKING_GUIDE.md
- **API Design**: See IMPLEMENTATION_STATUS_SESSION_TRACKING.md
- **Visual Design**: See VISUAL_FACE_DETECTION_GUIDE.md
- **Architecture**: See backend/SYSTEM_ARCHITECTURE.md

---

## 💡 Tips & Tricks

### Faster Testing
- Use lower resolution frames initially (faster processing)
- Disable features you don't need
- Set shorter FACE_SESSION_TIMEOUT for quicker testing

### Better Face Recognition
- Good lighting (avoid backlighting)
- Face centered in frame
- Face at least 50x50 pixels
- Direct eye contact with camera

### Database Debugging
```sql
-- See all sessions
SELECT * FROM face_sessions;

-- See how many times each person visited
SELECT name, COUNT(*) as visits, 
       SUM(session_duration) as total_seconds
FROM face_sessions 
GROUP BY name;

-- See visits today
SELECT name, first_seen, session_duration
FROM face_sessions 
WHERE DATE(first_seen) = DATE('now');

-- Delete test data
DELETE FROM face_sessions WHERE name = 'Unknown_0';
```

---

## 🚀 Ready?

```bash
# Terminal 1: Backend
cd backend
python main_unified.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Browser
Open http://localhost:5174
Allow camera access
Show your face!
```

**Enjoy! 🎉**
