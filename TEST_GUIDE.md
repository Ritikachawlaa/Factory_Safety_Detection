# 🧪 Quick Test Guide - Face Detection Fixes

## What Was Fixed

✅ **Face Recognition Threshold** - Changed 0.6 → 0.75 (more lenient)
✅ **Bounding Boxes** - Now returned from backend through pipeline
✅ **Duplicate Detections** - Same face no longer detected twice

---

## Quick Test Checklist

### Start the System
```bash
# Terminal 1
cd backend
python main_unified.py

# Terminal 2
cd frontend
npm run dev

# Browser
Open http://localhost:5174
Allow camera access
```

### Test 1: Ritika Recognition ⭐ Important
**Action:** Show Ritika to camera at different angles
```
Expected Results:
├─ ✅ Consistent recognition as "Ritika" (not Unknown)
├─ ✅ Box color: GREEN (known person)
├─ ✅ Label: "Track ID: 1 - Ritika"
├─ ✅ Track ID stays same for 30 seconds
└─ ✅ Console shows: "New faces detected: ['Ritika (Track ID: 1)']"

Problems to Look For:
├─ ❌ Sometimes shows as Unknown, sometimes as Ritika
├─ ❌ Multiple boxes visible (2 detections of same person)
├─ ❌ Track ID keeps changing
└─ ❌ No bounding box visible
```

### Test 2: Unknown Face Recognition
**Action:** Show someone not in database
```
Expected Results:
├─ ✅ Orange box (unknown person)
├─ ✅ Label: "Track ID: 2 - Unknown_0"
├─ ✅ Only 1 detection (not duplicated)
└─ ✅ Console shows: "New faces detected: ['unknown_0 (Track ID: 2)']"

NOT:
├─ ❌ 2 different Track IDs for same person
├─ ❌ Multiple orange boxes
```

### Test 3: Two People (Ritika + Unknown)
**Action:** Both in frame together
```
Expected Results:
├─ ✅ 2 separate boxes
├─ ✅ Box 1: Green "Track ID: 1 - Ritika"
├─ ✅ Box 2: Orange "Track ID: 2 - Unknown_0"
├─ ✅ Different Track IDs
└─ ✅ Console: 2 separate new face detections

NOT:
├─ ❌ Same person appearing twice with different IDs
```

### Test 4: Duration Check
**Action:** Keep Ritika in view for 30+ seconds
```
Expected Results:
├─ ✅ Track ID remains 1 for full duration
├─ ✅ Label consistently shows "Track ID: 1"
├─ ✅ Leave frame → after 30s timeout → database logged
└─ ✅ Return → new Track ID 2 created

NOT:
├─ ❌ Track ID changing every frame
├─ ❌ New Track ID immediately
```

---

## Debugging

### Issue: Still Showing Duplicate Detections

**Check Backend Console:**
```
🔍 DEBUG: Found 2 faces
🔍 DEBUG: Removing duplicate face, distance=15.3px
🔍 DEBUG: After deduplication: 1 faces
```

If you don't see "Removing duplicate", the faces are far enough apart (different people).

**Solution:** Adjust threshold in `backend/models/face_model.py`:
```python
if distance < 50:  # Try lowering to 40 or raising to 60
```

### Issue: Ritika Still Shows as Unknown Sometimes

**Check Console for Distance Values:**
```
🔍 DEBUG: vs Ritika: distance=0.72
❓ UNKNOWN FACE (distance=0.72 > threshold=0.75)
```

If distance is 0.72-0.80, increase threshold:
```python
self.face_distance_threshold = 0.80  # File: backend/models/face_model.py:17
```

### Issue: No Bounding Boxes Visible

**Check:** Right-click page → Inspect → Console tab
```
Look for errors like:
- "Cannot read property 'bbox'"
- "face_bboxes is undefined"
- "Cannot read property 'x' of null"
```

**Check Backend Logs:**
```
Face should be returned with bbox in response:
📤 /api/detect RESPONSE: faces=1
   ├─ Track ID: 1, Name: Ritika, Known: True, Bbox: {'x': 442, 'y': 325, 'w': 258, 'h': 258}
```

