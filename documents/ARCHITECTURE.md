# 🏗️ System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FACTORY SAFETY DETECTOR                       │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────────┐
                        │   Camera /   │
                        │ Video Source │
                        └──────┬───────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │           ML Models (Python)                  │
        ├──────────────────────────────────────────────┤
        │  • YOLO (best_helmet.pt)                     │
        │  • YOLO (best_product.pt)                    │
        │  • DeepFace (Face Recognition)               │
        └──────────────┬───────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────┐
        │         FastAPI Backend (Port 8000)          │
        ├──────────────────────────────────────────────┤
        │  Services:                                    │
        │  • helmet_service.py                          │
        │  • loitering_service.py                       │
        │  • production_counter_service.py              │
        │  • attendance_service.py                      │
        │                                               │
        │  Endpoints:                                   │
        │  • GET /api/status/helmet                     │
        │  • GET /api/status/loitering                  │
        │  • GET /api/status/counting                   │
        │  • GET /api/status/attendance                 │
        └──────────────┬───────────────────────────────┘
                       │
                       │ HTTP/JSON + CORS
                       │
                       ▼
        ┌──────────────────────────────────────────────┐
        │      Angular Frontend (Port 4200)            │
        ├──────────────────────────────────────────────┤
        │  Services:                                    │
        │  • helmet.service.ts                          │
        │  • loitering.service.ts                       │
        │  • production.service.ts                      │
        │  • attendance.service.ts                      │
        │                                               │
        │  Components:                                  │
        │  • Dashboard Component                        │
        │  • Helmet Detection Component                │
        └──────────────┬───────────────────────────────┘
                       │
                       ▼
                ┌─────────────┐
                │   Browser   │
                │   (Chrome)  │
                └─────────────┘
```

## Data Flow Details

### 1. Video Capture Layer
```
Camera → OpenCV → Frame Buffer
         (cv2.VideoCapture)
```

### 2. ML Processing Layer
```
Frame → YOLO Detection → Bounding Boxes → Tracking
                      ↓
                   Classes (helmet, head, box, etc.)
                      ↓
                   Confidence Scores

Frame → DeepFace → Face Embeddings → Database Match
                ↓
             Identity Recognition
```

### 3. Service Layer
```
helmet_service.py:
  Frame → YOLO → Count people, helmets, violations
              → Return: {totalPeople, compliantCount, violationCount}

loitering_service.py:
  Frame → YOLO + Tracking → Distance calculation
                          → Timer management
                          → Return: {activeGroups}

production_counter_service.py:
  Frame → YOLO + Tracking → Line crossing detection
                          → Increment counter
                          → Return: {itemCount}

attendance_service.py:
  Frame → DeepFace → Face recognition
                  → Database lookup
                  → Log attendance
                  → Return: {verifiedCount, lastPersonSeen, attendanceLog}
```

### 4. API Layer
```
FastAPI Routes:
  /api/status/helmet     → helmet_service.get_helmet_detection_status()
  /api/status/loitering  → loitering_service.get_loitering_status()
  /api/status/counting   → production_counter_service.get_production_count()
  /api/status/attendance → attendance_service.get_attendance_status()

CORS Middleware:
  allow_origins=["*"]    → Allow all origins (dev mode)
  allow_methods=["*"]    → Allow all HTTP methods
  allow_headers=["*"]    → Allow all headers
```

### 5. HTTP Communication
```
Angular HttpClient:
  GET http://localhost:8000/api/status/helmet
  ↓
  JSON Response: {"totalPeople": 5, "compliantCount": 4, "violationCount": 1}
  ↓
  RxJS Observable → Component
```

### 6. Frontend Services
```
helmet.service.ts:
  getHelmetStatusStream(2000)
    ↓
  interval(2000) → switchMap → http.get()
    ↓
  Observable<HelmetStatus>
    ↓
  Component subscribes
```

### 7. Component Layer
```
dashboard.component.ts:
  ngOnInit() {
    this.helmetService.getHelmetStatusStream(2000)
      .subscribe(data => this.helmetData = data);
  }
  ↓
  Template updates automatically (Angular Change Detection)
```

### 8. UI Layer
```
dashboard.component.html:
  {{ helmetData.totalPeople }}    → Displays number
  {{ helmetData.violationCount }} → Displays violations
  [class.danger]                  → Conditional styling
  *ngFor                          → Loop attendance logs
```

## Component Communication

### Backend Internal Communication
```
main.py
  ↓ imports
helmet_service.py
  ↓ uses
YOLO model (best_helmet.pt)
  ↓ processes
Camera frame
  ↓ returns
Detection data
```

### Frontend Internal Communication
```
app.component
  ↓ router-outlet
dashboard.component
  ↓ constructor injection
helmet.service
  ↓ HttpClient
FastAPI backend
```

## State Management

### Backend State (In-Memory)
```
helmet_service:
  • model (YOLO) - loaded once
  • cap (VideoCapture) - loaded once

loitering_service:
  • model (YOLO) - loaded once
  • cap (VideoCapture) - loaded once
  • person_loitering_timer {} - persists between calls
  • active_loitering_groups {} - persists between calls

