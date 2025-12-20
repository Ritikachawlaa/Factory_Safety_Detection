# Module 4: People Counting & Occupancy Analytics - Quick Start Guide

## 📋 Overview

This guide walks you through setting up and using Module 4 for real-time occupancy tracking with virtual line crossing detection.

**What you'll be able to do:**
- Track people entering/exiting areas in real-time
- View current occupancy for any camera
- Access 7 days of hourly data, 30 days of daily data, 12 months of monthly data
- Receive capacity alerts when areas exceed max occupancy
- Calibrate counts after manual headcounts

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Database Setup

```bash
# Create tables (from backend directory)
cd backend
python -c "
from detection_system.occupancy_models import Base
from database import engine
Base.metadata.create_all(bind=engine)
print('✓ Occupancy tables created')
"
```

### Step 2: Add Camera Configuration

```python
# config.py or in FastAPI startup

from detection_system.occupancy_models import CameraDAO
from database import SessionLocal

db = SessionLocal()

# Create a camera
camera_data = {
    'camera_id': 'GATE_A',
    'camera_name': 'Gate A Entrance',
    'location': 'Main Gate',
    'camera_type': 'entry_only',
    'max_occupancy': 100,
    'resolution_width': 1920,
    'resolution_height': 1080
}

camera = CameraDAO.create(db, camera_data)
print(f"✓ Created camera: {camera.camera_id}")
```

### Step 3: Define Virtual Lines

```python
from detection_system.occupancy_models import VirtualLineDAO

# Create an entry line (crossing from left to right means entry)
line_data = {
    'camera_id': camera.id,
    'line_name': 'Entrance Line A',
    'x1': 0,
    'y1': 300,      # Middle height of frame
    'x2': 1920,
    'y2': 300,      # Horizontal line
    'direction': 'entry',
    'confidence_threshold': 0.5
}

line = VirtualLineDAO.create(db, line_data)
print(f"✓ Created line: {line.line_name}")
```

**Line Coordinate Explanation:**
```
(0,0) ──────────────────────────── (1920,0)
  │                                   │
  │          Camera View              │
  │                                   │
  │     x1,y1 ──────────── x2,y2     │  ← Virtual Line
  │     (0,300)─────────(1920,300)    │
  │                                   │
  │                                   │
  (0,1080)────────────────────────(1920,1080)
```

### Step 4: Initialize Service

```python
from detection_system.occupancy_endpoints import init_occupancy_service

# On app startup
init_occupancy_service(db)
print("✓ Occupancy service initialized")
```

### Step 5: Start Processing Frames

```python
# In your detection pipeline (e.g., realtime_detector.py)

while True:
    frame = camera.read()
    
    # YOLOv8 + ByteTrack detection (existing)
    detections = yolo_model.detect(frame)
    tracked_persons = byte_tracker.update(detections)
    
    # NEW: Process occupancy
    detection_data = [
        {
            'track_id': person.track_id,
            'confidence': person.confidence,
            'centroid': person.get_centroid(),
            'prev_centroid': person.get_prev_centroid()
        }
        for person in tracked_persons
        if person.class_id == PERSON_CLASS  # Filter to persons only
    ]
    
    occupancy_service.process_frame(camera.id, detection_data)
    
    # Save occupancy every minute
    if frame_count % 1500 == 0:  # At 25 fps = 1 minute
        occupancy_service.save_occupancy_log(camera.id, period_seconds=60)
```

### Step 6: Query Occupancy

```bash
# Get current occupancy
curl http://localhost:8000/api/occupancy/cameras/1/live

# Response:
{
  "camera_id": 1,
  "current_occupancy": 45,
  "total_entries": 1234,
  "total_exits": 1189,
  "unique_persons": 45,
  "last_updated": "2025-01-15T10:30:45Z"
}
```

---

## 📊 API Quick Reference

### Real-Time Occupancy
```bash
# Current occupancy for camera
GET /api/occupancy/cameras/{id}/live

# Facility-wide occupancy
GET /api/occupancy/facility/live

# Calibrate after manual headcount
POST /api/occupancy/cameras/{id}/calibrate
Body: { "occupancy_value": 50, "notes": "Manual count" }
```

### Historical Data
```bash
# Last 24 hours (1-minute logs)
GET /api/occupancy/cameras/{id}/logs?hours=24

# Last 7 days (hourly summaries)
GET /api/occupancy/cameras/{id}/hourly?days=7

# Last 30 days (daily summaries)
GET /api/occupancy/cameras/{id}/daily?days=30

# Last 12 months (monthly summaries)
GET /api/occupancy/cameras/{id}/monthly?months=12
```

### Camera & Line Management
```bash
# Create camera
POST /api/occupancy/cameras
Body: { "camera_id": "GATE_A", "camera_name": "...", ... }

# Create virtual line
POST /api/occupancy/lines
Body: { "camera_id": 1, "line_name": "...", "x1": 0, ... }

# Get all cameras
GET /api/occupancy/cameras

# Get camera's lines
GET /api/occupancy/cameras/{id}/lines
```

### Alerts
```bash
# Get active alerts
GET /api/occupancy/alerts

# Resolve an alert
PUT /api/occupancy/alerts/{id}/resolve
```

