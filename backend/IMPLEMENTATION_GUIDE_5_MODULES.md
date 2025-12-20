# Factory AI SaaS - Production Implementation Guide
## Complete Backend Integration for 5 Critical Modules

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements_complete.txt
```

**Key additions:**
- `apscheduler>=3.10.4` - Background job scheduling
- `sqlalchemy>=2.0.0` - Database ORM
- `boto3>=1.26.0` - AWS Rekognition

### 2. Configure Environment Variables
```bash
# .env file
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
REKOGNITION_COLLECTION_ID=factory-employees

# Camera Configuration
RTSP_URL=rtsp://192.168.1.100:554/stream
CAMERA_ID=CAM-MAIN

# Database (if using production DB)
DATABASE_URL=postgresql://user:password@localhost/factory_ai
```

### 3. Run the Complete System
```bash
python -m uvicorn main_integration:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📋 Module Implementation Summary

### **Module 1: Identity AWS Retry & Snapshot Management**
**File:** `services/identity_aws_retry.py`

#### Features Implemented:
✅ **Retry Decorator for AWS Rekognition**
- Exponential backoff strategy (1s → 2s → 4s → 8s)
- Handles: ServiceUnavailable, ThrottlingException, TimeoutError
- Configurable max retries (default: 3)
- Optional callback for monitoring retries

✅ **Snapshot Cleanup Service**
- Deletes images older than 90 days
- Scans multiple directories: `data/snapshots/unknown/`, `data/snapshots/faces/`, etc.
- Reports disk space freed
- Graceful error handling per file

#### Usage Example:
```python
from services.identity_aws_retry import create_aws_retry_decorator

@create_aws_retry_decorator(max_retries=3)
def search_faces_by_image(image_bytes):
    # Your AWS Rekognition call
    return client.search_faces_by_image(...)

# Or cleanup old snapshots
from services.identity_aws_retry import SnapshotCleanupService

cleanup = SnapshotCleanupService()
result = cleanup.cleanup_old_snapshots()
# Returns: {success: bool, files_deleted: int, disk_space_freed_mb: float}
```

---

### **Module 2: Vehicle Quality Gate & ANPR Validation**
**File:** `services/vehicle_quality_gate.py`

#### Features Implemented:
✅ **Three-Layer Quality Gate**
1. **OCR Confidence Threshold** (> 0.85)
   - Rejects low-confidence detections
   - Prevents "ghost plates" from triggering events

2. **Plate Format Validation** (India Standard)
   - Regex: `^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$`
   - Example: KA01AB1234
   - Cleans spaces and special characters

3. **Blocked Vehicle Detection**
   - Real-time system logging for blocked plates
   - In-memory cache + database lookup
   - Triggers security alerts

#### Usage Example:
```python
from services.vehicle_quality_gate import VehicleQualityGate

gate = VehicleQualityGate()

# Validate a plate
result = gate.validate_plate_recognition(
    ocr_text="KA 01 AB 1234",
    ocr_confidence=0.92,
    vehicle_track_id=5
)

# Result includes:
# {
#     'valid': True,
#     'plate_number': 'KA01AB1234',
#     'confidence': 0.92,
#     'status': 'UNKNOWN',  # or BLOCKED/AUTHORIZED
#     'should_trigger_gate_event': True,
#     'alert_message': None
# }

# Add to blocked list
gate.register_blocked_vehicle('KA01AB1234', 'Stolen vehicle', 'Officer_Smith')

# Check stats
stats = gate.get_gate_statistics()
# {blocked_vehicles: 5, ocr_threshold: 0.85, ...}
```

---

### **Module 3: Attendance Shift Integrity**
**File:** `services/attendance_shift_service.py`

#### Features Implemented:
✅ **Grace Period Logic**
- Compare check-in_time with shift_start_time + grace_period_minutes
- Flags as LATE if beyond grace period
- HR-visible in payroll reports

✅ **Early Exit Detection**
- Compare check_out_time with shift_end_time
- Flags employees leaving before shift ends
- Useful for identifying short breaks or early departures

✅ **Double-Entry Prevention**
- Caches check-ins in memory (12-hour window)
- Ignores face-recognition duplicates
- Prevents payroll errors from multiple detections

