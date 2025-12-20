# Quick Start: Backend-Frontend Integration

## What Just Happened?

You now have complete backend-frontend integration for all 4 modules:

✅ **Module 1 (Identity)** - `identity.service.ts`
✅ **Module 2 (Vehicle)** - `vehicle.service.ts`
✅ **Module 3 (Attendance)** - `attendance-module.service.ts`
✅ **Module 4 (Occupancy)** - `occupancy.service.ts`
✅ **API Config** - `api-config.service.ts`
✅ **HTTP Interceptor** - `http-error.interceptor.ts`
✅ **App Module** - Updated with all services

## Running the System

### 1. Start Backend

```bash
cd backend

# Install requirements
pip install -r requirements.txt

# Run FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run unified backend
python main_unified.py
```

Backend will be available at: `http://localhost:8000/api`

### 2. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
ng serve
```

Frontend will be available at: `http://localhost:4200`

### 3. Verify Integration

Open your browser console and test:

```typescript
// In browser console

// Test Module 1 (Identity)
fetch('http://localhost:8000/api/module1/health')
  .then(r => r.json())
  .then(d => console.log('Module 1 ✅', d))
  .catch(e => console.error('Module 1 ❌', e));

// Test Module 2 (Vehicle)
fetch('http://localhost:8000/api/module2/health')
  .then(r => r.json())
  .then(d => console.log('Module 2 ✅', d))
  .catch(e => console.error('Module 2 ❌', e));

// Test Module 3 (Attendance)
fetch('http://localhost:8000/api/module3/health')
  .then(r => r.json())
  .then(d => console.log('Module 3 ✅', d))
  .catch(e => console.error('Module 3 ❌', e));

// Test Module 4 (Occupancy)
fetch('http://localhost:8000/api/module4/health')
  .then(r => r.json())
  .then(d => console.log('Module 4 ✅', d))
  .catch(e => console.error('Module 4 ❌', e));
```

## Using the Services

### Example: Identity Service

```typescript
import { IdentityService } from './services/identity.service';

@Component({...})
export class MyComponent {
  constructor(private identityService: IdentityService) {}

  ngOnInit() {
    // Load all employees
    this.identityService.listEmployees().subscribe(
      employees => console.log('Employees:', employees),
      error => console.error('Error:', error)
    );

    // Subscribe to real-time identity updates
    this.identityService.identities$.subscribe(
      identities => console.log('New identities:', identities)
    );
  }

  enrollEmployee(name: string, department: string, photo: File) {
    this.identityService.enrollEmployee({
      name,
      department,
      photo
    }).subscribe(
      result => console.log('Enrollment success:', result),
      error => console.error('Enrollment failed:', error)
    );
  }
}
```

### Example: Vehicle Service

```typescript
import { VehicleService } from './services/vehicle.service';

@Component({...})
export class VehicleComponent {
  constructor(private vehicleService: VehicleService) {}

  ngOnInit() {
    // Load vehicles
    this.vehicleService.listVehicles().subscribe(
      vehicles => this.vehicles = vehicles
    );

    // Real-time detections
    this.vehicleService.vehicleDetections$.subscribe(
      detection => this.updateDetection(detection)
    );

    // Real-time alerts
    this.vehicleService.alerts$.subscribe(
      alerts => this.showAlerts(alerts)
    );
  }
}
```

### Example: Attendance Service

```typescript
import { AttendanceService } from './services/attendance-module.service';

@Component({...})
export class AttendanceComponent {
  constructor(private attendanceService: AttendanceService) {}

  ngOnInit() {
    // Get today's summary
    this.attendanceService.getSummary().subscribe(
      summary => this.summary = summary
    );

    // Get today's records
    this.attendanceService.getTodayAttendance().subscribe(
      records => this.records = records
    );
  }

  processCheckIn(awsRekognitionId: string) {
    this.attendanceService.processFaceDetection({
      aws_rekognition_id: awsRekognitionId,
      camera_id: 'camera-1',
      confidence: 0.95,
      is_exit: false
    }).subscribe(
      result => console.log('Check-in:', result)
    );
  }
}
```

### Example: Occupancy Service

```typescript
import { OccupancyService } from './services/occupancy.service';

@Component({...})
export class OccupancyComponent {
  constructor(private occupancyService: OccupancyService) {}

  ngOnInit() {
    // Real-time facility occupancy
    this.occupancyService.facilityOccupancy$.subscribe(
      occupancy => this.facilityOccupancy = occupancy
    );

    // Real-time alerts
    this.occupancyService.alerts$.subscribe(
      alerts => this.alerts = alerts
    );

    // Statistics
    this.occupancyService.stats$.subscribe(
      stats => this.stats = stats
    );
  }

  createCamera(name: string, location: string, rtspUrl: string) {
    this.occupancyService.createCamera({
      name,
      location,
      rtsp_url: rtspUrl,
      view_area_sqm: 100,
      capacity: 50
    }).subscribe(
      camera => console.log('Camera created:', camera)
    );
  }
}
```

