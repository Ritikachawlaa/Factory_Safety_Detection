# Backend-Frontend Integration Guide

## Overview

This document describes the complete integration of the Factory Safety Detection System backend with the Angular frontend for all 4 modules.

## Architecture

### API Structure

```
Backend API Base: http://localhost:8000/api

├── /module1 - Identity & Access Intelligence
│   ├── POST   /process-frame
│   ├── POST   /enroll
│   ├── GET    /employees
│   ├── POST   /access-logs
│   └── GET    /statistics
│
├── /module2 - Vehicle & Gate Management
│   ├── POST   /process-frame
│   ├── POST   /vehicle/register
│   ├── GET    /vehicles
│   ├── GET    /access-logs
│   └── GET    /statistics
│
├── /module3 - Attendance Tracking
│   ├── POST   /process-face-detection
│   ├── POST   /override
│   ├── GET    /reports
│   ├── GET    /summary
│   └── GET    /shifts
│
└── /module4 - Occupancy & Space Management
    ├── POST   /cameras
    ├── GET    /cameras
    ├── GET    /facility/live
    ├── GET    /alerts
    └── GET    /facility/stats
```

## Frontend Services

### 1. Module 1: Identity Service

**Location:** `frontend/src/app/services/identity.service.ts`

**Responsibilities:**
- Face detection and identification
- Employee enrollment with AWS Rekognition
- Access log management
- Face search and matching
- Employee directory and statistics

**Key Methods:**

```typescript
// Process real-time identity detection
processFrame(request: ProcessFrameRequest): Observable<ProcessFrameResponse>

// Enroll new employee
enrollEmployee(request: EnrollEmployeeRequest): Observable<EnrollEmployeeResponse>

// Employee management
listEmployees(): Observable<EmployeeInfo[]>
getEmployee(employeeId: number): Observable<EmployeeInfo>
updateEmployee(employeeId: number, updates: Partial<EmployeeInfo>): Observable<EmployeeInfo>

// Access logs
getAccessLogs(startDate?: string, endDate?: string): Observable<AccessLog[]>
getTodayAccessLogs(): Observable<AccessLog[]>

// Face recognition
searchFaces(faceImage: string, threshold?: number): Observable<SearchFacesResponse>

// Reports
getStatistics(startDate?: string, endDate?: string): Observable<any>
getEmployeeMonthlyReport(employeeId: number, month: string): Observable<any>
```

**Observable Streams:**

```typescript
identities$: Observable<IdentityResult[]>      // Current identities
employees$: Observable<EmployeeInfo[]>         // Employees list
accessLogs$: Observable<AccessLog[]>           // Access logs
health$: Observable<any>                        // Health status
```

### 2. Module 2: Vehicle Service

**Location:** `frontend/src/app/services/vehicle.service.ts`

**Responsibilities:**
- Vehicle detection and tracking (YOLO + ByteTrack)
- Automatic License Plate Recognition (ANPR)
- Vehicle authorization checking
- Gate access control
- Access log and alert management

**Key Methods:**

```typescript
// Real-time frame processing
processFrame(request: ProcessFrameRequest): Observable<VehicleDetection>

// Vehicle registration
registerVehicle(request: VehicleRegisterRequest): Observable<VehicleResponse>

// Vehicle management
listVehicles(category?: string, status?: string): Observable<VehicleResponse[]>
getVehicle(vehicleId: number): Observable<VehicleResponse>
updateVehicleStatus(vehicleId: number, status: string): Observable<VehicleResponse>

// Access logs
getAccessLogs(limit?: number): Observable<VehicleAccessLog[]>
getTodayAccessLogs(): Observable<VehicleAccessLog[]>
flagAccessLog(logId: number): Observable<VehicleAccessLog>

// Reports
getDailySummary(date: string): Observable<DailySummaryResponse>
getMonthlySummary(month: string): Observable<MonthlySummaryResponse>

// Alerts
getAlerts(limit?: number): Observable<GateAlert[]>

// Statistics
getStatistics(): Observable<StatisticsResponse>
```