production_counter_service:
  • model (YOLO) - loaded once
  • cap (VideoCapture) - loaded once
  • line_counter - persists between calls

attendance_service:
  • DeepFace models - loaded once (warm-up)
  • cap (VideoCapture) - loaded once
  • logged_today {} - persists between calls
  • attendance_log [] - persists between calls
  • last_person_seen - persists between calls
```

### Frontend State (Component)
```
dashboard.component:
  • helmetData: HelmetStatus
  • loiteringData: LoiteringStatus
  • productionData: ProductionCount
  • attendanceData: AttendanceStatus
  • subscriptions: Subscription[]

Updated automatically via:
  Observable subscriptions → Change detection → UI update
```

## Timing & Intervals

```
Frontend Polling:
  Helmet:     every 2000ms (2 seconds)
  Loitering:  every 2000ms (2 seconds)
  Production: every 2000ms (2 seconds)
  Attendance: every 5000ms (5 seconds)

Backend Processing:
  Helmet:     ~instant (one frame)
  Loitering:  ~instant (one frame + state)
  Production: ~instant (one frame + state)
  Attendance: expensive (DeepFace) - cached for RECOGNITION_INTERVAL

Total Update Cycle:
  Frontend poll → Network request → Backend process → Response → UI update
  Typical: 100-500ms per cycle
```

## Resource Usage

```
Backend (Python):
  CPU: High (video processing + ML inference)
  RAM: ~2-4GB (models loaded in memory)
  GPU: Optional (speeds up YOLO inference 10-50x)
  Disk: Read models once, minimal I/O
  Network: Minimal (only API responses)

Frontend (Angular):
  CPU: Low (just UI rendering)
  RAM: ~200-500MB (browser)
  Network: Low (small JSON responses every 2-5s)
  Disk: None after load
```

## Technology Stack Layers

```
┌────────────────────────────────────────┐
│         Presentation Layer             │
│  • Angular 17                          │
│  • TypeScript                          │
│  • HTML/CSS                            │
│  • RxJS                                │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│         Communication Layer            │
│  • HTTP/REST                           │
│  • JSON                                │
│  • CORS                                │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│         Application Layer              │
│  • FastAPI                             │
│  • Python Services                     │
│  • Uvicorn (ASGI Server)               │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│         ML/AI Layer                    │
│  • Ultralytics YOLO                    │
│  • DeepFace                            │
│  • OpenCV                              │
│  • Supervision                         │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│         Hardware Layer                 │
│  • CPU/GPU                             │
│  • RAM                                 │
│  • Webcam                              │
│  • Storage                             │
└────────────────────────────────────────┘
```

## Security Layers

```
Browser (Frontend):
  ✓ Same-origin policy
  ✓ Content Security Policy (CSP)
  ✗ No authentication (dev mode)

Network:
  ✗ HTTP (not HTTPS)
  ✓ CORS enabled
  ✗ No rate limiting

Backend:
  ✓ CORS middleware
  ✗ No authentication
  ✗ No input validation
  ✗ No request logging

Data:
  ✗ Employee photos unencrypted
  ✗ No access control

For Production:
  → Add HTTPS/TLS
  → Add JWT authentication
  → Add rate limiting
  → Add input validation
  → Encrypt sensitive data
  → Add audit logging
```

## Scalability Considerations

```
Current Setup (Single Machine):
  • 1 Camera
  • 1 Backend process
  • 1 Frontend instance
  • Supports: ~5-10 concurrent users

To Scale Horizontally:
  • Multiple cameras → Multiple backend instances
  • Load balancer → Distribute requests
  • Shared state → Redis/Database
  • Message queue → Process frames async
  • CDN → Serve frontend static files

To Scale Vertically:
  • Better GPU → Faster inference
  • More RAM → Load more models
  • Faster CPU → Process more frames
  • Better camera → Higher resolution
```

## Deployment Architecture

```
Development (Current):
  localhost:8000 ← Backend
  localhost:4200 ← Frontend

Production Option 1 (Cloud):
  https://api.company.com    ← Backend (Cloud VM)
  https://dashboard.company.com ← Frontend (CDN)

Production Option 2 (On-Premise):
  http://192.168.1.100:8000 ← Backend (Local Server)
  http://192.168.1.100:80   ← Frontend (Nginx)

Production Option 3 (Containerized):
  Docker Container 1 → Backend
  Docker Container 2 → Frontend
  Docker Compose → Orchestration
```

## File Relationships

```
app/main.py
  ├─ imports: app.services.helmet_service
  ├─ imports: app.services.loitering_service
  ├─ imports: app.services.production_counter_service
  └─ imports: app.services.attendance_service

frontend/src/app/app.module.ts
  ├─ declares: AppComponent
  ├─ declares: DashboardComponent
  ├─ declares: HelmetDetectionComponent
  ├─ imports: HttpClientModule
  └─ imports: AppRoutingModule

frontend/src/app/app-routing.module.ts
  ├─ route: '' → DashboardComponent
  └─ route: '/helmet-detection' → HelmetDetectionComponent

frontend/src/environments/environment.ts
  └─ used by: All service files
```

---

This architecture provides:
✅ Real-time monitoring
✅ Scalable design
✅ Modular components
✅ Easy to maintain
✅ Easy to extend