## Service Features

### Observable Streams (Real-Time Updates)

All services provide observable streams for real-time data:

```typescript
// Module 1: Identity
identityService.identities$              // Current identified persons
identityService.employees$               // Employees list
identityService.accessLogs$              // Access logs

// Module 2: Vehicle
vehicleService.vehicleDetections$        // Vehicle detections
vehicleService.vehicles$                 // Registered vehicles
vehicleService.accessLogs$               // Access logs
vehicleService.alerts$                   // Gate alerts

// Module 3: Attendance
attendanceService.attendanceRecords$     // Attendance records
attendanceService.summary$               // Daily summary
attendanceService.shifts$                // Shifts
attendanceService.departments$           // Departments

// Module 4: Occupancy
occupancyService.facilityOccupancy$      // Real-time occupancy
occupancyService.cameras$                // Cameras
occupancyService.alerts$                 // Occupancy alerts
occupancyService.stats$                  // Facility statistics
```

### Health Checks

All services automatically check backend health every 30 seconds:

```typescript
// Manual health check
identityService.healthCheck().subscribe(
  health => console.log('Module 1 healthy:', health)
);

// Subscribe to health status
identityService.health$.subscribe(
  status => console.log('Module 1 status:', status)
);
```

## Configuration

### Change API URL

Update `environment.ts` to point to your backend:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://your-api-server:8000/api'  // Change this
};
```

### API Configuration Service

Use `ApiConfigService` to access all endpoint URLs:

```typescript
constructor(private apiConfig: ApiConfigService) {}

ngOnInit() {
  // Get endpoint URL
  const enrollUrl = this.apiConfig.getUrl(
    this.apiConfig.MODULE1_ENDPOINTS.enroll
  );
  console.log('Enroll endpoint:', enrollUrl);

  // Validate backend connection
  this.apiConfig.validateConnection().then(
    status => console.log('Backend connected:', status)
  ).catch(
    error => console.error('Backend unreachable:', error)
  );
}
```

## Error Handling

All services have built-in error handling:

```typescript
// Automatic retry for GET requests
// Error interceptor catches and logs all HTTP errors
// Graceful error messages for users

this.identityService.processFrame(request).subscribe(
  success => console.log('Success:', success),
  error => console.error('Error:', error.message)
);
```

## Browser DevTools

### Network Tab
Monitor HTTP requests to backend in Network tab:
- `http://localhost:8000/api/module1/*`
- `http://localhost:8000/api/module2/*`
- `http://localhost:8000/api/module3/*`
- `http://localhost:8000/api/module4/*`

### Console
View service logs and errors:
```
Module 1 Health check failed: Error: ...
Vehicle Module Health check failed: Error: ...
HTTP Error: Error Code: 404
```

## Troubleshooting

### "Cannot GET /api/module1/..."

**Problem:** Backend not running
**Solution:** Start backend with `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### "CORS error: Access-Control-Allow-Origin"

**Problem:** Backend CORS not configured for frontend URL
**Solution:** Update backend CORS in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "404 Not Found"

**Problem:** Endpoint doesn't exist
**Solution:** Verify endpoint path:
- Check `backend/detection_system/*_endpoints.py` files
- Use `ApiConfigService` to get correct paths
- Ensure backend is running the unified server

### Service shows undefined

**Problem:** Service not injected
**Solution:** 
1. Import service in component
2. Add to constructor parameter
3. Verify service is in `app.module.ts` providers

## Next Steps

1. **Create UI Components** - Wire services to components
2. **Add Forms** - For enrollment, registration, overrides
3. **Display Data** - Use *ngIf, *ngFor to show results
4. **Real-Time Updates** - Subscribe to observable streams
5. **Charts/Graphs** - Display analytics (ng2-charts, etc.)
6. **Animations** - Add loading spinners, transitions
7. **Notifications** - Toast, alerts for events

## File Structure

```
frontend/src/app/
├── services/
│   ├── identity.service.ts              ← Module 1
│   ├── vehicle.service.ts               ← Module 2
│   ├── attendance-module.service.ts     ← Module 3
│   ├── occupancy.service.ts             ← Module 4
│   └── api-config.service.ts            ← API Config
├── interceptors/
│   └── http-error.interceptor.ts        ← Error Handling
├── components/
│   └── modules/
│       ├── module-identity/             ← Module 1 components
│       ├── module-vehicle/              ← Module 2 components
│       ├── module-attendance/           ← Module 3 components
│       └── module-occupancy/            ← Module 4 components
└── app.module.ts                        ← Updated with all services
```

## Documentation

- **Integration Guide:** `INTEGRATION_GUIDE.md`
- **Backend API:** `backend/FASTAPI_BACKEND.md`
- **QA Report:** `QA_REVIEW_REPORT.md`
- **Quick Start:** `QUICK_START_INTEGRATION.md` (this file)

---

**Status:** ✅ Integration Complete
**Ready for:** Component Development & Testing
