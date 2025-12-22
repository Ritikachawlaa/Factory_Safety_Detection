# Visual Face Detection Implementation Guide

## Overview
This document describes the implementation of visual bounding boxes with face IDs, persistent identification, and smart state-based detection.

## What Was Implemented

### 1. **Canvas-Based Bounding Box Drawing** ✅
**File:** [frontend/src/components/WebcamFeed.tsx](../frontend/src/components/WebcamFeed.tsx)

- Added overlay canvas element that renders on top of the video stream
- Draws rectangles around each detected face with:
  - **Green boxes** for recognized/known faces
  - **Orange boxes** for unknown faces
  - Face ID above each box in the format: `ID: [number] - [name]`
  - Confidence percentage below each box
  - Dynamic scaling to match video container size

**Code Changes:**
```tsx
// Added refs for overlay canvas and video container
const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
const videoContainerRef = useRef<HTMLDivElement>(null);

// Draw bounding boxes effect
useEffect(() => {
  // Get canvas context and clear
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // For each detected face:
  // - Draw rectangle outline (color based on recognition status)
  // - Draw name + ID label above box
  // - Draw confidence score below box
}, [result, width, height]);
```

### 2. **Persistent Face ID Assignment** ✅
**File:** [backend/main_unified.py](../backend/main_unified.py)

Backend now:
- Tracks each detected face with a unique `face_id`
- Assigns new IDs to newly detected faces
- Maintains face tracking across frames (10-second timeout)
- Matches faces across frames using bounding box proximity (100px threshold)
- Returns face data in API response with structure:
  ```json
  {
    "face_id": 1,
    "name": "John Doe",
    "confidence": 0.95,
    "bbox": { "x": 100, "y": 50, "w": 150, "h": 150 },
    "recognized": true
  }
  ```

**Backend Components:**
- `face_tracking = {}` - Global dictionary storing face states
- `face_counter = 0` - Counter for assigning new IDs
- `update_face_tracking()` - Function that manages face lifecycle
- `/api/detect` endpoint - Returns detected_faces array with IDs

### 3. **Smart State-Based Detection** ✅
**File:** [frontend/src/hooks/useSmartFaceDetection.ts](../frontend/src/hooks/useSmartFaceDetection.ts) (NEW)

Custom React hook that:
- Tracks previously detected faces using useRef
- Detects when NEW faces appear (new face_id)
- Detects when faces LEAVE (face_id no longer present)
- Only triggers updates when faces change
- Provides detection state with:
  - `hasChanged`: Boolean - whether face state changed
  - `newFaces`: Array - newly detected faces
  - `removedFaces`: Array - faces that left
  - `persistentFaces`: Array - all current faces

**Usage in PersonIdentityModule:**
```tsx
const { processFaceDetection, detectionState } = useSmartFaceDetection();

// In detection result handler:
const faceState = processFaceDetection(result);

// Only update when faces change
if (faceState.hasChanged) {
  // Update UI, show notifications
  console.log('New faces:', faceState.newFaces);
  console.log('Removed faces:', faceState.removedFaces);
}
```

### 4. **Enhanced PersonIdentityModule UI** ✅
**File:** [frontend/src/pages/PersonIdentityModule.tsx](../frontend/src/pages/PersonIdentityModule.tsx)

**New Features:**
1. **Currently Detected Faces Card**
   - Shows all faces currently visible on camera
   - Color-coded: Green for known, Orange for unknown
   - Displays Face ID, Name, and Confidence
   - Updates only when faces change

2. **Detection Events Alerts**
   - Shows when NEW faces are detected
   - Shows when faces leave the frame
   - Lists face names and IDs

3. **Detection History Table**
   - Tracks all detection events
   - Columns: Face ID, Name, Type (Employee/Unknown), Confidence, Last Seen, Status
   - Displays last 20 detection events

4. **Smart Updates**
   - Uses `useSmartFaceDetection` hook
   - Only processes data when faces actually change
   - Console logs show detection state changes