**Observable Streams:**

```typescript
vehicleDetections$: Observable<VehicleDetection>     // Latest detections
vehicles$: Observable<VehicleResponse[]>             // Vehicles list
accessLogs$: Observable<VehicleAccessLog[]>          // Access logs
alerts$: Observable<GateAlert[]>                     // Gate alerts
health$: Observable<any>                              // Health status
```

### 3. Module 3: Attendance Service

**Location:** `frontend/src/app/services/attendance-module.service.ts`

**Responsibilities:**
- Attendance check-in/check-out
- Shift management
- Early exit detection (COMING - QA found as P0 issue)
- Double-entry prevention (COMING - QA found as P0 issue)
- Attendance reports and analytics

**Key Methods:**

```typescript
// Face detection integration
processFaceDetection(request: FaceDetectionRequest): Observable<CheckInResult>
processExitDetection(awsRekognitionId: string, cameraId: string, confidence: number): Observable<CheckOutResult>

// Manual override
createOverride(request: ManualOverrideRequest): Observable<AttendanceRecord>

// Records
getRecord(recordId: number): Observable<AttendanceRecord>
getTodayAttendance(): Observable<AttendanceRecord[]>
getAttendanceRecords(employeeId?: number, startDate?: string, endDate?: string): Observable<AttendanceRecord[]>

// Reports
getEmployeeMonthlyReport(employeeId: number, month: string): Observable<AttendanceReport>

// Summary
getSummary(): Observable<AttendanceSummary>

// Shifts
createShift(shift: Partial<ShiftResponse>): Observable<ShiftResponse>
listShifts(): Observable<ShiftResponse[]>

// Departments
createDepartment(dept: Partial<DepartmentResponse>): Observable<DepartmentResponse>
listDepartments(): Observable<DepartmentResponse[]>
```

**Observable Streams:**

```typescript
attendanceRecords$: Observable<AttendanceRecord[]>   // Records
summary$: Observable<AttendanceSummary>              // Daily summary
shifts$: Observable<ShiftResponse[]>                 // Shifts
departments$: Observable<DepartmentResponse[]>       // Departments
health$: Observable<any>                              // Health status
```

### 4. Module 4: Occupancy Service

**Location:** `frontend/src/app/services/occupancy.service.ts`

**Responsibilities:**
- Camera management and configuration
- Virtual line setup for people counting
- Real-time occupancy tracking
- Occupancy analytics and reporting
- Overcapacity alerts

**Key Methods:**

```typescript
// Cameras
createCamera(request: CameraCreateRequest): Observable<CameraResponse>
listCameras(): Observable<CameraResponse[]>
getCamera(cameraId: number): Observable<CameraResponse>
updateCamera(cameraId: number, updates: Partial<CameraResponse>): Observable<CameraResponse>
calibrateCamera(cameraId: number): Observable<any>

// Virtual lines
createVirtualLine(request: VirtualLineCreateRequest): Observable<VirtualLineResponse>
listVirtualLines(): Observable<VirtualLineResponse[]>
getCameraVirtualLines(cameraId: number): Observable<VirtualLineResponse[]>
updateVirtualLine(lineId: number, updates: Partial<VirtualLineResponse>): Observable<VirtualLineResponse>

// Live occupancy
getLiveCameraOccupancy(cameraId: number): Observable<OccupancyLiveResponse>
getLiveFacilityOccupancy(): Observable<FacilityOccupancyResponse>

// Analytics
getCameraHourlyOccupancy(cameraId: number, date: string): Observable<HourlyOccupancyResponse[]>
getCameraDailyOccupancy(cameraId: number, month: string): Observable<DailyOccupancyResponse[]>
getCameraMonthlyOccupancy(cameraId: number, year: string): Observable<MonthlyOccupancyResponse[]>

// Alerts
getAlerts(limit?: number): Observable<OccupancyAlertResponse[]>
resolveAlert(alertId: number): Observable<OccupancyAlertResponse>

// Statistics
getFacilityStats(): Observable<FacilityStatsResponse>
```

