<!-- Module 3: Attendance System - Visual Reference Guide -->

# Module 3: Attendance System - Visual Reference & Architecture Diagrams

**Document Status**: Production-Ready | **Last Updated**: December 2025

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAMERA FEEDS (Multiple Locations)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Entry Cam 1 │  │ Entry Cam 2 │  │ Exit Cam 1  │  │ Exit Cam 2  ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘│
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────┘
          │                 │                 │                 │
          ├─────────────────┼─────────────────┼─────────────────┤
          │ Face Detection Data               │                 │
          │ (Image Frames)                    │                 │
          ↓                                   ↓                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│            MODULE 1: IDENTITY SERVICE (AWS Rekognition)             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Face Detection & Recognition                                  │ │
│  │ - Compare faces in frame to known person IDs                  │ │
│  │ - Return: aws_rekognition_id, confidence, coordinates         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              │ {
                              │   "aws_rekognition_id": "person-123",
                              │   "confidence": 0.95,
                              │   "camera_id": "ENTRY_CAM_01",
                              │   "is_exit": false
                              │ }
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│         MODULE 3: ATTENDANCE SERVICE (Main Processing)              │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. IDENTIFY EMPLOYEE                                         │   │
│  │    AWS Rekognition ID → Employee Object                      │   │
│  │    Check: active, aws_id_cached or db                        │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. VALIDATE SHIFT WINDOW                                     │   │
│  │    Is employee on shift right now?                           │   │
│  │    start_time ≤ now ≤ end_time + 30min_buffer               │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. CHECK SESSION STATE                                       │   │
│  │    Is employee already tracked in frame?                     │   │
│  │    Check: employee_sessions dict (in-memory)                │   │
│  │    If yes: update, return (avoid duplicate DB write)        │   │
│  │    If no: continue                                           │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 4. GET/CREATE ATTENDANCE RECORD                              │   │
│  │    Get today's record from DB                                │   │
│  │    If exists + has check_in: already done, return            │   │
│  │    If not exists: create new record                          │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 5. CALCULATE STATUS                                          │   │
│  │    if check_in_time > start_time + grace_period:            │   │
│  │        status = LATE                                         │   │
│  │    else:                                                      │   │
│  │        status = PRESENT                                      │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 6. PERSIST TO DATABASE                                       │   │
│  │    Create/Update AttendanceRecord                            │   │
│  │    Fields: check_in_time, status, camera_id, confidence     │   │
│  │    Commit to PostgreSQL                                      │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 7. TRACK IN-MEMORY SESSION                                   │   │
│  │    Create EmployeeSessionState                               │   │
│  │    Store in employee_sessions dict                           │   │
│  │    Timeout: 300 seconds (5 minutes)                          │   │
│  └──────────────────┬──────────────────────────────────────────┘   │
│                     ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 8. RETURN SUCCESS                                            │   │
│  │    {success, employee_id, name, check_in_time, is_late}     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
                      │ FastAPI Response
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│  API RESPONSE TO CALLER (Module 1 or External System)              │
│  {                                                                   │
│    "success": true,                                                │
│    "employee_id": 5,                                               │
│    "employee_name": "Rajesh Kumar",                               │
│    "check_in_time": "2025-12-20T08:03:15",                       │
│    "is_late": false,                                              │
│    "message": "Checked in - On time"                             │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📈 Data Flow: Face Detection → Attendance Check-In

```
START: Face Detected in Frame
│
├─ Input: aws_rekognition_id, camera_id, confidence
│  Example: person-123, ENTRY_CAM_01, 0.95
│
├─ Step 1: Identify Employee (AWS ID → Employee)
│  ├─ Check cache: aws_id in cache?
│  │  ├─ YES → Get Employee from cache (O(1))
│  │  └─ NO → Query DB (O(log n)), add to cache
│  └─ Employee = {id: 5, name: "Rajesh", department_id: 1, shift_id: 1}
│
├─ Step 2: Validate Employee
│  ├─ Check confidence >= 0.8? YES ✓
│  ├─ Check is_active? YES ✓
│  └─ Continue
│
├─ Step 3: Get Shift Details
│  ├─ Query Shift(id=1)
│  ├─ Shift = {start_time: 08:00, end_time: 16:00, grace_period: 5}
│  └─ Now = 08:03 (current time)
│
├─ Step 4: Check if On Shift
│  ├─ Is 08:03 between 08:00 and 16:00? YES ✓
│  ├─ Check 5-min grace before start? N/A
│  ├─ Check 30-min buffer after end? N/A
│  └─ Employee is ON SHIFT ✓
│
├─ Step 5: Check Session State
│  ├─ Is employee.id (5) in employee_sessions dict? NO
│  ├─ Session was empty, so this is first detection
│  └─ Continue to database check
│
├─ Step 6: Query Today's Record
│  ├─ SELECT * FROM attendance_records
│  │    WHERE employee_id = 5 AND attendance_date = 2025-12-20
│  ├─ Result: No record found
│  └─ Will create new record
│
├─ Step 7: Calculate Status
│  ├─ Grace cutoff = 08:00 + 5min = 08:05
│  ├─ Check-in time = 08:03
│  ├─ Is 08:03 > 08:05? NO
│  └─ Status = PRESENT (not late)
│
├─ Step 8: Create AttendanceRecord
│  ├─ INSERT INTO attendance_records (
│  │    employee_id, attendance_date, check_in_time,
│  │    status, first_detection_camera, detection_confidence, ...
│  │  ) VALUES (
│  │    5, 2025-12-20, 2025-12-20 08:03:15,
│  │    'Present', 'ENTRY_CAM_01', 0.95, ...
│  │  )
│  └─ record_id = 123
│
├─ Step 9: Create Session State (In-Memory)
│  ├─ employee_sessions[5] = EmployeeSessionState {
│  │    employee_id: 5,
│  │    name: "Rajesh Kumar",
│  │    first_detection_time: 08:03:15,
│  │    last_detection_time: 08:03:15,
│  │    detection_count: 1,
│  │    is_in_frame: True,
│  │    session_timeout_seconds: 300
│  │  }
│  └─ Subsequent detections in next 5 min just update this
│
├─ Step 10: Update Statistics
│  ├─ daily_stats['total_check_ins'] += 1 → 1
│  ├─ daily_stats['total_late_entries'] += 0 (not late)
│  └─ daily_stats['last_updated'] = now
│
└─ END: Return Success Response
   └─ {
      "success": true,
      "employee_id": 5,
      "employee_name": "Rajesh Kumar",
      "check_in_time": "2025-12-20T08:03:15",
      "is_late": false,
      "message": "Checked in - On time",
      "record_id": 123
    }
```

---

## 🚪 Data Flow: Exit Detection → Check-Out

```
START: Face Detected at Exit Camera
│
├─ Input: aws_rekognition_id, camera_id="EXIT_CAM_01", confidence=0.94
│
├─ Step 1: Identify Employee (Same as check-in)
│  └─ Employee = {id: 5, name: "Rajesh Kumar", dept_id: 1}
│
├─ Step 2: Validate Exit Camera
│  ├─ Query Department(id=1)
│  ├─ Department.exit_camera_id = "EXIT_CAM_01"
│  ├─ Is camera_id == exit_camera_id? YES ✓
│  └─ This is the correct exit camera
│
├─ Step 3: Validate Exit Timing
│  ├─ Shift: 08:00 - 16:00
│  ├─ Current time: 16:05 (5 min after shift end)
│  ├─ Allow exit within shift + 30-min buffer? YES ✓
│  │  (16:05 is within 16:00 + 30min = 16:30)
│  └─ Valid exit time
│
├─ Step 4: Get Today's Attendance Record
│  ├─ SELECT * FROM attendance_records
│  │    WHERE employee_id = 5 AND attendance_date = 2025-12-20
│  ├─ Result found: record_id=123, check_in_time=08:03:15
│  ├─ Check if already checked out? NO
│  └─ Ready to update
│
├─ Step 5: Update Check-Out Time
│  ├─ UPDATE attendance_records
│  │    SET check_out_time = 2025-12-20 16:05:30,
│  │        check_out_type = 'auto_face',
│  │        last_detection_camera = 'EXIT_CAM_01',
│  │        actual_duration_minutes = 482
│  │    WHERE id = 123
│  └─ Record updated
│
├─ Step 6: Create TimeFenceLog (Exit Event)
│  ├─ INSERT INTO time_fence_logs (
│  │    employee_id, attendance_record_id, event_timestamp,
│  │    event_type, exit_reason, camera_id, is_authorized
│  │  ) VALUES (
│  │    5, 123, 2025-12-20 16:05:30,
│  │    'exit', 'end_of_shift', 'EXIT_CAM_01', true
│  │  )
│  └─ Audit trail created
│
├─ Step 7: Clear In-Memory Session
│  ├─ if employee_id (5) in employee_sessions:
│  │    del employee_sessions[5]
│  └─ Session cleared, stop tracking
│
├─ Step 8: Update Statistics
│  ├─ daily_stats['total_check_outs'] += 1
│  └─ daily_stats['last_updated'] = now
│
└─ END: Return Check-Out Response
   └─ {
      "success": true,
      "employee_id": 5,
      "check_out_time": "2025-12-20T16:05:30",
      "duration_minutes": 482,
      "message": "Successfully checked out"
    }
```

---

## 🔄 Session State Machine Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION STATE MACHINE                        │
└─────────────────────────────────────────────────────────────────┘

        START (Employee Not In Frame)
            │
            │ Face detected for first time
            │ (aws_rekognition_id, camera_id, confidence)
            ↓
    ┌───────────────────────┐
    │  CREATE SESSION       │
    │  EmployeeSessionState │
    │  state = ACTIVE       │
    │  timeout = 300 sec    │
    └───────────────────┬───┘
            │           
            │ (Session exists in memory)
            │
            ├──────────────────────────────────────────┐
            │                                          │
            │ Another face detection (within 300s)     │
            │ same employee                            │
            │                                          │
            ├──UPDATE SESSION ONLY──┐                  │
            │                       ↓                  │
            │               last_detection_time = now  │
            │               detection_count += 1       │
            │               (NO DB WRITE)              │
            │                       │                  │
            │                       └─→ (Stay in same session)
            │                          │
            │                          └─ REPEAT (if detected again within 300s)
            │
            │ 300 seconds pass with NO detection
            │ (Session timeout)
            │
            ├──→ SESSION EXPIRES
                 │
                 └─→ Remove from employee_sessions dict
                     └─ END (Back to not-in-frame)

---

EXAMPLE TIMELINE:

08:00:00 → First detection (ENTRY_CAM_01)
           └─ CREATE session, write to DB
           
08:00:02 → Second detection (ENTRY_CAM_01) - 2 seconds later
           └─ UPDATE session only (NO DB write)
           
08:00:05 → Third detection (ENTRY_CAM_02) - 5 seconds later
           └─ UPDATE session only (NO DB write)
           
08:00:10 → Detection outside frame (no face)
           └─ Session expires after 300s (5 min) of no detection
           
08:05:15 → Face reappears after 5 minutes
           └─ CREATE NEW session, write to DB
           
            (But we won't create new check-in record because
             attendance_record already has check_in_time from 08:00:00)
```

---

## 💾 Database Schema Relationship Diagram

```
┌──────────────────┐
│    shifts        │
├──────────────────┤
│ id (PK)          │◄──────┐
│ shift_name       │       │ (1:N)
│ start_time       │       │
│ end_time         │       │
│ grace_period_min │       │
└──────────────────┘       │
                           │
        ┌─────────────────┐ │
        │  departments    │ │
        ├─────────────────┤ │
        │ id (PK)         │─┘
        │ shift_id (FK)───┘
        │ dept_name       │
        │ entry_camera_id │
        │ exit_camera_id  │
        └────────┬────────┘
                 │
                 │ (1:N)
                 │
        ┌────────▼────────┐
        │   employees     │
        ├─────────────────┤
        │ id (PK)         │
        │ employee_id     │
        │ name            │
        │ department_id──►│─→ departments
        │ shift_id────►│─→ shifts
        │ aws_rekog_id│
        └────────┬────────┘
                 │
                 │ (1:N)
                 │
        ┌────────▼──────────────────┐
        │  attendance_records       │
        ├───────────────────────────┤
        │ id (PK)                   │
        │ employee_id (FK)──────────┤─→ employees
        │ attendance_date           │
        │ check_in_time             │
        │ check_out_time            │
        │ status (enum)             │
        │ is_manual_override        │
        │ override_by_user          │
        │ override_reason           │
        │ override_timestamp        │
        │ shift_duration_minutes    │
        │ actual_duration_minutes   │
        │ grace_period_applied      │
        └────────┬──────────────────┘
                 │
                 │ (1:N)
                 │
        ┌────────▼──────────────────┐
        │   time_fence_logs         │
        ├───────────────────────────┤
        │ id (PK)                   │
        │ employee_id (FK)──────────┤─→ employees
        │ attendance_record_id──────┤─→ attendance_records
        │ event_timestamp           │
        │ event_type (enum)         │
        │ exit_reason (enum)        │
        │ camera_id                 │
        │ duration_outside_minutes  │
        │ is_authorized             │
        └───────────────────────────┘
```

---

## 📊 Attendance Status Decision Tree

```
                    EMPLOYEE DETECTED
                           │
                ┌──────────┴──────────┐
                │                     │
         Is on shift?            Is on shift?
                │ YES               │ NO
                │                   │
                ↓                   ↓
        Check-in Process     Skip (Not on shift)
                │                   │
        Has check_in_time?          └───→ Return error
                │ YES               "Not on shift"
                │ NO (first time)
                ↓
        Get check_in_time = now
                │
                ├─ Check_in_time after
                │  start_time + grace_period?
                │
                ├─ YES (Late)
                │  └─→ Status = LATE
                │       grace_period_applied = true
                │
                └─ NO (On time)
                   └─→ Status = PRESENT
                        grace_period_applied = false
                           │
                           ↓
                    Create AttendanceRecord
                    with status (PRESENT|LATE)
                           │
                           ↓
                    RETURN SUCCESS
```

---

## 🔒 Manual Override Flow Diagram

```
TRIGGER: HR needs to correct attendance (camera downtime, etc.)
    │
    ├─ POST /api/attendance/override
    │
    ├─ Input: {
    │    employee_id: 5,
    │    attendance_date: 2025-12-20,
    │    check_in_time: 2025-12-20T08:00:00,
    │    check_out_time: 2025-12-20T16:00:00,
    │    status: "Present",
    │    reason: "Camera downtime 8 AM - 10 AM",
    │    override_user: "hr@company.com"
    │  }
    │
    ├─ PROCESS:
    │   1. Get or create AttendanceRecord
    │   2. Apply overrides:
    │      └─ check_in_time ← 08:00:00 (override)
    │      └─ check_out_time ← 16:00:00 (override)
    │      └─ status ← "Present" (override)
    │   3. Mark record as manual:
    │      └─ is_manual_override = true
    │      └─ override_by_user = "hr@company.com"
    │      └─ override_reason = "Camera downtime..."
    │      └─ override_timestamp = now
    │   4. Commit to database
    │
    ├─ DATABASE UPDATE:
    │  UPDATE attendance_records SET
    │    check_in_time = '2025-12-20 08:00:00',
    │    check_out_time = '2025-12-20 16:00:00',
    │    status = 'Present',
    │    is_manual_override = true,
    │    override_by_user = 'hr@company.com',
    │    override_reason = 'Camera downtime 8 AM - 10 AM',
    │    override_timestamp = now()
    │  WHERE id = 123
    │
    └─ RESPONSE: {
       "success": true,
       "message": "Attendance record updated",
       "record_id": 123,
       "status": "Present"
     }
```

---

## 📈 Reporting Flow Diagram

```
GET /api/attendance/reports?report_type=shift-wise&report_date=2025-12-20
    │
    ├─ SHIFT-WISE REPORT
    │   │
    │   ├─ For each Shift in DB:
    │   │   │
    │   │   ├─ Get all Employees with shift_id
    │   │   ├─ Get all AttendanceRecords for date with those employees
    │   │   │
    │   │   ├─ Count by status:
    │   │   │   ├─ present = COUNT(status='Present')
    │   │   │   ├─ late = COUNT(status='Late')
    │   │   │   ├─ half_day = COUNT(status='Half-day')
    │   │   │   ├─ absent = COUNT(status='Absent')
    │   │   │   └─ leave = COUNT(status='Leave')
    │   │   │
    │   │   └─ Calculate:
    │   │       └─ attendance_percentage = (present + late) / total_employees * 100
    │   │
    │   └─ Return array of shift data
    │
    ├─ DEPARTMENT-WISE REPORT (similar flow)
    │   └─ Group by Department instead of Shift
    │
    ├─ LATE-ENTRIES REPORT
    │   │
    │   ├─ Get all records with status='Late'
    │   │
    │   ├─ For each late record:
    │   │   ├─ Calculate late_minutes:
    │   │   │   late_minutes = (check_in_time - grace_cutoff) in minutes
    │   │   │
    │   │   └─ Add to list: {
    │   │       employee_id, name, department,
    │   │       check_in_time, late_minutes, grace_period
    │   │     }
    │   │
    │   └─ Sort by late_minutes DESC (worst first)
    │
    └─ RESPONSE: JSON with report data
```

---

## 🔍 Index Strategy Diagram

```
CRITICAL QUERIES vs INDEXES

┌─────────────────────────────────────────────────────────────┐
│ Query 1: Get today's record for employee                   │
│ SELECT * FROM attendance_records                            │
│ WHERE employee_id = 5 AND attendance_date = 2025-12-20     │
│                                                             │
│ Index: idx_attendance_employee_date(employee_id, date)    │
│ Performance: O(log n) = ~3 comparisons for 1M records      │
│ Without index: O(n) = 500K comparisons on average         │
│ Benefit: 166,666x faster                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Query 2: Get all late entries for a date                   │
│ SELECT * FROM attendance_records                            │
│ WHERE attendance_date = 2025-12-20 AND status = 'Late'     │
│                                                             │
│ Index: idx_attendance_date_status(date, status)           │
│ Performance: O(log n) = ~3 comparisons, filtered subset   │
│ Without index: O(n) = full table scan                     │
│ Benefit: 1,000x+ faster                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Query 3: Get manual overrides for date                      │
│ SELECT * FROM attendance_records                            │
│ WHERE is_manual_override = true AND attendance_date = d    │
│                                                             │
│ Index: idx_attendance_manual_override(override, date)      │
│ Performance: O(log n) + binary search on bool              │
│ Without index: Full table scan                             │
│ Benefit: 1,000x+ faster                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Query 4: Identity lookup                                    │
│ SELECT * FROM employees                                     │
│ WHERE aws_rekognition_id = 'person-123'                    │
│                                                             │
│ Index: idx_employee_aws_id(aws_rekognition_id)            │
│ Performance: O(1) direct lookup                            │
│ (But with caching: O(1) memory access = microseconds)     │
│ Benefit: Database access avoided entirely                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Reporting Examples Output

### Shift-Wise Report
```
┌─────────────────────────────────────────────────────────────────┐
│ SHIFT-WISE ATTENDANCE REPORT - 2025-12-20                       │
├─────────────────────────────────────────────────────────────────┤
│ MORNING SHIFT (08:00 - 16:00)                                   │
│   Total Employees: 100                                           │
│   Present: 97  Late: 2  Half-day: 1  Absent: 0  Leave: 0       │
│   Attendance: 98.0%                                              │
│                                                                  │
│ EVENING SHIFT (16:00 - 00:00)                                  │
│   Total Employees: 50                                            │
│   Present: 47  Late: 1  Half-day: 2  Absent: 0  Leave: 0       │
│   Attendance: 98.0%                                              │
│                                                                  │
│ NIGHT SHIFT (00:00 - 08:00)                                    │
│   Total Employees: 30                                            │
│   Present: 28  Late: 0  Half-day: 0  Absent: 2  Leave: 0       │
│   Attendance: 93.3%                                              │
│                                                                  │
│ TOTAL: 180 employees | 172 present | 3 late | 3 other | 98.3%  │
└─────────────────────────────────────────────────────────────────┘
```

### Late Entries Report
```
┌──────────────────────────────────────────────────────────────────────┐
│ LATE ENTRIES REPORT - 2025-12-20                                     │
├──────────────────────────────────────────────────────────────────────┤
│ Employee ID │ Name              │ Dept    │ Check-in │ Late │ Grace   │
├─────────────┼───────────────────┼─────────┼──────────┼──────┼─────────┤
│ EMP-001     │ Rajesh Kumar      │ Prod    │ 08:08    │ 8m   │ 5m      │
│ EMP-012     │ Priya Sharma      │ Assembly│ 08:06    │ 6m   │ 5m      │
│ EMP-045     │ Arun Patel        │ QA      │ 08:11    │ 11m  │ 5m      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration Parameters Reference

```python
# In settings.py or config

ATTENDANCE_CONFIG = {
    # Timing
    'session_timeout_seconds': 300,         # 5 min (employee detection timeout)
    'exit_detection_buffer_minutes': 30,    # Allow exit 30 min after shift
    'grace_period_minutes': 5,              # Default late tolerance (per shift)
    
    # Detection thresholds
    'confidence_threshold': 0.80,           # Min face detection confidence
    'aws_rekognition_min_confidence': 0.8,  # AWS ID confidence
    
    # Database
    'cleanup_retention_days': 365,          # Keep 1 year of records
    'timefence_cleanup_days': 90,           # Keep 3 months of movement logs
    
    # Reporting
    'late_entries_threshold_minutes': 15,   # Consider late if > 15 min
    'half_day_threshold_hours': 4,          # Half-day if < 4 hours worked
    
    # Caching
    'cache_refresh_interval_hours': 24,     # Refresh employee cache daily
    'employee_session_ttl_seconds': 300,    # Session timeout
}
```

---

**For detailed implementation**: See MODULE_3_IMPLEMENTATION_GUIDE.md
