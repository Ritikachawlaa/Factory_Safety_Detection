# Integration Testing Checklist

## Pre-Integration Tests

### Backend Startup ✅

- [ ] Backend server starts without errors
  ```bash
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- [ ] FastAPI docs available at `http://localhost:8000/docs`
- [ ] Database migrations applied
- [ ] All models loaded successfully

### Frontend Startup ✅

- [ ] Frontend dev server starts
  ```bash
  ng serve
  ```
- [ ] No TypeScript compilation errors
- [ ] Angular app loads at `http://localhost:4200`
- [ ] No console errors

## Module 1: Identity & Access Intelligence

### Service Initialization

- [ ] `IdentityService` loads successfully
- [ ] Constructor initializes health check interval
- [ ] Observable streams created:
  - [ ] `identities$`
  - [ ] `employees$`
  - [ ] `accessLogs$`
  - [ ] `health$`

### API Connectivity

- [ ] Health check endpoint responds
  ```
  GET http://localhost:8000/api/module1/health
  ```
- [ ] Service recognizes health response
- [ ] Health status updates in observable

### Employee Operations

- [ ] List employees works
  ```typescript
  identityService.listEmployees().subscribe(...)
  ```
- [ ] Employees observable updates
- [ ] Get specific employee works
- [ ] Employee update works (if implemented)

### Identity Detection

- [ ] Process frame endpoint accessible
- [ ] Frame processing returns results
- [ ] Identities observable updates with results
- [ ] Caching works (redundant calls faster)

### Access Logs

- [ ] Get today's access logs works
- [ ] Access logs observable updates
- [ ] Date filtering works
- [ ] Employee filtering works

### Reports

- [ ] Statistics endpoint works
- [ ] Monthly report endpoint works
- [ ] Data formatting correct

## Module 2: Vehicle & Gate Management

### Service Initialization

- [ ] `VehicleService` loads successfully
- [ ] Constructor initializes health check
- [ ] Observable streams created:
  - [ ] `vehicleDetections$`
  - [ ] `vehicles$`
  - [ ] `accessLogs$`
  - [ ] `alerts$`
  - [ ] `health$`

### API Connectivity

- [ ] Health check endpoint responds
  ```
  GET http://localhost:8000/api/module2/health
  ```
- [ ] Service recognizes response
- [ ] Health status updates

### Vehicle Registration

- [ ] Register vehicle works
  ```typescript
  vehicleService.registerVehicle(request).subscribe(...)
  ```
- [ ] Vehicle appears in list
- [ ] Vehicles observable updates

### Vehicle Operations

- [ ] List vehicles works
- [ ] Filter by category works
- [ ] Filter by status works
- [ ] Get specific vehicle works
- [ ] Update vehicle status works
- [ ] Delete vehicle works

### Frame Processing

- [ ] Process frame endpoint accessible
- [ ] Returns detection results
- [ ] Vehicle detection count increases
- [ ] Plates recognized count updates
- [ ] Detections observable updates

### Access Logs

- [ ] Get access logs works
- [ ] Today's logs works
- [ ] Flag log for review works
- [ ] Logs observable updates

### Alerts

- [ ] Get alerts works
- [ ] Alerts observable updates with new alerts
- [ ] Alert types correct (UNKNOWN, BLOCKED, SUSPICIOUS, etc.)

### Reports

- [ ] Daily summary works
- [ ] Monthly summary works
- [ ] Statistics endpoint works

## Module 3: Attendance Tracking

### Service Initialization