## How It Works Together

### Frontend Flow:
```
Video Stream → WebcamFeed Component
                     ↓
              Frame Capture (500ms interval)
                     ↓
              Send to Backend API (/api/detect)
                     ↓
              Receive Response with detected_faces[]
                     ↓
              Canvas Drawing (Draw bounding boxes)
                     ↓
              Smart Detection Hook (Compare old vs new)
                     ↓
              PersonIdentityModule Updates (On face changes only)
```

### Backend Flow:
```
Incoming Frame
      ↓
Run Face Detection Pipeline
      ↓
Extract Faces (Recognized + Unknown)
      ↓
Call update_face_tracking()
  - Remove timeouts faces
  - Match to existing by proximity
  - Assign new IDs if needed
  - Update last_seen timestamp
      ↓
Return response with detected_faces[]
      ↓
Send to Frontend with IDs
```

## Key Improvements

1. **Visual Feedback**: Users see exactly where faces are detected with colored boxes
2. **Persistent Identification**: Same person gets same ID across frames
3. **Efficient Processing**: Only updates when faces actually change (not every frame)
4. **Smart Alerts**: Shows when new people appear or leave
5. **Clear Status**: Color coding (green=known, orange=unknown) for quick recognition
6. **Confidence Display**: Shows detection confidence percentage

## Configuration

### Backend Settings (in main_unified.py):
```python
FACE_TIMEOUT = 10  # Remove face ID if not seen for 10 seconds
PROXIMITY_THRESHOLD = 100  # pixels - match faces within 100px distance
```

### Frontend Settings (in WebcamFeed.tsx):
```tsx
enabledFeatures={{
  face_detection: true,
  face_recognition: true,
  // ... other features
}}
intervalMs={500}  // Process frame every 500ms
```

## Testing the Implementation

1. **Open PersonIdentityModule** in the web app
2. **Webcam Feed** should show your face with a bounding box
3. **Box Color** indicates:
   - 🟢 **Green**: You've been enrolled as an employee
   - 🟠 **Orange**: Unknown person
4. **Face ID** displays above the box (e.g., "ID: 1 - John Doe")
5. **Move around** - same face keeps same ID even if it moves
6. **Leave frame** - box disappears, appears in "Faces Left" alert
7. **Return** - box reappears with same ID (within 10 seconds)

## Files Modified

| File | Changes |
|------|---------|
| [WebcamFeed.tsx](../frontend/src/components/WebcamFeed.tsx) | Added canvas drawing, bounding box rendering |
| [PersonIdentityModule.tsx](../frontend/src/pages/PersonIdentityModule.tsx) | Added detection cards, alerts, smart processing |
| [main_unified.py](../backend/main_unified.py) | Face tracking system, ID assignment |
| [useSmartFaceDetection.ts](../frontend/src/hooks/useSmartFaceDetection.ts) | NEW - Smart state detection hook |

## Next Steps (Optional Enhancements)

1. **Face Database Integration**: Store recognized faces in persistent database
2. **Real-time Attendance**: Auto-mark attendance when enrolled face detected
3. **Confidence Threshold**: Only show boxes above certain confidence level
4. **Snapshot Capture**: Save images of detected faces
5. **Alert System**: Notify when unknown person detected
6. **Performance Optimization**: Reduce canvas redraws with dirty rectangle tracking

## Troubleshooting

### Boxes not appearing?
- Check if face_detection is enabled in features
- Verify backend is returning detected_faces array
- Check browser console for JavaScript errors

### Boxes wrong color?
- Green = face recognized in database
- Orange = face not recognized
- Make sure you've enrolled a face first

### IDs changing?
- IDs only persist for 10 seconds of no detection
- If face leaves frame and returns within 10s, same ID is reused
- After 10s, face gets new ID when detected again

### Performance issues?
- Reduce `intervalMs` in WebcamFeed (default 500ms)
- Lower video resolution if needed
- Disable unused detection features