**Observable Streams:**

```typescript
cameras$: Observable<CameraResponse[]>                        // Cameras
virtualLines$: Observable<VirtualLineResponse[]>              // Virtual lines
facilityOccupancy$: Observable<FacilityOccupancyResponse>     // Facility occupancy
cameraOccupancy$: Observable<Map<number, OccupancyLiveResponse>>  // Per-camera occupancy
alerts$: Observable<OccupancyAlertResponse[]>                 // Occupancy alerts
stats$: Observable<FacilityStatsResponse>                     // Facility stats
health$: Observable<any>                                       // Health status
```

## Configuration

### API Configuration Service

**Location:** `frontend/src/app/services/api-config.service.ts`

Centralized API configuration providing:
- Endpoint URL management
- Query parameter building
- Backend connectivity validation

```typescript
// Get full URL for endpoint
this.apiConfig.getUrl(apiConfig.MODULE1_ENDPOINTS.enroll)
// => http://localhost:8000/api/module1/enroll

// Validate backend connection
await this.apiConfig.validateConnection()
// => { status: 'connected', modules: ['identity', 'vehicle', ...] }
```

### Environment Configuration

**Development:** `frontend/src/environments/environment.ts`
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

**Production:** `frontend/src/environments/environment.prod.ts`
```typescript
export const environment = {
  production: true,
  apiUrl: 'http://your-production-api.com/api'
};
```

## HTTP Error Handling

**Location:** `frontend/src/app/interceptors/http-error.interceptor.ts`

Global HTTP interceptor provides:
- Automatic retry for GET requests (once)
- Consistent error handling and logging
- Specific error responses for different HTTP codes (400, 401, 403, 404, 500, 503, etc.)
- User-friendly error messages

## Module Integration Points

### Module 1 → Module 3 Integration

**Identity Service (Module 1)** feeds into **Attendance Service (Module 3)**:

```typescript
// In Attendance Component
constructor(
  private identityService: IdentityService,
  private attendanceService: AttendanceService
) {}

onFaceDetected(faceDetectionRequest: FaceDetectionRequest) {
  // Module 1 processes face
  this.identityService.processFrame({
    frame: frameData,
    track_ids: [{ track_id: 1, face_crop: faceCropData }]
  }).subscribe(identityResponse => {
    
    // Identity result feeds into Module 3
    const checkInRequest = {
      aws_rekognition_id: identityResponse.identities[0].face_id,
      camera_id: 'cam1',
      confidence: identityResponse.identities[0].confidence,
      is_exit: false
    };
    
    this.attendanceService.processFaceDetection(checkInRequest).subscribe(
      result => console.log('Check-in:', result)
    );
  });
}
```

### Module 2 (Vehicle) Integration

**Vehicle Service** is independent but feeds alerts to dashboard:

```typescript
constructor(private vehicleService: VehicleService) {}

ngOnInit() {
  // Real-time vehicle detection
  this.vehicleService.vehicleDetections$.subscribe(detection => {
    this.updateVehicleStats(detection);
  });
  
  // Real-time alerts
  this.vehicleService.alerts$.subscribe(alerts => {
    this.showGateAlerts(alerts);
  });
}
```

### Module 4 (Occupancy) Integration

**Occupancy Service** provides real-time facility stats:

```typescript
constructor(private occupancyService: OccupancyService) {}

ngOnInit() {
  // Real-time facility occupancy
  this.occupancyService.facilityOccupancy$.subscribe(occupancy => {
    this.updateOccupancyDashboard(occupancy);
  });
  
  // Real-time alerts
  this.occupancyService.alerts$.subscribe(alerts => {
    this.showOccupancyAlerts(alerts);
  });
  
  // Periodic statistics update
  this.occupancyService.stats$.subscribe(stats => {
    this.updateFacilityStats(stats);
  });
}
```

## Running the System

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/factory_safety"
export FASTAPI_ENV="development"

# Run unified backend with all 4 modules
python main_unified.py
# or
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run just the app/main.py for Django setup
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server
ng serve
# Navigate to http://localhost:4200

