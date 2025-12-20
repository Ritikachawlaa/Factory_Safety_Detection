<!-- Module 3: Attendance & Workforce Presence System - Complete Implementation Guide -->

# Module 3: Attendance & Workforce Presence System - Implementation Guide

**Version:** 1.0 | **Last Updated:** December 2025 | **Status:** Production-Ready

---

## 📚 Complete Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema Deep Dive](#database-schema-deep-dive)
3. [Service Layer Architecture](#service-layer-architecture)
4. [API Reference](#api-reference)
5. [Integration with Module 1](#integration-with-module-1)
6. [Business Logic](#business-logic)
7. [Performance Optimization](#performance-optimization)
8. [Error Handling](#error-handling)
9. [Testing Guide](#testing-guide)
10. [Deployment Guide](#deployment-guide)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│              Module 1: Identity Service                  │
│          (AWS Rekognition Face Detection)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Face Detection Events
                     │ (aws_rekognition_id, confidence)
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Module 3: Attendance Service                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AttendanceService (Main Orchestrator)           │   │
│  │  - process_face_detection()                      │   │
│  │  - process_exit_detection()                      │   │
│  │  - manual_override_attendance()                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IdentityServiceIntegration                      │   │
│  │  - AWS Rekognition ID → Employee mapping        │   │
│  │  - Confidence threshold checking                 │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  GracePeriodCalculator                           │   │
│  │  - Late detection logic                          │   │
│  │  - Grace period validation                       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ExitDetectionManager                            │   │
│  │  - Exit camera validation                        │   │
│  │  - Unauthorized exit detection                   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AttendanceReportingUtility                      │   │
│  │  - Shift-wise reports                            │   │
│  │  - Department-wise reports                       │   │
│  │  - Late entries report                           │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  FastAPI Endpoints Layer (attendance_endpoints.py)      │
│  - POST /api/attendance/process-face-detection          │
│  - POST /api/attendance/override                        │
│  - GET /api/attendance/reports                          │
│  - GET /api/attendance/summary                          │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  Database Layer (attendance_models.py)                  │
│  - Shift, Department, Employee                          │
│  - AttendanceRecord, TimeFenceLog                       │
│  - DAOs: ShiftDAO, DepartmentDAO, etc.                  │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│           PostgreSQL Database                           │
│  (ACID compliance, indexing, relationships)             │
└─────────────────────────────────────────────────────────┘
```

### Data Flow: Check-In Process

```
Face Detection
    ↓
POST /api/attendance/process-face-detection
    ↓
AttendanceService.process_face_detection()
    ├─ Identify employee (AWS Rekognition ID lookup)
    ├─ Check if on shift (shift time window)
    ├─ Check/Create session (in-memory EmployeeSessionState)
    ├─ Get today's AttendanceRecord
    ├─ Calculate status (Present vs Late)
    ├─ Create/Update database record
    └─ Return result (success, employee_name, is_late)
    ↓
Database
    ├─ AttendanceRecord created/updated
    ├─ Employee session tracked in memory
    └─ Statistics updated
    ↓
Response to Caller
    └─ {success, employee_id, check_in_time, is_late, message}
```

### Data Flow: Check-Out Process

```
Face at Exit Camera
    ↓
POST /api/attendance/process-face-detection?is_exit=true
    ↓
AttendanceService.process_exit_detection()
    ├─ Identify employee
    ├─ Verify exit camera (is this the exit camera?)
    ├─ Validate exit timing (within shift hours?)
    ├─ Get today's AttendanceRecord
    ├─ Update check_out_time
    ├─ Create TimeFenceLog (exit event)
    ├─ Clear employee session
    └─ Return result
    ↓
Database
    ├─ AttendanceRecord.check_out_time updated
    ├─ TimeFenceLog.exit event created
    ├─ Session state cleared
    └─ Statistics updated
    ↓
Response
    └─ {success, check_out_time, duration_minutes, message}
```

---

## Database Schema Deep Dive

### Table 1: `shifts` (Shift Configuration)

```sql
CREATE TABLE shifts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    shift_name VARCHAR(100) UNIQUE NOT NULL,
    start_time TIME NOT NULL,                    -- e.g., 08:00:00
    end_time TIME NOT NULL,                      -- e.g., 16:00:00
    grace_period_minutes INTEGER DEFAULT 5,     -- Late tolerance
    break_start TIME,                            -- e.g., 12:00:00
    break_end TIME,                              -- e.g., 13:00:00
    break_duration_minutes INTEGER DEFAULT 0,   -- e.g., 60
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    
    CONSTRAINT check_shift_time_order 
        CHECK (start_time < end_time),
    
    INDEX idx_shift_active (is_active),
    INDEX idx_shift_name (shift_name)
);
```

**Example Data**:
```
| id | shift_name | start_time | end_time | grace_period_minutes |
|----|------------|------------|----------|----------------------|
| 1  | Morning    | 08:00:00   | 16:00:00 | 5                    |
| 2  | Evening    | 16:00:00   | 00:00:00 | 5                    |
| 3  | Night      | 00:00:00   | 08:00:00 | 10                   |
```

**Key Methods**:
- `get_duration_minutes()` - Total shift duration (480 min for 8-hour shift)
- `is_during_shift(time)` - Check if time is within shift
- `is_late(time)` - Check if time exceeds grace period

---

### Table 2: `departments` (Department Configuration)

```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(150) UNIQUE NOT NULL,
    shift_id INTEGER NOT NULL,
    manager_name VARCHAR(100),
    location VARCHAR(200),                 -- e.g., "Floor 1, Section A"
    entry_camera_id VARCHAR(50),           -- Main entry camera
    exit_camera_id VARCHAR(50),            -- Main exit camera
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    
    FOREIGN KEY (shift_id) REFERENCES shifts(id),
    INDEX idx_dept_shift_active (shift_id, is_active)
);
```

**Example Data**:
```
| id | dept_name        | shift_id | location           | entry_camera_id | exit_camera_id |
|----|------------------|----------|-------------------|-----------------|----------------|
| 1  | Production Floor | 1        | Floor 1, Section A | ENTRY_CAM_01    | EXIT_CAM_01    |
| 2  | Assembly Line    | 1        | Floor 2, Section B | ENTRY_CAM_02    | EXIT_CAM_02    |
| 3  | Quality Check    | 2        | Floor 1, Section C | ENTRY_CAM_03    | EXIT_CAM_03    |
```

---

### Table 3: `employees` (Extended with Attendance Fields)

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id VARCHAR(50) UNIQUE NOT NULL,     -- e.g., "EMP-001"
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL,
    face_encoding VARCHAR(500),                  -- Face recognition data
    aws_rekognition_id VARCHAR(200) UNIQUE,      -- AWS Rekognition index ID
    is_active BOOLEAN DEFAULT TRUE,
    hire_date DATE,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (shift_id) REFERENCES shifts(id),
    INDEX idx_employee_dept_shift (department_id, shift_id, is_active),
    INDEX idx_employee_aws_id (aws_rekognition_id)
);
```

**Critical Field**: `aws_rekognition_id`
- Populated by Module 1: Identity Service
- Unique identifier for face recognition
- Used to match detected faces to employees
- Must be filled for attendance to work

---

### Table 4: `attendance_records` (Daily Attendance)

```sql
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_date DATE NOT NULL,               -- e.g., 2025-12-20
    check_in_time DATETIME,                      -- First detection
    check_out_time DATETIME,                     -- Last detection at exit
    check_in_type ENUM('auto_face', 'manual_override', 'system_correction'),
    check_out_type ENUM('auto_face', 'manual_override', 'system_correction'),
    status ENUM('Present', 'Late', 'Half-day', 'Absent', 'Leave'),
    
    -- Override tracking
    is_manual_override BOOLEAN DEFAULT FALSE,
    override_by_user VARCHAR(100),               -- HR user ID
    override_reason TEXT,
    override_timestamp DATETIME,
    
    -- Calculated fields
    shift_duration_minutes INTEGER,              -- Expected duration
    actual_duration_minutes INTEGER,             -- Actual duration
    grace_period_applied BOOLEAN DEFAULT FALSE,
    
    -- Detection metadata
    first_detection_camera VARCHAR(50),
    last_detection_camera VARCHAR(50),
    detection_confidence FLOAT DEFAULT 0.0,
    notes TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    UNIQUE KEY unique_daily_attendance (employee_id, attendance_date),
    INDEX idx_attendance_employee_date (employee_id, attendance_date),
    INDEX idx_attendance_date_status (attendance_date, status),
    INDEX idx_attendance_manual_override (is_manual_override, attendance_date)
);
```

**Status Logic**:
```
if check_in_time is NULL:
    status = ABSENT
else if check_in_time > start_time + grace_period:
    status = LATE
else:
    status = PRESENT

if check_out_time is NULL and date is today:
    status = HALF_DAY (if after shift end)
```

**Example Data**:
```
| id | employee_id | attendance_date | check_in_time       | check_out_time      | status |
|----|-------------|-----------------|---------------------|---------------------|--------|
| 1  | 5           | 2025-12-20      | 2025-12-20 08:03:15 | 2025-12-20 16:05:30 | Late   |
| 2  | 6           | 2025-12-20      | 2025-12-20 07:58:00 | 2025-12-20 16:00:45 | Present|
| 3  | 7           | 2025-12-20      | NULL                | NULL                | Absent |
```

---

### Table 5: `time_fence_logs` (Movement Tracking)

```sql
CREATE TABLE time_fence_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_record_id INTEGER,                -- Link to daily record
    event_timestamp DATETIME DEFAULT NOW(),     -- When event occurred
    event_type ENUM('entry', 'exit', 're_entry', 'suspicious_movement'),
    exit_reason ENUM('normal_exit', 'lunch_break', 'meeting', 'emergency', 'end_of_shift', 'unknown'),
    
    -- Detection location
    camera_id VARCHAR(50),
    zone_name VARCHAR(100),
    detection_confidence FLOAT,
    
    -- Analysis
    duration_outside_minutes INTEGER,            -- If re-entry
    is_authorized BOOLEAN,                       -- Whether exit was expected
    
    created_at DATETIME DEFAULT NOW(),
    
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (attendance_record_id) REFERENCES attendance_records(id),
    INDEX idx_timefence_employee_timestamp (employee_id, event_timestamp),
    INDEX idx_timefence_event_type_timestamp (event_type, event_timestamp)
);
```

**Event Flow Examples**:
```
Entry: Employee detected at entry camera
→ TimeFenceLog {event_type: 'entry', is_authorized: true}

Normal Exit: Employee leaves through exit at shift end
→ TimeFenceLog {event_type: 'exit', is_authorized: true, exit_reason: 'end_of_shift'}

Lunch Break: Employee exits mid-shift
→ TimeFenceLog {event_type: 'exit', is_authorized: true, exit_reason: 'lunch_break'}

Re-entry: Employee re-enters after lunch
→ TimeFenceLog {event_type: 're_entry', duration_outside_minutes: 45}

Suspicious: Employee exits before shift start
→ TimeFenceLog {event_type: 'suspicious_movement', is_authorized: false}
```

---

## Service Layer Architecture

### 1. AttendanceService (Main Orchestrator)

**Responsibilities**:
- Coordinate face detection → attendance marking
- Manage employee sessions (in-memory state)
- Handle check-in/check-out logic
- Apply grace periods
- Manage manual overrides

**Key Methods**:

#### `__init__(session: Session)`
```python
AttendanceService(db_session)
# Initializes:
# - identity_service: AWS Rekognition integration
# - exit_manager: Exit camera validation
# - employee_sessions: In-memory dict of active sessions
# - daily_stats: Check-in/out/late statistics
```

#### `process_face_detection(aws_rekognition_id, camera_id, confidence) → AttendanceCheckInResult`
Main entry point for face detection:

1. **Identify Employee** (AWS ID → Employee object)
   ```python
   employee = identity_service.identify_employee(aws_id, confidence)
   if not employee or confidence < 0.8:
       return AttendanceCheckInResult(success=False)
   ```

2. **Check Shift Window** (Is employee on shift?)
   ```python
   if not _is_on_shift_now(employee.shift, current_time):
       return AttendanceCheckInResult(success=False, message="Not on shift")
   ```

3. **Manage Sessions** (Track employee in frame)
   ```python
   if employee.id in employee_sessions:
       # Already tracked, just update
       session.update_detection(camera_id, confidence)
       return AttendanceCheckInResult(success=True, message="Already checked in")
   ```

4. **Get/Create Record** (Daily attendance record)
   ```python
   record = AttendanceRecordDAO.get_today_record(session, employee.id, today)
   if record and record.check_in_time:
       return AttendanceCheckInResult(success=True)  # Already checked in
   ```

5. **Calculate Status** (Present vs Late)
   ```python
   is_late = GracePeriodCalculator.is_late(current_time, employee.shift)
   status = AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT
   ```

6. **Persist Record** (Database)
   ```python
   record.check_in_time = current_time
   record.status = status
   session.commit()
   ```

7. **Track Session** (In-memory)
   ```python
   session_state = EmployeeSessionState(...)
   employee_sessions[employee.id] = session_state
   ```

**Return Example**:
```python
AttendanceCheckInResult(
    success=True,
    employee_id=5,
    employee_name="Rajesh Kumar",
    check_in_time=datetime(2025, 12, 20, 8, 3, 15),
    is_late=True,
    message="Checked in - Late",
    record_id=123
)
```

#### `process_exit_detection(aws_rekognition_id, camera_id, confidence, exit_reason) → AttendanceCheckOutResult`

1. **Identify Employee** (Same as check-in)
2. **Verify Exit Camera** (Is this the exit camera for employee's dept?)
3. **Validate Exit Timing** (Within shift hours + 30-min buffer?)
4. **Get Today's Record** (Ensure check-in exists)
5. **Update Check-Out** (Record check-out time)
6. **Create TimeFenceLog** (Log the exit event)
7. **Clear Session** (Remove from in-memory tracking)

#### `manual_override_attendance(employee_id, override_date, check_in_time, check_out_time, status, reason, override_user) → Dict`

Allows HR to correct records:
```python
service.manual_override_attendance(
    employee_id=5,
    override_date=date(2025, 12, 20),
    check_in_time=datetime(2025, 12, 20, 8, 0),
    check_out_time=datetime(2025, 12, 20, 16, 0),
    status=AttendanceStatus.PRESENT,
    reason="Camera downtime 8 AM - 9 AM",
    override_user="admin@company.com"
)
```

**Marks record as**:
- `is_manual_override = True`
- `override_by_user = admin@company.com`
- `override_reason = "Camera downtime..."`
- `override_timestamp = datetime.utcnow()`

---

### 2. IdentityServiceIntegration (AWS Rekognition Wrapper)

**Responsibilities**:
- Map AWS Rekognition IDs to Employee objects
- Cache mappings for fast lookup
- Handle confidence thresholds

**Key Methods**:

#### `identify_employee(aws_rekognition_id, confidence) → Optional[Employee]`
```python
# Minimum confidence check
if confidence < 0.8:
    return None

# Check cache first (O(1) lookup)
if aws_id in cache:
    emp = cache[aws_id]
    return emp if emp.is_active else None

# Fall back to database
emp = session.query(Employee).filter(
    Employee.aws_rekognition_id == aws_id,
    Employee.is_active == True
).first()

# Cache the result
if emp and aws_id not in cache:
    cache[aws_id] = emp

return emp
```

**Cache Strategy**:
- On-memory dictionary: `{aws_id → Employee}`
- Loaded on service init
- Refreshed periodically or on employee updates
- Fast O(1) lookup vs O(n) database query

#### `refresh_cache()`
Call when employees are added/updated:
```python
self.aws_rekognition_cache.clear()
self._load_cache()  # Reload all active employees
```

---

### 3. GracePeriodCalculator (Late Detection Logic)

**Responsibilities**:
- Determine if check-in is late
- Calculate minutes late
- Handle grace period logic

**Key Methods**:

#### `is_late(check_in_time, shift) → bool`
```
Shift start: 08:00
Grace period: 5 minutes
Grace time: 08:05

if check_in_time <= 08:05:  return False  # On time
else:                       return True   # Late
```

#### `calculate_late_minutes(check_in_time, shift) → int`
```
Shift: 08:00 - 16:00, grace_period = 5
Check-in: 08:10
Grace time: 08:05
Late minutes = 10 - 5 = 5 minutes
```

---

### 4. ExitDetectionManager (Exit Validation)

**Responsibilities**:
- Validate exit camera assignments
- Check exit timing
- Detect unauthorized exits

**Key Methods**:

#### `is_exit_detection(employee, camera_id) → bool`
```python
# Get exit camera for employee's department
exit_camera = exit_cameras[employee.department_id]

# Check if detection is at exit camera
return camera_id == exit_camera
```

#### `process_exit(employee, camera_id, current_time) → Tuple[bool, Optional[str]]`
```
Validate:
1. Is this the exit camera? → is_exit_detection()
2. Is it during shift hours? → shift.start_time <= current_time.time() <= shift.end_time + 30min
3. Is employee checked in? → record.check_in_time exists

Return: (is_valid, reason_if_invalid)
```

---

### 5. AttendanceReportingUtility (Analytics)

**Responsibilities**:
- Generate shift-wise reports
- Generate department-wise reports
- Generate late entries reports
- Calculate monthly statistics

**Key Methods**:

#### `get_shift_wise_report(report_date) → List[Dict]`
For each shift:
- Get all employees in shift
- Get attendance records for date
- Count by status (Present, Late, etc.)
- Calculate attendance percentage

#### `get_department_wise_report(report_date) → List[Dict]`
For each department:
- Get all employees in department
- Get attendance records for date
- Count by status
- Calculate attendance percentage

#### `get_late_entries_report(report_date) → List[Dict]`
Get all late entries with:
- Employee name, department
- Check-in time
- Late minutes (how many minutes after grace period)
- Whether it was manually overridden

---

## API Reference

### Authentication
All endpoints require proper API key or authentication (to be configured in your FastAPI setup).

### Error Handling
All endpoints return proper HTTP status codes:
- `200` - Success
- `400` - Bad request (validation error)
- `404` - Not found
- `500` - Server error

---

### Face Detection Endpoint

#### POST `/api/attendance/process-face-detection`

**Purpose**: Process face detection from cameras (entry point from Module 1)

**Request**:
```json
{
  "aws_rekognition_id": "person-12345",
  "camera_id": "ENTRY_CAM_01",
  "confidence": 0.95,
  "is_exit": false
}
```

**Response (Check-In Success)**:
```json
{
  "success": true,
  "employee_id": 5,
  "employee_name": "Rajesh Kumar",
  "check_in_time": "2025-12-20T08:03:15",
  "is_late": false,
  "message": "Checked in - On time"
}
```

**Response (Check-In Already Done)**:
```json
{
  "success": true,
  "employee_id": 5,
  "employee_name": "Rajesh Kumar",
  "check_in_time": "2025-12-20T08:03:15",
  "is_late": false,
  "message": "Already checked in"
}
```

**Response (Unknown Employee)**:
```json
{
  "success": false,
  "message": "Unknown employee or low confidence match"
}
```

---

### Manual Override Endpoint

#### POST `/api/attendance/override`

**Purpose**: Manually create or update attendance record (HR function)

**Request**:
```json
{
  "employee_id": 5,
  "attendance_date": "2025-12-20",
  "check_in_time": "2025-12-20T08:00:00",
  "check_out_time": "2025-12-20T16:00:00",
  "status": "Present",
  "reason": "Camera downtime during shift - verified manually",
  "override_user": "hr@company.com"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Attendance record updated",
  "record_id": 123,
  "employee_id": 5,
  "status": "Present"
}
```

---

### Reporting Endpoints

#### GET `/api/attendance/reports?report_type=summary`

**Purpose**: Get today's attendance summary

**Response**:
```json
{
  "success": true,
  "timestamp": "2025-12-20T17:30:00",
  "data": {
    "date": "2025-12-20",
    "total_employees": 150,
    "present": 145,
    "late": 3,
    "half_day": 1,
    "absent": 1,
    "leave": 0,
    "currently_in_frame": 45,
    "check_ins_today": 145,
    "check_outs_today": 130,
    "late_entries": 3
  }
}
```

#### GET `/api/attendance/reports?report_type=shift-wise&report_date=2025-12-20`

**Purpose**: Shift-wise attendance breakdown

**Response**:
```json
{
  "success": true,
  "data": {
    "shifts": [
      {
        "shift_name": "Morning",
        "shift_hours": "08:00:00 - 16:00:00",
        "total_employees": 100,
        "present": 97,
        "late": 2,
        "half_day": 1,
        "absent": 0,
        "leave": 0,
        "attendance_percentage": 98.0
      }
    ]
  }
}
```

#### GET `/api/attendance/reports?report_type=department-wise&report_date=2025-12-20`

**Purpose**: Department-wise attendance breakdown

**Response**:
```json
{
  "success": true,
  "data": {
    "departments": [
      {
        "department_name": "Production Floor",
        "location": "Floor 1, Section A",
        "manager": "John Manager",
        "total_employees": 50,
        "present": 48,
        "late": 2,
        "half_day": 0,
        "absent": 0,
        "leave": 0,
        "attendance_percentage": 96.0
      }
    ]
  }
}
```

---

### Shift Management Endpoints

#### POST `/api/attendance/shifts`

**Purpose**: Create shift

**Request**:
```json
{
  "shift_name": "Morning",
  "start_time": "08:00:00",
  "end_time": "16:00:00",
  "grace_period_minutes": 5,
  "break_start": "12:00:00",
  "break_end": "13:00:00",
  "break_duration_minutes": 60
}
```

**Response**:
```json
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

#### GET `/api/attendance/shifts`

**Response**: Array of shift objects

#### GET `/api/attendance/shifts/{shift_id}`

**Response**: Single shift object

---

### Department Management Endpoints

#### POST `/api/attendance/departments`

**Request**:
```json
{
  "dept_name": "Production Floor",
  "shift_id": 1,
  "manager_name": "John Manager",
  "location": "Floor 1, Section A",
  "entry_camera_id": "ENTRY_CAM_01",
  "exit_camera_id": "EXIT_CAM_01"
}
```

#### GET `/api/attendance/departments`

Returns list of all departments

#### GET `/api/attendance/departments/{dept_id}`

Returns single department

---

### Status Endpoints

#### GET `/api/attendance/summary`

Quick status of today's attendance

#### GET `/api/attendance/health`

Health check endpoint
```json
{
  "status": "healthy",
  "timestamp": "2025-12-20T17:30:00",
  "service": "attendance_module"
}
```

---

## Integration with Module 1

### Data Flow from Identity Service

Module 1 detects face and identifies employee:

```python
# In Module 1's face detection processing
from detection_system.attendance_service import AttendanceService

db = SessionLocal()
attendance_service = AttendanceService(db)

# When face is identified
identity_result = module1_identity_service.identify(face_embedding)
if identity_result.matches_employee:
    # Send to attendance module
    attendance_result = attendance_service.process_face_detection(
        aws_rekognition_id=identity_result.aws_id,
        camera_id="ENTRY_CAM_01",
        confidence=identity_result.confidence
    )
    
    logger.info(f"Attendance: {attendance_result.message}")

db.close()
```

### Critical Integration Points

1. **AWS Rekognition ID** (Employee.aws_rekognition_id)
   - Must be populated for each employee
   - Unique identifier from AWS Rekognition
   - Used to match detected faces to employees

2. **Confidence Threshold**
   - Module 1 must provide confidence scores
   - Minimum 0.8 required for attendance (configurable)
   - Low confidence detections ignored

3. **Camera ID**
   - Must match Department entry_camera_id or exit_camera_id
   - Used to determine entry vs exit
   - Used for TimeFenceLog tracking

---

## Business Logic

### Check-In Logic

```python
def process_face_detection():
    1. Identify employee (AWS ID → Employee)
    2. Check confidence >= 0.8
    3. Check employee is active
    4. Check employee is on shift
    5. Check today's attendance record doesn't exist
    6. Calculate status:
       if check_in_time > start_time + grace_period:
           status = LATE
       else:
           status = PRESENT
    7. Create AttendanceRecord
    8. Create EmployeeSessionState
    9. Return success
```

### Check-Out Logic

```python
def process_exit_detection():
    1. Identify employee
    2. Verify this is the exit camera
    3. Verify exit is within shift hours
    4. Get today's attendance record (ensure check-in exists)
    5. Update check_out_time
    6. Calculate actual_duration_minutes
    7. Create TimeFenceLog
    8. Clear EmployeeSessionState
    9. Return success
```

### Late Detection Logic

```
Shift: start=08:00, grace_period=5
Grace cutoff: 08:05

Check-in at 08:03 → Present (3 < 5)
Check-in at 08:05 → Present (5 ≤ 5)
Check-in at 08:06 → Late (6 > 5)
```

### Manual Override Logic

```python
def manual_override():
    1. Get or create AttendanceRecord
    2. Apply overrides:
       - check_in_time (if provided)
       - check_out_time (if provided)
       - status (if provided, else auto-calculate)
    3. Mark record as manual_override = True
    4. Record override metadata:
       - override_by_user (HR user)
       - override_reason (camera downtime, etc.)
       - override_timestamp (when override applied)
    5. Commit to database
    6. Log the action
```

---

## Performance Optimization

### 1. In-Memory Session Caching

**Why**: Avoid database queries for every face detection

**How**:
```python
# In EmployeeSessionState
employee_sessions = {
    employee_id → EmployeeSessionState(
        first_detection_time,
        last_detection_time,
        detection_count,
        ...
    )
}

# Session stays in memory for 5 minutes (300 seconds)
# If face detected multiple times, only 1 database write
```

**Benefit**: 
- 30 FPS camera → 30 detections/second
- With session caching → 1 database write per ~300 seconds
- 98%+ reduction in database writes

### 2. Identity Cache

**Why**: AWS Rekognition ID → Employee mapping

**How**:
```python
aws_rekognition_cache = {
    "person-12345" → Employee(id=5, ...),
    "person-67890" → Employee(id=6, ...),
    ...
}
```

**Benefit**: O(1) lookup vs database query

### 3. Strategic Indexing

```sql
-- Critical indexes on AttendanceRecord
CREATE INDEX idx_attendance_employee_date 
    ON attendance_records(employee_id, attendance_date);

CREATE INDEX idx_attendance_date_status 
    ON attendance_records(attendance_date, status);

CREATE INDEX idx_attendance_manual_override 
    ON attendance_records(is_manual_override, attendance_date);

-- Fast queries:
-- Find today's attendance: O(log n)
-- Find all late entries: O(log n)
-- Find manual overrides: O(log n)
```

### 4. Database Connection Pooling

```python
# Configure in your app
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@localhost/factory',
    pool_size=20,           # Connection pool size
    max_overflow=40,        # Max overflow connections
    pool_recycle=3600,      # Recycle connections hourly
    pool_pre_ping=True      # Test connections before use
)
```

### 5. Asynchronous Processing

For non-critical operations:
```python
# Non-critical: TimeFenceLog creation
# Could be queued and processed async
# Critical: AttendanceRecord creation (synchronous)
```

---

## Error Handling

### Graceful Degradation

```python
try:
    employee = identity_service.identify_employee(aws_id, confidence)
    if not employee:
        logger.warning(f"Unknown employee: {aws_id}")
        return AttendanceCheckInResult(success=False)
        
    record = AttendanceRecordDAO.get_today_record(session, employee.id, today)
    if not record:
        record = AttendanceRecord(...)  # Create new
    
    session.commit()
    
except DatabaseError as e:
    logger.error(f"Database error: {str(e)}")
    session.rollback()
    return AttendanceCheckInResult(success=False, message="Database error")
    
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    session.rollback()
    return AttendanceCheckInResult(success=False, message="Unexpected error")
```

### Common Error Scenarios

| Error | Cause | Resolution |
|-------|-------|-----------|
| "Unknown employee" | AWS ID not in database | Ensure employee.aws_rekognition_id is set |
| "Not on shift" | Detection outside shift hours | Check shift times are correct |
| "Not at exit point" | Exit at wrong camera | Verify department.exit_camera_id |
| "Database error" | Connection lost | Check PostgreSQL is running |
| "Low confidence" | Face match < 0.8 | Adjust confidence threshold or improve image |

---

## Testing Guide

### Unit Tests

```python
# Test grace period calculation
def test_grace_period_on_time():
    shift = Shift(start_time=time(8, 0), grace_period_minutes=5)
    check_in = datetime(2025, 12, 20, 8, 3)
    assert not GracePeriodCalculator.is_late(check_in, shift)

def test_grace_period_late():
    shift = Shift(start_time=time(8, 0), grace_period_minutes=5)
    check_in = datetime(2025, 12, 20, 8, 6)
    assert GracePeriodCalculator.is_late(check_in, shift)

# Test identity matching
def test_identify_employee():
    service = IdentityServiceIntegration(db_session)
    employee = service.identify_employee("person-123", 0.95)
    assert employee.id == 5
    
    # Low confidence
    employee = service.identify_employee("person-123", 0.7)
    assert employee is None  # Below threshold

# Test check-in logic
def test_check_in_first_time():
    service = AttendanceService(db_session)
    result = service.process_face_detection("person-123", "ENTRY_01", 0.95)
    assert result.success
    assert result.is_late == False
    assert result.record_id is not None

def test_check_in_already_done():
    # Create record first
    service.process_face_detection("person-123", "ENTRY_01", 0.95)
    # Second detection
    result = service.process_face_detection("person-123", "ENTRY_01", 0.95)
    assert result.success
    assert result.message == "Already checked in"
```

### Integration Tests

```python
# Test full flow: check-in → check-out
def test_full_attendance_flow():
    service = AttendanceService(db_session)
    
    # Morning: Check-in
    check_in_result = service.process_face_detection("person-123", "ENTRY_01", 0.95)
    assert check_in_result.success
    assert check_in_result.is_late == False
    
    # Afternoon: Check-out
    check_out_result = service.process_exit_detection("person-123", "EXIT_01", 0.94)
    assert check_out_result.success
    assert check_out_result.duration_minutes > 400  # ~8 hours
    
    # Verify record
    record = AttendanceRecordDAO.get_today_record(db_session, check_in_result.employee_id)
    assert record.check_in_time is not None
    assert record.check_out_time is not None
    assert record.status == AttendanceStatus.PRESENT
```

### End-to-End Tests

```bash
# Using curl
curl -X POST http://localhost:8000/api/attendance/process-face-detection \
  -H "Content-Type: application/json" \
  -d '{"aws_rekognition_id":"person-123","camera_id":"ENTRY_01","confidence":0.95,"is_exit":false}'

# Verify response
# {"success":true,"employee_id":5,"employee_name":"Rajesh Kumar",...}
```

---

## Deployment Guide

### Prerequisites

- PostgreSQL 12+ with proper access
- Python 3.8+ with FastAPI installed
- SQLAlchemy 2.0+ configured
- Module 1: Identity Service operational

### Step 1: Database Setup

```bash
# Create database
createdb factory_attendance

# Create user
createuser factory_user -P

# Grant privileges
psql factory_attendance
GRANT ALL ON SCHEMA public TO factory_user;

# Run migrations (if using Alembic)
alembic upgrade head
```

### Step 2: Update Requirements

```bash
pip install sqlalchemy>=2.0
pip install postgresql
pip install fastapi
pip install pydantic
```

### Step 3: Configure Application

In `settings.py`:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://factory_user:password@localhost:5432/factory_attendance"

# Attendance module config
ATTENDANCE_CONFIG = {
    'session_timeout_seconds': 300,        # 5 minutes
    'confidence_threshold': 0.80,           # Minimum face confidence
    'grace_period_minutes': 5,              # Default grace period
    'exit_detection_buffer_minutes': 30,    # Time after shift end to allow exit
    'cleanup_retention_days': 365           # Keep 1 year of logs
}
```

### Step 4: Initialize on Startup

In `main.py`:
```python
from fastapi import FastAPI
from detection_system.attendance_endpoints import router, init_attendance_module

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    init_attendance_module(db)
    db.close()
    logger.info("Attendance module initialized")

app.include_router(router)
```

### Step 5: Test

```bash
# Start application
python -m uvicorn main:app --reload

# Test endpoint
curl http://localhost:8000/api/attendance/health

# Should respond with
# {"status":"healthy","timestamp":"...","service":"attendance_module"}
```

### Step 6: Monitor Logs

```bash
# Watch application logs
tail -f app.log | grep attendance

# Monitor database
psql factory_attendance
SELECT COUNT(*) FROM attendance_records;
SELECT COUNT(*) FROM time_fence_logs;
```

---

**Next Steps**: See `MODULE_3_QUICK_START.md` for immediate integration, or `MODULE_3_DEPLOYMENT_CHECKLIST.md` for production deployment.