- [ ] `AttendanceService` loads successfully
- [ ] Initial data loads (today's attendance, summary, shifts, departments)
- [ ] Observable streams created:
  - [ ] `attendanceRecords$`
  - [ ] `summary$`
  - [ ] `shifts$`
  - [ ] `departments$`
  - [ ] `health$`

### API Connectivity

- [ ] Health check endpoint responds
  ```
  GET http://localhost:8000/api/module3/health
  ```
- [ ] Service recognizes response
- [ ] Health status updates

### Face Detection Integration

- [ ] Process face detection works
- [ ] Check-in result returns employee info
- [ ] Check-in observable updates
- [ ] Check-out works
- [ ] Duration calculated correctly

### Manual Override

- [ ] Create override works
- [ ] Override appears in records
- [ ] Reason stored correctly

### Records

- [ ] Get today's attendance works
- [ ] Records observable updates
- [ ] Get specific record works
- [ ] Get employee records works
- [ ] Date filtering works

### Shifts

- [ ] Create shift works
- [ ] List shifts works
- [ ] Shift data available
- [ ] Shifts observable updates

### Departments

- [ ] Create department works
- [ ] List departments works
- [ ] Department data available
- [ ] Departments observable updates

### Summary

- [ ] Get summary works
- [ ] Contains today's stats:
  - [ ] Present count
  - [ ] Absent count
  - [ ] Late count
  - [ ] Total employees
  - [ ] Attendance percentage

### Reports

- [ ] Get monthly report works
- [ ] Report contains:
  - [ ] Present days
  - [ ] Absent days
  - [ ] Late count
  - [ ] Attendance percentage

## Module 4: Occupancy & Space Management

### Service Initialization

- [ ] `OccupancyService` loads successfully
- [ ] Initial data loads (cameras, virtual lines, facility occupancy)
- [ ] Real-time updates start (5s interval)
- [ ] Observable streams created:
  - [ ] `cameras$`
  - [ ] `virtualLines$`
  - [ ] `facilityOccupancy$`
  - [ ] `cameraOccupancy$`
  - [ ] `alerts$`
  - [ ] `stats$`
  - [ ] `health$`

### API Connectivity

- [ ] Health check endpoint responds
  ```
  GET http://localhost:8000/api/module4/health
  ```
- [ ] Service recognizes response
- [ ] Health status updates

### Camera Management

- [ ] Create camera works
- [ ] Camera appears in list
- [ ] List cameras works
- [ ] Get specific camera works
- [ ] Update camera works
- [ ] Cameras observable updates

### Virtual Lines

- [ ] Create virtual line works
- [ ] Line appears in camera's lines
- [ ] Get camera lines works
- [ ] List all lines works
- [ ] Update line works
- [ ] Virtual lines observable updates

### Live Occupancy

- [ ] Get live camera occupancy works
- [ ] Returns current occupancy count
- [ ] Returns capacity
- [ ] Returns occupancy percentage
- [ ] Returns density level
- [ ] Camera occupancy map updates

### Facility Occupancy

- [ ] Get live facility occupancy works
- [ ] Returns total occupancy
- [ ] Returns total capacity
- [ ] Per-camera breakdown correct
- [ ] Facility occupancy observable updates
- [ ] Real-time updates every 5 seconds

### Analytics

- [ ] Get hourly occupancy works
- [ ] Get daily occupancy works
- [ ] Get monthly occupancy works
- [ ] Data properly aggregated

### Alerts

- [ ] Get alerts works
- [ ] Alerts observable updates
- [ ] Alert types correct (OVERCAPACITY, DENSITY_HIGH, etc.)
- [ ] Resolve alert works
- [ ] Alert status updates

### Statistics

- [ ] Get facility stats works
- [ ] Stats include:
  - [ ] Total cameras
  - [ ] Total capacity
  - [ ] Current occupancy
  - [ ] Areas by density
  - [ ] Peak occupancy
  - [ ] Entry/exit counts
- [ ] Stats observable updates
- [ ] Updates every 30 seconds

### Calibration

- [ ] Calibrate camera works
- [ ] Calibration initiates setup

## HTTP Interceptor Tests

- [ ] GET requests retry once on failure
- [ ] POST/PUT/DELETE don't retry
- [ ] Error messages displayed in console
- [ ] Network errors handled gracefully
- [ ] 404 errors handled
- [ ] 500 errors handled
- [ ] CORS errors handled
- [ ] 401/403 errors handled

## API Configuration Tests

- [ ] `ApiConfigService` initializes
- [ ] `getUrl()` returns correct full URLs
- [ ] All endpoint constants available
- [ ] Query parameters built correctly
- [ ] Backend validation works
  ```typescript
  await apiConfig.validateConnection()
  ```

## Observable Stream Tests

### Module 1

- [ ] Subscribe to `identities$` receives updates
- [ ] Subscribe to `employees$` receives list
- [ ] Subscribe to `accessLogs$` receives logs
- [ ] Multiple subscribers work independently

### Module 2

- [ ] Subscribe to `vehicleDetections$` receives frames
- [ ] Subscribe to `vehicles$` receives list
- [ ] Subscribe to `alerts$` receives new alerts
- [ ] Multiple concurrent operations work

### Module 3

- [ ] Subscribe to `attendanceRecords$` receives updates
- [ ] Subscribe to `summary$` receives daily summary
- [ ] Subscribe to `shifts$` receives shifts
- [ ] Subscribing updates on new data

### Module 4

- [ ] Subscribe to `facilityOccupancy$` updates every 5s
- [ ] Subscribe to `stats$` updates every 30s
- [ ] Subscribe to `alerts$` receives updates
- [ ] Real-time updates continuous

## Integration Tests

### Module 1 → Module 3

- [ ] Identity service results feed to attendance
- [ ] Face ID from Module 1 used in Module 3
- [ ] Check-in creates attendance record
- [ ] Check-out updates attendance record

### Module 4 Real-Time

- [ ] Facility occupancy updates automatically
- [ ] Stats update automatically
- [ ] Alerts trigger in real-time
- [ ] No memory leaks from interval subscriptions

### Error Scenarios

- [ ] Backend offline: graceful error message
- [ ] Invalid endpoint: 404 handled
- [ ] Invalid data: 400 handled
- [ ] Server error: 500 handled
- [ ] Network timeout: retry and error
- [ ] CORS issue: error logged

## Performance Tests

### API Response Times

- [ ] Module 1 process-frame: < 500ms
- [ ] Module 2 process-frame: < 500ms
- [ ] Module 3 process-face-detection: < 500ms
- [ ] Module 4 live occupancy: < 200ms

### Observable Subscription Performance

- [ ] Multiple subscribers don't cause issues
- [ ] Memory usage stable over time
- [ ] No memory leaks from intervals
- [ ] Unsubscribe cleanup works

### Network Optimization

- [ ] Health checks don't overwhelm server
- [ ] Real-time updates efficient
- [ ] Error retries limited

## Browser DevTools Tests

### Network Tab

- [ ] All API calls visible
- [ ] Status codes correct (200, 201, 400, 404, 500)
- [ ] Response bodies valid JSON
- [ ] Request headers include Content-Type
- [ ] No failed requests (unless intentional tests)

### Console

- [ ] No TypeScript errors
- [ ] Services log properly
- [ ] Health checks logged
- [ ] Errors logged with context
- [ ] No infinite loop warnings

### Storage

- [ ] LocalStorage/SessionStorage if used
- [ ] Cache management working (if implemented)

## Smoke Tests

Run these after each module integration:

```bash
# Test all module health endpoints
curl http://localhost:8000/api/module1/health && echo "Module 1 OK"
curl http://localhost:8000/api/module2/health && echo "Module 2 OK"
curl http://localhost:8000/api/module3/health && echo "Module 3 OK"
curl http://localhost:8000/api/module4/health && echo "Module 4 OK"

# Test frontend loads
curl http://localhost:4200/ | grep -q "Module" && echo "Frontend OK"
```

## Final Checklist

- [ ] All backend endpoints responding
- [ ] All frontend services connected
- [ ] All observable streams working
- [ ] Real-time updates functioning
- [ ] Error handling robust
- [ ] Health checks passing
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Performance acceptable
- [ ] Integration documentation complete

## Testing Report Template

```markdown
# Integration Testing Report - [Date]

## Summary
- Modules Tested: [1, 2, 3, 4]
- Tests Passed: [X/Y]
- Tests Failed: [X]
- Critical Issues: [X]
- Status: [READY/BLOCKED]

## Module 1: Identity
- Status: ✅ PASS / ❌ FAIL
- Issues: [List any issues]

## Module 2: Vehicle
- Status: ✅ PASS / ❌ FAIL
- Issues: [List any issues]

## Module 3: Attendance
- Status: ✅ PASS / ❌ FAIL
- Issues: [List any issues]

## Module 4: Occupancy
- Status: ✅ PASS / ❌ FAIL
- Issues: [List any issues]

## Next Steps
- [Blockers to resolve]
- [Nice-to-haves]
```

---

**Test Status:** Ready for Integration Testing
**Last Updated:** 2024
