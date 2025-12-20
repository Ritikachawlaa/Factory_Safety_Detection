<!-- Module 3: Attendance & Workforce Presence System - Quick Start Guide -->

# Module 3: Attendance & Workforce Presence System - Quick Start Guide

**Version:** 1.0  
**Last Updated:** December 2025  
**Status:** Production-Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [5-Minute Integration](#5-minute-integration)
3. [Core Concepts](#core-concepts)
4. [Basic Usage Examples](#basic-usage-examples)
5. [Verification Checklist](#verification-checklist)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Module 3 provides **automated, face-based attendance tracking** for factory employees without requiring biometric devices. It integrates with **Module 1: Identity Service** (AWS Rekognition) to identify employees and automatically mark their attendance.

### Key Features:
- ✅ **Automatic Check-In/Out**: Face detection at cameras triggers attendance
- ✅ **Grace Period Handling**: Configurable late tolerance (default: 5 minutes)
- ✅ **Exit-Based Check-Out**: Detect check-out when employee leaves premises
- ✅ **Manual Overrides**: HR can correct records for camera downtime
- ✅ **Shift Management**: Support for multiple shifts with different hours
- ✅ **Comprehensive Reporting**: Daily, shift-wise, and department-wise reports

---

## 5-Minute Integration

### Step 1: Copy Files (30 seconds)
Copy three Python files to your backend:
```bash
# From: Module 3 delivery package
# To: backend/detection_system/

- attendance_models.py      (650 lines)
- attendance_service.py     (950 lines)
- attendance_endpoints.py   (700 lines)
```

### Step 2: Update Database Models (1 minute)
Ensure your SQLAlchemy setup includes the new models. In your `settings.py` or database initialization:

```python
from detection_system.attendance_models import (
    Base, Shift, Department, Employee, AttendanceRecord, TimeFenceLog
)

# Include in Base.metadata.create_all()
```

### Step 3: Initialize Attendance Module (1 minute)
In your FastAPI main app (`app/main.py` or `main_unified.py`):

```python
from fastapi import FastAPI
from sqlalchemy.orm import Session
from detection_system.attendance_endpoints import (
    router as attendance_router,
    init_attendance_module
)
from database import SessionLocal  # Your database session

app = FastAPI()

# On startup
@app.on_event("startup")
async def startup():
    db = SessionLocal()
    init_attendance_module(db)
    db.close()

# Include router
app.include_router(attendance_router)
```

### Step 4: Set Up Shifts & Departments (1 minute)
Create shifts and departments using the API:

```bash
# Create Morning Shift
curl -X POST http://localhost:8000/api/attendance/shifts \
  -H "Content-Type: application/json" \
  -d '{
    "shift_name": "Morning",
    "start_time": "08:00:00",
    "end_time": "16:00:00",
    "grace_period_minutes": 5
  }'

# Create Department
curl -X POST http://localhost:8000/api/attendance/departments \
  -H "Content-Type: application/json" \
  -d '{
    "dept_name": "Production Floor",
    "shift_id": 1,
    "manager_name": "John Manager",
    "location": "Floor 1, Section A",
    "entry_camera_id": "ENTRY_CAM_01",
    "exit_camera_id": "EXIT_CAM_01"
  }'
```

### Step 5: Connect Identity Service (1 minute)
When Module 1 detects a face and identifies an employee, call:

```python
# From your Module 1 identity processing
from detection_system.attendance_service import AttendanceService
from database import SessionLocal

db = SessionLocal()
service = AttendanceService(db)

# On face detection - check-in
result = service.process_face_detection(
    aws_rekognition_id="person-123",
    camera_id="ENTRY_CAM_01",
    confidence=0.95
)

# On exit detection - check-out
result = service.process_exit_detection(
    aws_rekognition_id="person-123",
    camera_id="EXIT_CAM_01",
    confidence=0.93,
    exit_reason=ExitReason.END_OF_SHIFT
)

db.close()
```

---

## Core Concepts

### 1. **Shift Model**
Defines work hours and grace periods:
```python
Shift {
  shift_name: "Morning"        # Name of shift
  start_time: 08:00            # When shift starts
  end_time: 16:00              # When shift ends
  grace_period_minutes: 5      # Late tolerance
  break_start: 12:00           # (Optional) break start
  break_end: 13:00             # (Optional) break end
}
```

### 2. **Department Model**
Maps employees to shifts and locations:
```python
Department {
  dept_name: "Production"
  shift_id: 1                    # Link to Shift
  manager_name: "John"
  location: "Floor 1, Section A"
  entry_camera_id: "ENTRY_01"    # Where employees enter
  exit_camera_id: "EXIT_01"      # Where employees leave
}
```

### 3. **AttendanceRecord Model**
One record per employee per day:
```python
AttendanceRecord {
  employee_id: 1
  attendance_date: "2025-12-20"
  check_in_time: "08:03:00"      # When employee first detected
  check_out_time: "16:05:00"     # When employee detected at exit
  status: "Present|Late|Absent"  # Automatically calculated
  is_manual_override: false       # HR-made corrections
  grace_period_applied: false     # Whether grace period was used
}
```

### 4. **TimeFenceLog Model**
Tracks employee movement:
```python
TimeFenceLog {
  employee_id: 1
  event_type: "entry|exit|re_entry|suspicious_movement"
  event_timestamp: "2025-12-20T08:03:00"
  camera_id: "ENTRY_01"
  exit_reason: "lunch_break|end_of_shift|unknown"
  is_authorized: true            # Whether exit was expected
}
```

### 5. **Face-Based Check-In Flow**

```
Face Detected (Module 1)
    ↓
Identify Employee (AWS Rekognition)
    ↓
Check Shift Window (Is employee on shift?)
    ↓
Create/Update Session (Track employee in frame)
    ↓
Get Today's Record (Already checked in?)
    ↓
Calculate Status (On time? Late?)
    ↓
Create AttendanceRecord with Check-In Time
    ↓
Return Result (Success, employee name, status)
```

---

## Basic Usage Examples

### Example 1: Create Morning Shift
```bash
POST /api/attendance/shifts
{
  "shift_name": "Morning",
  "start_time": "08:00:00",
  "end_time": "16:00:00",
  "grace_period_minutes": 5,
  "description": "First shift of the day"
}

Response:
{
  "id": 1,
  "shift_name": "Morning",
  "start_time": "08:00:00",
  "end_time": "16:00:00",
  "grace_period_minutes": 5,
  "duration_minutes": 480,
  "is_active": true
}
```

### Example 2: Process Face Detection
```bash
POST /api/attendance/process-face-detection
{
  "aws_rekognition_id": "person-12345",
  "camera_id": "ENTRY_CAM_01",
  "confidence": 0.95,
  "is_exit": false
}

Response (Check-In):
{
  "success": true,
  "employee_id": 5,
  "employee_name": "Rajesh Kumar",
  "check_in_time": "2025-12-20T08:03:15",
  "is_late": false,
  "message": "Checked in - On time"
}
```

### Example 3: Process Exit Detection
```bash
POST /api/attendance/process-face-detection
{
  "aws_rekognition_id": "person-12345",
  "camera_id": "EXIT_CAM_01",
  "confidence": 0.94,
  "is_exit": true,
  "exit_reason": "end_of_shift"
}

Response (Check-Out):
{
  "success": true,
  "employee_id": 5,
  "check_out_time": "2025-12-20T16:05:30",
  "duration_minutes": 482,
  "message": "Successfully checked out"
}
```

### Example 4: Manual Override (Camera Downtime)
```bash
POST /api/attendance/override
{
  "employee_id": 5,
  "attendance_date": "2025-12-20",
  "check_in_time": "2025-12-20T08:00:00",
  "check_out_time": "2025-12-20T16:00:00",
  "status": "Present",
  "reason": "Camera downtime during shift",
  "override_user": "admin@company.com"
}

Response:
{
  "success": true,
  "message": "Attendance record updated",
  "record_id": 123,
  "employee_id": 5,
  "status": "Present"
}
```

### Example 5: Get Daily Report
```bash
GET /api/attendance/reports?report_type=summary

Response:
{
  "success": true,
  "timestamp": "2025-12-20T17:30:00",
  "data": {
    "date": "2025-12-20",
    "total_employees": 150,
    "present": 145,
    "late": 3,
    "half_day": 2,
    "absent": 0,
    "leave": 0,
    "currently_in_frame": 0,
    "check_ins_today": 145,
    "check_outs_today": 144,
    "late_entries": 3
  }
}
```

### Example 6: Get Shift-Wise Report
```bash
GET /api/attendance/reports?report_type=shift-wise&report_date=2025-12-20

Response:
{
  "success": true,
  "timestamp": "2025-12-20T17:30:00",
  "data": {
    "shifts": [
      {
        "shift_name": "Morning",
        "shift_hours": "08:00:00 - 16:00:00",
        "total_employees": 100,
        "present": 98,
        "late": 2,
        "half_day": 0,
        "absent": 0,
        "leave": 0,
        "attendance_percentage": 98.0
      },
      {
        "shift_name": "Evening",
        "shift_hours": "16:00:00 - 00:00:00",
        "total_employees": 50,
        "present": 47,
        "late": 1,
        "half_day": 2,
        "absent": 0,
        "leave": 0,
        "attendance_percentage": 98.0
      }
    ]
  }
}
```

### Example 7: Get Late Entries Report
```bash
GET /api/attendance/reports?report_type=late-entries&report_date=2025-12-20

Response:
{
  "success": true,
  "data": {
    "late_entries": [
      {
        "employee_id": "EMP-001",
        "employee_name": "Rajesh Kumar",
        "department": "Production",
        "check_in_time": "2025-12-20T08:08:00",
        "late_minutes": 8,
        "grace_period_minutes": 5,
        "override": false
      }
    ]
  }
}
```

---

## Verification Checklist

After integration, verify these components:

### Database Setup ✓
- [ ] Shift table created with 5 columns
- [ ] Department table created with 8 columns
- [ ] AttendanceRecord table with 20+ columns
- [ ] TimeFenceLog table created
- [ ] All foreign key constraints in place
- [ ] All indexes created (10+ on critical columns)

### Service Initialization ✓
- [ ] AttendanceService instantiated at startup
- [ ] IdentityServiceIntegration cache loaded
- [ ] ExitDetectionManager initialized
- [ ] Database session connected

### API Endpoints ✓
- [ ] GET `/api/attendance/health` returns 200
- [ ] POST `/api/attendance/shifts` works
- [ ] POST `/api/attendance/departments` works
- [ ] POST `/api/attendance/process-face-detection` works
- [ ] GET `/api/attendance/reports` works
- [ ] POST `/api/attendance/override` works

### Face Detection Flow ✓
- [ ] Identity Service calls `/api/attendance/process-face-detection`
- [ ] AttendanceRecord created on first detection
- [ ] Status calculated correctly (Present/Late)
- [ ] Session state tracked in memory

### Exit Detection Flow ✓
- [ ] Face detected at exit camera
- [ ] Check-out time recorded
- [ ] TimeFenceLog entry created
- [ ] Session cleared

---

## Troubleshooting

### Issue: "Unknown employee" on face detection
**Cause**: Employee not registered or AWS Rekognition ID not in database
**Solution**:
1. Ensure employee record has `aws_rekognition_id` filled
2. Run identity cache refresh: `identity_service.refresh_cache()`
3. Check employee `is_active = True`

### Issue: "Not on shift" message
**Cause**: Detection occurring outside shift hours
**Solution**:
1. Verify shift `start_time` and `end_time` are correct
2. Check employee's assigned `shift_id`
3. System allows 30-min grace period after shift end

### Issue: All employees marked as "Absent"
**Cause**: No check-in detections, or camera IDs not configured
**Solution**:
1. Verify entry camera is configured in Department
2. Check Module 1 is sending detections to `/process-face-detection`
3. Ensure face confidence > 0.8 (minimum threshold)

### Issue: Check-out not working
**Cause**: Exit camera not properly configured
**Solution**:
1. Set `exit_camera_id` in Department model
2. Verify face is detected at exact `exit_camera_id` (not approximate)
3. Check exit detection is within shift hours + 30-min buffer

### Issue: Manual override not saving
**Cause**: Employee ID or date format incorrect
**Solution**:
1. Use correct employee ID (integer, not string)
2. Ensure date format: `YYYY-MM-DD`
3. Verify employee exists and is active

### Issue: Reports showing incorrect data
**Cause**: Records not committed to database
**Solution**:
1. Verify `session.commit()` is called in service
2. Check database connection is active
3. Ensure attendance records have `is_active = True`

---

## Next Steps

1. **Production Deployment**: Configure PostgreSQL backups and monitoring
2. **Face Accuracy**: Test with helmets, masks, poor lighting conditions
3. **Grace Periods**: Adjust `grace_period_minutes` based on site requirements
4. **Break Handling**: Configure `break_start` and `break_end` times for shifts
5. **Reporting**: Set up automated daily/weekly report generation
6. **Alerts**: Configure notifications for late entries or suspicious exits

---

## Support & Documentation

- **Implementation Guide**: Detailed technical reference for all components
- **Visual Reference**: ASCII diagrams of architecture and data flows
- **API Reference**: Complete endpoint documentation
- **Troubleshooting Matrix**: Common issues and solutions

For detailed implementation, see `MODULE_3_IMPLEMENTATION_GUIDE.md`

---

**Module Status**: ✅ Production-Ready | **Last Tested**: December 2025