# Production build
ng build --prod
```

## Testing Integration

### 1. Check Backend Health

```typescript
constructor(private apiConfig: ApiConfigService) {}

async checkBackendHealth() {
  try {
    const status = await this.apiConfig.validateConnection();
    console.log('Backend Status:', status);
  } catch (error) {
    console.error('Backend unreachable:', error);
  }
}
```

### 2. Test Each Module

```typescript
// Module 1: Identity
this.identityService.listEmployees().subscribe(employees => {
  console.log('Module 1 OK:', employees);
});

// Module 2: Vehicle
this.vehicleService.listVehicles().subscribe(vehicles => {
  console.log('Module 2 OK:', vehicles);
});

// Module 3: Attendance
this.attendanceService.getSummary().subscribe(summary => {
  console.log('Module 3 OK:', summary);
});

// Module 4: Occupancy
this.occupancyService.listCameras().subscribe(cameras => {
  console.log('Module 4 OK:', cameras);
});
```

### 3. Monitor Observable Streams

```typescript
// Subscribe to all streams for real-time updates
this.identityService.identities$.subscribe(identities => {
  console.log('New identities:', identities);
});

this.vehicleService.vehicleDetections$.subscribe(detection => {
  console.log('Vehicle detection:', detection);
});

this.attendanceService.attendanceRecords$.subscribe(records => {
  console.log('Attendance records:', records);
});

this.occupancyService.facilityOccupancy$.subscribe(occupancy => {
  console.log('Facility occupancy:', occupancy);
});
```

## Known Issues & Pending Fixes

### From QA Audit (CRITICAL)

**P0 Issues (Blocking):**
1. **RTSP Streaming** - Module 1, 2, 3, 4 need RTSP to browser streaming (3-4 days)
2. **Background Scheduler** - Module 3, 4 missing APScheduler for cleanup (2-3 hrs)
3. **Early Exit Logic** - Module 3 missing early exit detection (2-3 hrs)
4. **Double-Entry Prevention** - Module 3 missing duplicate check (2-3 hrs)

**Integration Status:**
- ✅ All backend endpoints defined and documented
- ✅ All frontend services created with proper TypeScript types
- ✅ Observable streams configured for real-time updates
- ✅ HTTP error interceptor configured
- ✅ API configuration service created
- ⏳ Module components need integration updates (in progress)

## Performance Considerations

### Caching
- Module 1: Identity results cached to avoid redundant AWS calls
- Module 3: Shift/department data cached with 1-hour TTL

### Real-Time Updates
- Module 4: Facility occupancy updates every 5 seconds
- Module 4: Stats updates every 30 seconds
- Module 1, 2, 3: Updates triggered by detection events

### Connection Management
- All services include health checks every 30 seconds
- Automatic retry for failed GET requests
- Graceful degradation on backend unavailability

## Troubleshooting

### "Cannot connect to backend"

1. Check backend is running:
```bash
curl http://localhost:8000/api/module1/health
```

2. Verify CORS configuration in `main_unified.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Check frontend environment configuration:
```typescript
export const environment = {
  apiUrl: 'http://localhost:8000/api'  // Must match backend
};
```

### "API endpoint not found" (404)

- Verify endpoint path matches backend router configuration
- Check Module 1, 2, 3, 4 endpoints in their respective `*_endpoints.py` files
- Use `ApiConfigService` to build URLs correctly

### "CORS error"

1. Backend CORS origin must match frontend URL
2. For localhost development, add `http://localhost:4200` to allowed origins
3. Check `Access-Control-Allow-Origin` header in response

## Next Steps

1. **Create Module Components** - Wire services to UI components
2. **Add WebSocket Support** - Real-time updates via Socket.io
3. **Implement RTSP Streaming** - Camera feed display
4. **Add Business Logic** - Early exit, double-entry checks
5. **Deploy to Production** - Configure environment, SSL, etc.

---

**Last Updated:** 2024
**Status:** Integration Complete - Ready for Component Development