#### Usage Example:
```python
from services.attendance_shift_service import ShiftIntegrityService
from datetime import datetime

shift_service = ShiftIntegrityService()

# Process check-in
result = shift_service.process_shift_status(
    employee_id=123,
    check_in_time=datetime.now(),
    shift_data={
        'start_time': '08:00:00',
        'end_time': '17:00:00',
        'grace_period_minutes': 5
    }
)

# Result includes:
# {
#     'status': 'PRESENT' | 'LATE' | 'EARLY_EXIT' | 'ABSENT',
#     'is_late': True/False,
#     'is_early_exit': True/False,
#     'grace_period_applied': True/False,
#     'flagged_for_review': True/False,
#     'skipped_duplicate': True/False
# }

# Get payroll summary
summary = shift_service.get_employee_shift_summary(
    employee_id=123,
    date_range=(date(2025, 1, 1), date(2025, 1, 31))
)
# {total_days: 31, on_time: 28, late: 2, early_exits: 1, on_time_percentage: 90.3}
```

---

### **Module 4: Occupancy Background Scheduler**
**File:** `services/occupancy_scheduler.py`

#### Features Implemented:
✅ **Three Scheduled Jobs**

1. **Hourly Aggregation** (Every hour at :00)
   - Processes raw OccupancyLog entries
   - Calculates: avg_occupancy, max_occupancy, min_occupancy
   - Stores in OccupancyDailyAggregate table
   - Enables: Hourly charts, peak detection

2. **Drift Correction** (Daily at 03:00 AM)
   - Resets current_count to 0 for all cameras
   - Fixes accumulated detection errors
   - Prevents count from being "frozen" if someone missed on exit
   - Runs during night (facility closed)

3. **Monthly Aggregation** (1st of month at 00:00)
   - Summarizes daily data into monthly trends
   - Calculates total entries/exits for the month
   - Useful for capacity planning

#### Usage Example:
```python
from services.occupancy_scheduler import OccupancyScheduler

scheduler = OccupancyScheduler()

# Start all scheduled jobs
scheduler.start()
# ✅ Job 1: Hourly Occupancy Aggregation (every hour at :00)
# ✅ Job 2: Occupancy Drift Correction (daily at 03:00 AM)
# ✅ Job 3: Monthly Occupancy Aggregation (1st of month at 00:00)

# Get scheduler status
status = scheduler.get_scheduler_status()
# {
#     'running': True,
#     'jobs': [
#         {
#             'id': 'occupancy_hourly_aggregation',
#             'name': 'Hourly Occupancy Aggregation',
#             'next_run_time': '2025-01-15T15:00:00',
#             'trigger': 'cron[minute=0]'
#         },
#         ...
#     ]
# }

# Manually trigger hourly aggregation (for testing)
result = scheduler.aggregate_occupancy_hourly()
# {success: True, hour: 14, records_processed: 2400, aggregate_created: True}

# Stop scheduler at shutdown
scheduler.stop()
```

---

### **Module 5: Video RTSP-to-MJPEG Streaming**
**File:** `services/video_rtsp_mjpeg.py`

#### Features Implemented:
✅ **RTSP Stream Capture**
- OpenCV VideoCapture with reconnection logic
- Frame buffering and rate control
- Configurable frame rate (default: 30 FPS)

✅ **AI Overlay System**
- Bounding boxes for detections
- Color-coded by class (person: green, vehicle: blue, etc.)
- Confidence scores on labels
- Tracking IDs (if using tracker)

✅ **MJPEG Encoding**
- Converts frames to JPEG (quality: 80)
- Yields multipart/x-mixed-replace boundary format
- Compatible with `<img>` tags in browsers
- No external streaming service needed

#### Usage Example:
```python
# In your FastAPI app
from fastapi.responses import StreamingResponse
from services.video_rtsp_mjpeg import get_video_streaming_service

@app.get("/api/video_feed")
async def video_feed():
    service = get_video_streaming_service(
        rtsp_url="rtsp://192.168.1.100:554/stream",
        camera_id="CAM-MAIN",
        detection_model=my_detector  # Your detection model
    )
    
    service.start_stream()
    
    return StreamingResponse(
        service.generate_video_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# In Angular HTML
<img src="http://localhost:8000/api/video_feed" style="width: 100%;" />
```

---

## 🧪 Testing Each Module

### Test 1: Attendance Shift Integrity
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 123,
    "check_in_time": "2025-01-15T08:03:45",
    "shift_data": {
      "start_time": "08:00:00",
      "end_time": "17:00:00",
      "grace_period_minutes": 5
    }
  }'