If bbox is None, check pipeline.

---

## Quick Fixes

### Clear Session Storage (if stuck)
```javascript
// In browser console (F12)
localStorage.clear()
sessionStorage.clear()
location.reload()
```

### Restart Clean
```bash
# Kill processes
Ctrl+C in both terminals

# Clear Python cache
cd backend
del -r __pycache__

# Restart
python main_unified.py
```

---

## What Each Section Does

### Backend Console Output

```
📥 /api/detect REQUEST              # New frame received
   face_detection=True
   face_recognition=True
   Frame shape: (720, 1280, 3)

[PIPELINE] Detected 2 faces         # Raw face detection
[PIPELINE] Running face recognition...

🔍 DEBUG: Found 2 faces              # Detection pipeline
🔍 DEBUG: Removing duplicate face, distance=15.3px
🔍 DEBUG: After deduplication: 1 faces

vs Ritika: distance=0.65 < 0.75     # Embedding comparison
✅ RECOGNIZED: Ritika               # Result

📤 /api/detect RESPONSE: faces=1    # Response sent
   ├─ Track ID: 1, Name: Ritika, Known: True
```

### Frontend Console Output

```javascript
✅ New faces detected: ['Ritika (Track ID: 1)']
   // From PersonIdentityModule.tsx

Canvas: Drawing bbox at (442, 325, 258, 258)
Label: "Track ID: 1 - Ritika"
Color: Green (is_known = true)
```

---

## Pass/Fail Criteria

### ✅ PASS
- [ ] Ritika consistently recognized (not Unknown)
- [ ] Only 1 box per person (no duplicates)
- [ ] Bounding boxes visible on canvas
- [ ] Correct colors (green=known, orange=unknown)
- [ ] Track ID persists for 30 seconds
- [ ] No console errors
- [ ] No duplicate console messages

### ❌ FAIL
- [ ] Same person detected twice
- [ ] Ritika sometimes Unknown
- [ ] No bounding boxes
- [ ] Wrong colors
- [ ] Track ID changes every frame
- [ ] Console errors

---

## Before & After Visual

### Before (Broken)
```
Ritika shows to camera
└─ Visual: Orange box "Task ID: 2 - Unknown_0"
└─ Console: 2 detections (Unknown_0 + Ritika)
└─ Problem: Same person, 2 different detections!
```

### After (Fixed)
```
Ritika shows to camera
└─ Visual: Green box "Track ID: 1 - Ritika"
└─ Console: 1 detection (Ritika)
└─ Deduplication: Removed duplicate detection
└─ Result: Consistent, correct identification!
```

---

## Monitoring Commands

### Watch backend logs live
```bash
# Terminal with backend running
# Scroll up/down to see detection logs in real-time
```

### Check database after 30s timeout
```bash
sqlite3 "backend/factory_ai.db"
SELECT track_id, name, is_known, session_duration FROM face_sessions ORDER BY first_seen DESC LIMIT 5;
```

Expected: 1 entry per face per 30-second session, not multiple per frame.

---

## Performance Expectations

- **Frame Processing**: 500ms (2 FPS)
- **Face Detection**: 100-200ms
- **Face Recognition**: 300-400ms
- **Total**: ~500ms per frame = smooth real-time display

If slower, check:
- CPU usage
- Browser tab count (close other tabs)
- Camera resolution (might be too high)

---

## Success Indicators

When everything works:
1. **Immediate**: Face detected with bounding box within 500ms
2. **Consistent**: Same person keeps same Track ID
3. **Accurate**: Ritika shows green box, unknowns show orange
4. **Clean**: No duplicate detections
5. **Logged**: Database shows 1 entry per session

---

## Need Help?

Check documentation files:
- `BUG_FIXES_APPLIED.md` - What was fixed
- `DUPLICATE_FACE_FIX.md` - Deduplication details
- `SESSION_TRACKING_GUIDE.md` - How sessions work
- `QUICK_START_SESSION_TRACKING.md` - Setup guide

**Ready to test!** 🚀
