# 🧪 FRONTEND TESTING GUIDE
# Complete 12-Feature Testing Checklist for AI Video Analytics System

**Document Version**: 1.0  
**Last Updated**: December 14, 2025  
**Purpose**: Step-by-step testing guide for all 12 AI features

---

## 📋 TABLE OF CONTENTS

1. [Pre-Testing Setup](#1-pre-testing-setup)
2. [Test Environment Verification](#2-test-environment-verification)
3. [Feature Testing Checklist (12 Tests)](#3-feature-testing-checklist)
4. [Expected Results Reference](#4-expected-results-reference)
5. [Troubleshooting Guide](#5-troubleshooting-guide)
6. [Test Report Template](#6-test-report-template)

---

## 1️⃣ PRE-TESTING SETUP

### 1.1 Start Backend Server

**Terminal 1 - Backend**:
```powershell
cd "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\backend"
python main_unified.py
```

**Expected Output**:
```
🚀 Loading AI Models...
✅ Helmet Detection Model Loaded
✅ Box Detection Model Loaded
✅ Face Recognition System Ready (lazy loading)
✅ Vehicle Detection Model Loaded
✅ All Models Loaded Successfully
✅ System Ready - Server Starting...
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

**✅ Backend Status**: Running on http://localhost:8000

---

### 1.2 Start Frontend Server

**Terminal 2 - Frontend**:
```powershell
cd "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\frontend"
ng serve
```

**Expected Output**:
```
✔ Browser application bundle generation complete.
** Angular Live Development Server is listening on localhost:4200 **
✔ Compiled successfully.
```

**✅ Frontend Status**: Running on http://localhost:4200

---

### 1.3 Open Testing Interface

1. Open Chrome or Edge browser
2. Navigate to: **http://localhost:4200/unified-live**
3. You should see the "Unified AI Detection System" page

**Page Elements to Verify**:
- ✅ Video preview area (black initially)
- ✅ "Start Webcam" button
- ✅ Feature toggles section (11 checkboxes)
- ✅ Statistics dashboard (4 panels)

---

## 2️⃣ TEST ENVIRONMENT VERIFICATION

### ✅ Pre-Test Checklist

| Item | Status | How to Verify |
|------|--------|---------------|
| **Backend Running** | ⬜ | Visit http://localhost:8000/health - should return JSON |
| **Frontend Compiled** | ⬜ | Visit http://localhost:4200 - should load Angular app |
| **Webcam Available** | ⬜ | Click "Start Webcam" - should prompt for camera access |
| **CORS Working** | ⬜ | Open browser console (F12) - no CORS errors |
| **API Connectivity** | ⬜ | Open Network tab in DevTools - see /api/detect calls |

### Quick Backend Test

Open browser to: http://localhost:8000/features

**Expected Response** (JSON with 11 features):
```json
{
  "features": [
    {"id": 1, "name": "Human Detection", ...},
    {"id": 2, "name": "Vehicle Detection", ...},
    ...
  ]
}
```

---

## 3️⃣ FEATURE TESTING CHECKLIST

### 📹 Webcam Activation Test

**Test Steps**:
1. Click **"Start Webcam"** button
2. Allow camera access when prompted

**Expected Results**:
- ✅ Video stream appears in preview area
- ✅ Button changes to "Stop Webcam"
- ✅ Detection starts automatically (see FPS counter)
- ✅ Console shows no errors

**Pass Criteria**: Live video feed visible  
**Status**: ⬜ PASS / ⬜ FAIL

---

### 🧍 FEATURE 1: Human Detection

**Model Used**: `best_helmet.pt` (YOLO custom)  
**Test Scenario**: Detect people in camera view

#### Test Steps:
1. Enable **"Human Detection"** toggle (should be ON by default)
2. Position yourself in front of the camera
3. Move around to test continuous detection

#### Expected Results:
- ✅ **People Count** stat card shows count (1 or more)
- ✅ Count updates in real-time as you move
- ✅ Count decreases to 0 when you leave frame
- ✅ Bounding boxes drawn around detected people (if canvas overlay enabled)

#### Expected Values:
- **People Count**: 1-5 (depending on people in frame)
- **API Field**: `detectionResult.people_count`
- **Update Frequency**: ~2.5 FPS (every 400ms)

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 🚗 FEATURE 2: Vehicle Detection

**Model Used**: `yolo11n.pt` (YOLO COCO pretrained)  
**Test Scenario**: Detect cars, motorcycles, buses, trucks

#### Test Steps:
1. Enable **"Vehicle Detection"** toggle
2. Show a vehicle to the camera (options):
   - Show a toy car/vehicle
   - Point camera out window at road/parking lot
   - Show vehicle image on phone/tablet

#### Expected Results:
- ✅ **Vehicle Count** stat card shows count
- ✅ Vehicle type displayed (car, motorcycle, bus, truck)
- ✅ Count updates when new vehicles appear

#### Expected Values:
- **Vehicle Count**: 0 (no vehicles) to 10+ (busy road)
- **API Field**: `detectionResult.vehicle_count`
- **Vehicle Types**: `detectionResult.vehicles[].type`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### ⛑️ FEATURE 3: Helmet/PPE Detection

**Model Used**: `best_helmet.pt` (YOLO custom)  
**Test Scenario**: Detect helmets and safety violations

#### Test Steps:
1. Enable **"Helmet/PPE Detection"** toggle
2. Test WITHOUT helmet:
   - Stand in frame showing your head clearly
   - Observe violation count
3. Test WITH helmet/hat:
   - Wear a hardhat, helmet, or cap
   - Observe violation count decrease

#### Expected Results:
- ✅ **Helmet Violations** stat card shows count
- ✅ **PPE Compliance Rate** shows percentage
- ✅ Violations detected when head visible without helmet
- ✅ Compliance increases when wearing helmet/hat

#### Expected Values:
- **Helmet Violations**: 0 (wearing helmet) to 5 (multiple people without)
- **PPE Compliance**: 0% to 100%
- **API Fields**: 
  - `detectionResult.helmet_violations`
  - `detectionResult.ppe_compliance_rate`
  - `detectionResult.helmet_count`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### ⏱️ FEATURE 4: Loitering Detection

**Model Used**: Tracking logic (no model)  
**Test Scenario**: Detect person staying in area > 10 seconds

#### Test Steps:
1. Enable **"Loitering Detection"** toggle
2. Stand still in front of camera for 15 seconds
3. Move significantly and observe reset

#### Expected Results:
- ✅ **Loitering Detected** badge appears after ~10 seconds
- ✅ **Loitering Count** shows number of loiterers
- ✅ Badge turns red when detected
- ✅ Count resets when you move away

#### Expected Values:
- **Loitering Detected**: `false` (moving) or `true` (still > 10s)
- **Loitering Count**: 0 to 5
- **Time Threshold**: 10 seconds (configurable)
- **API Fields**:
  - `detectionResult.loitering_detected`
  - `detectionResult.loitering_count`
  - `detectionResult.loitering_groups`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 👷 FEATURE 5: Labour Count

**Model Used**: Aggregation from helmet model  
**Test Scenario**: Count total workers/people

#### Test Steps:
1. Enable **"Labour Count"** toggle
2. Have multiple people appear in frame (1-5)
3. Verify count matches visible people

#### Expected Results:
- ✅ **Labour Count** matches people count
- ✅ Updates as people enter/leave frame
- ✅ Same value as People Count (both from helmet model)

#### Expected Values:
- **Labour Count**: 0 to 10+
- **API Field**: `detectionResult.labour_count`
- **Note**: Should equal `people_count`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 👥 FEATURE 6: Crowd Density Detection

**Model Used**: Area calculation logic  
**Test Scenario**: Detect crowd formation

#### Test Steps:
1. Enable **"Crowd Density"** toggle
2. Single person: Observe "Low" density
3. Multiple people close together: Observe density increase
4. Have 3-5 people group together (if possible)

#### Expected Results:
- ✅ **Crowd Detected** badge appears with 5+ people
- ✅ **Crowd Density Level** shows: Low / Medium / High
- ✅ Density increases with more people
- ✅ Badge color changes (green → yellow → red)

#### Expected Values:
- **Crowd Detected**: `false` (< 5 people) or `true` (≥ 5)
- **Crowd Density**: "low", "medium", "high"
- **Occupied Area**: 0.0 to 1.0 (percentage)
- **API Fields**:
  - `detectionResult.crowd_detected`
  - `detectionResult.crowd_density`
  - `detectionResult.occupied_area`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 📦 FEATURE 7: Box Counting

**Model Used**: `best_product.pt` (YOLO custom)  
**Test Scenario**: Count boxes or products

#### Test Steps:
1. Enable **"Box Counting"** toggle
2. Show boxes/objects to camera (options):
   - Physical boxes/packages
   - Books/rectangular objects
   - Product images on screen

#### Expected Results:
- ✅ **Box Count** stat card shows detected boxes
- ✅ Count updates as boxes appear/disappear
- ✅ Tracking IDs assigned (if visible)

#### Expected Values:
- **Box Count**: 0 to 20+
- **API Fields**:
  - `detectionResult.box_count`
  - `detectionResult.boxes[]`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### ➡️ FEATURE 8: Line Crossing Detection

**Model Used**: Tracking + line logic  
**Test Scenario**: Detect objects crossing virtual line

#### Test Steps:
1. Enable **"Line Crossing"** toggle
2. Enable **"Box Counting"** (required for tracking)
3. Pass an object from top to bottom (or vice versa) across middle of frame
4. Observe crossing counter increment

#### Expected Results:
- ✅ **Total Crossings** counter increments
- ✅ **Line Crossed** badge appears temporarily
- ✅ Crossing detected when object crosses frame center
- ✅ No double-counting same object

#### Expected Values:
- **Total Crossings**: Incremental counter (0, 1, 2, ...)
- **Line Crossed**: `true` (moment of crossing) or `false`
- **Line Position**: 50% of frame height (configurable)
- **API Fields**:
  - `detectionResult.total_crossings`
  - `detectionResult.line_crossed`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 🎯 FEATURE 9: Auto Tracking

**Model Used**: Centroid tracker  
**Test Scenario**: Track objects across frames

#### Test Steps:
1. Enable **"Auto Tracking"** toggle
2. Enable **"Human Detection"** or **"Box Counting"**
3. Move objects/yourself around the frame
4. Observe tracking count

#### Expected Results:
- ✅ **Tracked Objects** counter shows active tracks
- ✅ Count includes people, boxes, vehicles (depending on enabled features)
- ✅ Tracking persists as objects move
- ✅ Count decreases when objects leave frame

#### Expected Values:
- **Tracked Objects**: 0 to 20+
- **API Field**: `detectionResult.tracked_objects`
- **Tracking Method**: Centroid-based

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 🌊 FEATURE 10: Smart Motion Detection

**Model Used**: Background subtraction (MOG2)  
**Test Scenario**: Detect motion validated by AI

#### Test Steps:
1. Enable **"Smart Motion"** toggle
2. Stand still for 3 seconds
3. Wave hands or move suddenly
4. Observe motion detection

#### Expected Results:
- ✅ **Motion Detected** badge appears when moving
- ✅ **Motion Intensity** shows percentage (0-100%)
- ✅ **AI Validated** indicator shows green
- ✅ Motion only detected when objects present (not just shadows)

#### Expected Values:
- **Motion Detected**: `false` (still) or `true` (moving)
- **Motion Intensity**: 0.0 to 1.0 (0% to 100%)
- **AI Validated**: `true` (objects detected) or `false`
- **API Fields**:
  - `detectionResult.motion_detected`
  - `detectionResult.motion_intensity`
  - `detectionResult.ai_validated`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 😊 FEATURE 11: Face Detection

**Model Used**: OpenCV Haar Cascade  
**Test Scenario**: Detect faces in frame

#### Test Steps:
1. Enable **"Face Detection"** toggle
2. Face the camera directly (well-lit area)
3. Turn sideways to test profile detection
4. Have multiple people in frame (if possible)

#### Expected Results:
- ✅ **Faces Detected** counter shows count
- ✅ Count updates as faces appear/disappear
- ✅ Works with frontal faces (best accuracy)
- ✅ May detect profile faces (lower accuracy)

#### Expected Values:
- **Faces Detected**: 0 to 10+
- **Detection Method**: Haar Cascade (fast)
- **API Field**: `detectionResult.faces_detected`

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

### 🔍 FEATURE 12: Face Recognition

**Model Used**: DeepFace FaceNet  
**Test Scenario**: Recognize registered employees

#### Test Steps:
1. Enable **"Face Recognition"** toggle
2. Enable **"Face Detection"** (required)
3. **If employee photos in database**:
   - Face camera
   - Check recognized names list
4. **If no employee photos**:
   - Will show "Unknown" faces

#### Expected Results:
- ✅ **Faces Recognized** shows employee names (if registered)
- ✅ **Unknown Faces** counter shows unregistered faces
- ✅ Recognition updates as faces change
- ✅ Names displayed in list format

#### Expected Values:
- **Faces Recognized**: Array of names ["John Doe", "Jane Smith"]
- **Unknown Faces**: 0 to 10+
- **Database Path**: `backend/database/employees/`
- **API Fields**:
  - `detectionResult.faces_recognized[]`
  - `detectionResult.unknown_faces`

#### Notes:
- First recognition may be slow (DeepFace lazy loading)
- Subsequent recognitions faster
- Requires employee photos in database folder

**Status**: ⬜ PASS / ⬜ FAIL  
**Notes**: _______________________________________

---

## 4️⃣ EXPECTED RESULTS REFERENCE

### Complete API Response Structure

When all features enabled, expect this JSON structure:

```json
{
  "people_count": 2,
  "vehicle_count": 0,
  "helmet_count": 1,
  "helmet_violations": 1,
  "ppe_compliance_rate": 50.0,
  "loitering_detected": false,
  "loitering_count": 0,
  "loitering_groups": [],
  "labour_count": 2,
  "crowd_detected": false,
  "crowd_density": "low",
  "occupied_area": 0.15,
  "box_count": 0,
  "boxes": [],
  "total_crossings": 0,
  "line_crossed": false,
  "tracked_objects": 2,
  "motion_detected": true,
  "motion_intensity": 0.45,
  "ai_validated": true,
  "faces_detected": 2,
  "faces_recognized": ["Unknown"],
  "unknown_faces": 2,
  "vehicles": [],
  "timestamp": "2025-12-14T10:30:45",
  "processing_time_ms": 245
}
```

### Feature Toggle Behavior

| Feature Disabled | Expected Behavior |
|-----------------|-------------------|
| Any feature OFF | Backend skips that detection |
| All features OFF | Returns empty/zero values |
| Only 1 feature ON | Faster processing (less computation) |

---

## 5️⃣ TROUBLESHOOTING GUIDE

### ❌ Webcam Not Starting

**Symptoms**: Black screen, no video feed

**Solutions**:
1. Check browser permissions (camera access)
2. Close other apps using camera (Zoom, Teams, etc.)
3. Refresh page and try again
4. Try different browser (Chrome recommended)
5. Check console for errors (F12)

---

### ❌ No Detection Results

**Symptoms**: All counters show 0, no stats updating

**Solutions**:
1. **Check backend running**: Visit http://localhost:8000/health
2. **Check console errors**: Open DevTools (F12) → Console tab
3. **Check network calls**: DevTools → Network tab → Look for `/api/detect` calls
4. **Verify CORS**: Should see 200 OK responses, not CORS errors
5. **Restart backend**: Stop and restart `main_unified.py`

**Expected Network Call**:
```
POST http://localhost:8000/api/detect
Status: 200 OK
Response: JSON with detection results
```

---

### ❌ Low FPS / Slow Performance

**Symptoms**: FPS < 1, laggy video

**Solutions**:
1. **Disable unused features**: Turn off features not being tested
2. **Reduce resolution**: Modify component to use 320x240
3. **Check CPU usage**: Backend may be maxed out
4. **Close other apps**: Free up system resources
5. **Check frame interval**: Default 400ms (2.5 FPS is normal)

**Performance Expectations**:
- **Good**: 2-3 FPS (all features enabled)
- **Very Good**: 4-5 FPS (few features enabled)
- **Poor**: < 1 FPS (system overloaded)

---

### ❌ CORS Errors

**Symptoms**: Console shows "blocked by CORS policy"

**Solutions**:
1. **Verify backend CORS config**: Check `main_unified.py` lines 14-20
2. **Allowed origins should include**: `http://localhost:4200`
3. **Restart backend** after any CORS changes
4. **Clear browser cache**: Hard refresh (Ctrl + Shift + R)

**Expected CORS Headers**:
```
Access-Control-Allow-Origin: http://localhost:4200
Access-Control-Allow-Methods: POST, GET
```

---

### ❌ Models Not Loading

**Symptoms**: Backend error "Model file not found"

**Solutions**:
1. **Verify model files exist**:
   ```powershell
   cd backend/models
   dir
   # Should see: best_helmet.pt, best_product.pt, yolo11n.pt, yolov8n.pt
   ```
2. **Check file paths**: Ensure models in correct directory
3. **Re-download models** if missing or corrupted
4. **Check Python path**: Run from `backend/` directory

---

### ❌ Face Recognition Not Working

**Symptoms**: Always shows "Unknown" faces

**Solutions**:
1. **Check employee database**: Verify `backend/database/employees/` has photos
2. **Photo format**: Use JPG/PNG images
3. **Photo naming**: `EmployeeName.jpg` (e.g., `John_Doe.jpg`)
4. **First recognition slow**: DeepFace lazy loads (5-10 seconds first time)
5. **Lighting**: Ensure face well-lit and facing camera

**Employee Photo Requirements**:
- Format: JPG, PNG
- Size: Any (will be resized)
- Content: Clear frontal face photo
- Naming: `FirstName_LastName.jpg`

---

### ❌ Line Crossing Not Detecting

**Symptoms**: Objects pass but counter doesn't increment

**Solutions**:
1. **Enable Box Counting**: Line crossing requires tracking (box model)
2. **Cross frame center**: Line is at 50% of frame height
3. **Move slowly**: Fast movements may skip frames
4. **Check direction**: Must cross line completely (top→bottom or bottom→top)

---

### ❌ Angular Not Compiling

**Symptoms**: `ng serve` errors

**Solutions**:
1. **Install dependencies**:
   ```powershell
   cd frontend
   npm install
   ```
2. **Check Node version**: Requires Node 18+
3. **Clear cache**:
   ```powershell
   npm cache clean --force
   rm -rf node_modules
   npm install
   ```
4. **Check for TypeScript errors**: Read terminal output

---

## 6️⃣ TEST REPORT TEMPLATE

### Test Execution Summary

**Test Date**: ___________________  
**Tested By**: ___________________  
**Browser**: Chrome / Edge / Firefox (circle one)  
**OS**: Windows 10 / 11 (circle one)

### Results Overview

| Feature | Status | Notes |
|---------|--------|-------|
| 1. Human Detection | ⬜ PASS / ⬜ FAIL | |
| 2. Vehicle Detection | ⬜ PASS / ⬜ FAIL | |
| 3. Helmet/PPE | ⬜ PASS / ⬜ FAIL | |
| 4. Loitering | ⬜ PASS / ⬜ FAIL | |
| 5. Labour Count | ⬜ PASS / ⬜ FAIL | |
| 6. Crowd Density | ⬜ PASS / ⬜ FAIL | |
| 7. Box Counting | ⬜ PASS / ⬜ FAIL | |
| 8. Line Crossing | ⬜ PASS / ⬜ FAIL | |
| 9. Auto Tracking | ⬜ PASS / ⬜ FAIL | |
| 10. Smart Motion | ⬜ PASS / ⬜ FAIL | |
| 11. Face Detection | ⬜ PASS / ⬜ FAIL | |
| 12. Face Recognition | ⬜ PASS / ⬜ FAIL | |

### Performance Metrics

- **Average FPS**: _________
- **API Response Time**: _________ ms
- **Backend CPU Usage**: _________ %
- **Frontend Load Time**: _________ seconds

### Issues Encountered

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Overall Assessment

**System Status**: ⬜ All Tests Passed / ⬜ Some Tests Failed / ⬜ Major Issues

**Recommendations**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Sign-Off

**Tester Signature**: ___________________  
**Date**: ___________________

---

## 📊 QUICK REFERENCE: Feature Dependencies

```
Model Dependencies:
├── best_helmet.pt
│   ├── Human Detection
│   ├── Helmet/PPE Detection
│   ├── Labour Count
│   ├── Loitering (uses people boxes)
│   └── Crowd Density (uses people boxes)
│
├── best_product.pt
│   ├── Box Counting
│   └── Line Crossing (requires box tracking)
│
├── yolo11n.pt
│   └── Vehicle Detection
│
└── DeepFace
    ├── Face Detection (OpenCV)
    └── Face Recognition (FaceNet)

Logic Dependencies:
├── Auto Tracking (requires any object detection enabled)
└── Smart Motion (standalone, validates with object counts)
```

---

## 🎯 SUCCESS CRITERIA

### Minimum Acceptable Performance (MVP)

- ✅ At least **10 out of 12** features working
- ✅ FPS ≥ 1.5
- ✅ No critical errors in console
- ✅ Webcam activates successfully
- ✅ API calls returning 200 OK

### Production-Ready Criteria

- ✅ All **12 features** working perfectly
- ✅ FPS ≥ 2.5
- ✅ Zero console errors
- ✅ Smooth video feed
- ✅ Accurate detections (< 10% false positives)
- ✅ Face recognition working with employee database

---

## 📞 SUPPORT

**Issues Not Resolved?**

1. Check backend logs: Terminal running `main_unified.py`
2. Check frontend console: Browser DevTools (F12)
3. Review [COMPLETE_AUDIT_REPORT.md](COMPLETE_AUDIT_REPORT.md)
4. Review [UNIFIED_SYSTEM_GUIDE.md](UNIFIED_SYSTEM_GUIDE.md)

**Expected Testing Time**: 30-45 minutes (all 12 features)

---

**Good luck with testing! 🚀**