# Expected: {status: LATE, is_late: true, grace_period_applied: true}
```

### Test 2: Vehicle Quality Gate
```bash
curl -X POST http://localhost:8000/api/v1/vehicle/validate-plate \
  -H "Content-Type: application/json" \
  -d '{
    "ocr_text": "KA 01 AB 1234",
    "ocr_confidence": 0.92,
    "vehicle_track_id": 5
  }'

# Expected: {valid: true, plate_number: KA01AB1234, should_trigger_gate_event: true}
```

### Test 3: Occupancy Scheduler
```bash
# Check if scheduler is running
curl http://localhost:8000/api/v1/occupancy/scheduler-status

# Expected: {running: true, jobs: [...]}

# Manually trigger aggregation
curl -X POST http://localhost:8000/api/v1/occupancy/trigger-aggregation

# Check logs for:
# ✅ Hourly Occupancy Aggregation completed in X.XXs
```

### Test 4: Snapshot Cleanup
```bash
# Cleanup old snapshots
curl -X POST http://localhost:8000/api/v1/identity/cleanup-snapshots

# Expected: {files_deleted: 42, disk_space_freed_mb: 1024.5}

# Check statistics
curl http://localhost:8000/api/v1/identity/snapshot-stats
```

### Test 5: Video Streaming
```bash
# Test in browser
http://localhost:8000/api/video_feed

# Check stream status
curl http://localhost:8000/api/video_feed/status

# Expected: {connected: true, frames_read: 1200, fps: 30}

# Add to HTML
<img src="http://localhost:8000/api/video_feed" style="max-width: 100%;">
```

---

## 📊 Production Deployment Checklist

- [ ] Install `apscheduler` and `sqlalchemy`
- [ ] Configure `.env` with AWS credentials
- [ ] Update RTSP_URL for your camera
- [ ] Create database tables (OccupancyLog, OccupancyDailyAggregate, etc.)
- [ ] Set up cron job or systemd timer for snapshot cleanup (if not using scheduler)
- [ ] Configure PostgreSQL for production (not SQLite)
- [ ] Set up log rotation for `backend.log`
- [ ] Create `/data/snapshots/unknown/` directory
- [ ] Test video stream in Angular frontend
- [ ] Enable CORS for your frontend domain
- [ ] Set up monitoring for scheduler job failures
- [ ] Configure AWS IAM role for Rekognition access

---

## 🔧 Customization Options

### Change Scheduler Times
```python
# In occupancy_scheduler.py, modify CronTrigger:
# Hourly: CronTrigger(minute=0)  # :00 of every hour
# Daily 3 AM: CronTrigger(hour=3, minute=0)
# Monthly 1st: CronTrigger(day=1, hour=0, minute=0)
```

### Adjust OCR Confidence Threshold
```python
# In vehicle_quality_gate.py:
OCR_CONFIDENCE_THRESHOLD = 0.85  # Change to 0.90 for stricter filtering
```

### Modify Grace Period
```python
# Pass in shift_data:
shift_data = {
    'start_time': '08:00:00',
    'end_time': '17:00:00',
    'grace_period_minutes': 10  # Change from 5 to 10
}
```

### Adjust Snapshot Retention
```python
# In identity_aws_retry.py:
RETENTION_DAYS = 90  # Change to 180 for longer retention
```

---

## 📈 Monitoring & Troubleshooting

### Check System Health
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/system-info
```

### View Logs
```bash
tail -f backend.log | grep "✅\|❌\|⚠️"
```

### Scheduler Not Running?
```python
# In Python console
from services.occupancy_scheduler import OccupancyScheduler
scheduler = OccupancyScheduler()
scheduler.start()
print(scheduler.get_scheduler_status())
```

### Video Stream Not Connecting?
1. Test RTSP URL manually:
   ```bash
   ffplay "rtsp://192.168.1.100:554/stream"
   ```
2. Check network connectivity to camera
3. Verify RTSP port (usually 554)
4. Check camera credentials if needed

---

## 🎯 Next Steps

1. **Test video stream** → Open `http://localhost:8000/api/video_feed` in browser
2. **Wait one hour** → Check if OccupancyDailyAggregate table gets first entry
3. **Monitor logs** → Watch for scheduler jobs completing successfully
4. **Run attendance check-in** → Test late detection with grace period
5. **Validate plates** → Test ANPR confidence gate with sample plates

---

**Version:** 4.0.0  
**Last Updated:** January 2025  
**Status:** ✅ Production Ready