---

## 🔧 Configuration

### Environment Variables
```bash
# .env or docker-compose.yml
DATABASE_URL=postgresql://user:pass@localhost/factory_ai
OCCUPANCY_LOG_INTERVAL=60  # Seconds between saves
OCCUPANCY_CONFIDENCE_MIN=0.5  # Min confidence threshold
```

### Camera Types

| Type | Purpose | Example |
|------|---------|---------|
| entry_only | Only counts entries | Entrance door |
| exit_only | Only counts exits | Exit door |
| bidirectional | Counts both | Hallway line |

### Virtual Line Tips

1. **Horizontal Line (Entry/Exit):**
   ```python
   x1=0, y1=300, x2=1920, y2=300  # Same Y = horizontal
   ```

2. **Vertical Line (Corridor):**
   ```python
   x1=960, y1=0, x2=960, y2=1080  # Same X = vertical
   ```

3. **Line Direction:**
   ```python
   # For entry line: crossing left→right = entry
   # For exit line: crossing right→left = exit
   # For bidirectional: direction determined by movement vector
   ```

---

## 📈 Understanding the Data

### Occupancy Log (1-5 minutes)
```
Time: 10:00 AM
─────────────────
Entries: 5 people crossed from left to right
Exits: 2 people crossed from right to left
Net: +3 (current occupancy = 43)
```

### Hourly Summary
```
Time: 10:00 - 11:00 AM
──────────────────────
Total Entries: 15
Total Exits: 8
Average Occupancy: 47.5 people
Peak Occupancy: 52 people (around 10:30)
Unique People: 22 distinct individuals
```

### Daily Summary
```
Date: Jan 15, 2025
──────────────────
Total Entries: 234
Total Exits: 231
Average Occupancy: 46.2
Peak Occupancy: 65 (during 2 PM rush)
Unique People: 189
```

---

## ⚠️ Common Issues and Solutions

### Issue: Occupancy keeps increasing (no exits detected)

**Cause:** Exit line not configured or people leaving off-camera

**Solution:**
1. Add exit line to camera
2. Verify exit line coordinates are correct
3. Check camera angle covers all exits
4. Use manual calibration to correct

```bash
POST /api/occupancy/cameras/1/calibrate
Body: { "occupancy_value": 45 }
```

### Issue: Negative occupancy (-5 people)

**This is automatically prevented.** Count is clamped to 0.

**Cause:** Detection errors (false positives)

**Solution:**
1. Increase `confidence_threshold` on line
2. Adjust line position
3. Manual calibration after verification

### Issue: Line crossing not detected

**Cause:** Line not configured correctly

**Verification Steps:**
1. Check line is in correct location (verify coordinates)
2. Verify `direction` field matches use case
3. Check `confidence_threshold` isn't too high
4. Ensure `is_active = true`

```python
# Debug: Log line configuration
line = VirtualLineDAO.get_by_id(db, line_id)
print(f"Line: ({line.x1},{line.y1}) → ({line.x2},{line.y2})")
print(f"Direction: {line.direction}")
print(f"Active: {line.is_active}")
```

### Issue: API returns "Service not initialized"

**Cause:** `init_occupancy_service()` not called

**Solution:** Call on app startup
```python
from fastapi import FastAPI
from detection_system.occupancy_endpoints import init_occupancy_service
from database import SessionLocal

app = FastAPI()

@app.on_event("startup")
async def startup():
    db = SessionLocal()
    init_occupancy_service(db)
```

---

## 🎯 Next Steps

1. **Dashboard Integration:** Display `/api/occupancy/facility/live` on your dashboard
2. **Alerts:** Subscribe to `/api/occupancy/alerts` endpoint
3. **Reports:** Use `/api/occupancy/cameras/{id}/daily` for daily reports
4. **Scheduled Aggregation:** Set up APScheduler for background tasks
5. **Notifications:** Email alerts when capacity exceeded

---

## 📚 Learn More

- **Full Implementation Guide:** See `OCCUPANCY_IMPLEMENTATION_GUIDE.md`
- **Database Schema:** See occupancy_models.py comments
- **Service Layer:** See occupancy_service.py for algorithm details
- **API Spec:** See occupancy_endpoints.py for all endpoints

---

## 🔗 Integration with Other Modules

### Module 2 (Vehicle Detection)
- Filter out non-person detections: `if person.class_id == PERSON_CLASS`
- Occupancy only tracks people, not vehicles

### Module 3 (Attendance)
- Attendance tracks face + person
- Occupancy tracks all people (recognized or not)
- Both can run simultaneously

### Future: Module 5 (Alert Integration)
- Occupancy alerts → push notifications
- Capacity exceeded → SMS to manager
- Anomaly detected → incident report

---

## 📞 Support

For questions or issues:
1. Check `OCCUPANCY_IMPLEMENTATION_GUIDE.md` for detailed docs
2. Review error logs in `occupancy_service.log`
3. Verify database schema: `SELECT * FROM cameras_occupancy;`
4. Test API with curl or Postman

---

**Version:** 1.0  
**Last Updated:** Jan 2025  
**Status:** Production Ready
