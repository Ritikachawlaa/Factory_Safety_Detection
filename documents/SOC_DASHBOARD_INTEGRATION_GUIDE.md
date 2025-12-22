

# SOC Dashboard Component Integration Guide

## Overview

This document provides complete instructions for integrating the professional Security Operations Center (SOC) dashboard components into your Angular application. The dashboard includes real-time video feeds, activity monitoring, metric tracking, and critical alert management.

---

## Table of Contents

1. [Component Architecture](#component-architecture)
2. [File Structure](#file-structure)
3. [Module Setup](#module-setup)
4. [Component Integration](#component-integration)
5. [Service Configuration](#service-configuration)
6. [Styling & Theming](#styling--theming)
7. [Real-Time Data Flow](#real-time-data-flow)
8. [Usage Examples](#usage-examples)
9. [Testing Checklist](#testing-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Component Architecture

```
SocDashboardComponent (Main Container)
├── Header
│   ├── Logo & Title
│   ├── System Status
│   ├── Time Display
│   └── User Info
├── Sidebar (Collapsible)
│   ├── Module Navigation (4 buttons)
│   └── Export Controls
├── Main Content Area
│   ├── MetricsBarComponent
│   │   └── MetricScorecardComponent (×4)
│   ├── VideoFeedTileComponent (×3 or ×4 in grid)
│   ├── VideoFeedDetailComponent (single camera detail)
│   ├── ActivityFeedComponent
│   └── Manual Override Modal
└── ToastContainerComponent
    └── ToastNotificationComponent (×n)
```

---

## File Structure

Created files for the SOC Dashboard:

```
frontend/src/app/components/soc-dashboard/
├── soc-dashboard.component.ts          # Main dashboard logic (800 lines)
├── soc-dashboard.component.html        # Main dashboard template (450 lines)
├── soc-dashboard.component.scss        # Dashboard styles & animations
├── video-feed.component.ts             # Video tile & detail components
├── activity-feed.component.ts          # Activity feed component
├── metric-scorecard.component.ts       # Metric cards & metrics bar
├── toast-notification.service.ts       # Toast notification system
└── soc-dashboard.module.ts             # Component module (to create)
```

**Existing Services (Already Created):**
- `app/services/identity.service.ts`
- `app/services/vehicle.service.ts`
- `app/services/attendance-module.service.ts`
- `app/services/occupancy.service.ts`
- `app/services/http-error.interceptor.ts`

---

## Module Setup

### 1. Create SOC Dashboard Module

Create `frontend/src/app/components/soc-dashboard/soc-dashboard.module.ts`:

```typescript
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

// Components
import { SocDashboardComponent } from './soc-dashboard.component';
import { VideoFeedTileComponent, VideoFeedDetailComponent } from './video-feed.component';
import { ActivityFeedComponent } from './activity-feed.component';
import { MetricScorecardComponent, MetricsBarComponent } from './metric-scorecard.component';
import { ToastNotificationComponent, ToastContainerComponent } from './toast-notification.service';

// Services
import { ToastNotificationService } from './toast-notification.service';

@NgModule({
  declarations: [
    SocDashboardComponent,
    VideoFeedTileComponent,
    VideoFeedDetailComponent,
    ActivityFeedComponent,
    MetricScorecardComponent,
    MetricsBarComponent,
    ToastNotificationComponent,
    ToastContainerComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    BrowserAnimationsModule,
  ],
  providers: [
    ToastNotificationService,
  ],
  exports: [
    SocDashboardComponent,
    ToastContainerComponent,
  ],
})
export class SocDashboardModule { }
```

### 2. Update App Module

Update `frontend/src/app/app.module.ts`:

```typescript
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

// Feature Modules
import { SocDashboardModule } from './components/soc-dashboard/soc-dashboard.module';

// Services
import { IdentityService } from './services/identity.service';
import { VehicleService } from './services/vehicle.service';
import { AttendanceModuleService } from './services/attendance-module.service';
import { OccupancyService } from './services/occupancy.service';
import { HttpErrorInterceptor } from './services/http-error.interceptor';

// Main Component
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule,
    SocDashboardModule,
  ],
  providers: [
    IdentityService,
    VehicleService,
    AttendanceModuleService,
    OccupancyService,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpErrorInterceptor,
      multi: true,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
```

### 3. Update App Routing

Update `frontend/src/app/app-routing.module.ts`:

```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SocDashboardComponent } from './components/soc-dashboard/soc-dashboard.component';

const routes: Routes = [
  {
    path: 'dashboard',
    component: SocDashboardComponent,
    data: { title: 'Security Operations Center' },
  },
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full',
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule { }
```

---

## Component Integration

### 1. Video Feed Components

**VideoFeedTileComponent** - Multi-camera grid tiles

```html
<app-video-feed-tile 
  [camera]="camera"
  [isSelected]="selectedCameraId === camera.id"
  (click)="selectCamera(camera.id)">
</app-video-feed-tile>
```

**VideoFeedDetailComponent** - Single camera detailed view

```html
<app-video-feed-detail 
  [camera]="selectedCamera"
  [liveData]="liveData$ | async">
</app-video-feed-detail>
```

Canvas overlay automatically renders:
- Detection bounding boxes (cyan, semi-transparent)
- Zone overlays (line crossing, restricted areas)
- Real-time coordinates transformation

### 2. Activity Feed Component

```html
<app-activity-feed 
  [events$]="events$">
</app-activity-feed>
```

Features:
- Real-time event display (max 50 events)
- Severity filtering (critical, warning, info, success)
- Thumbnail support for incidents
- Auto-dismiss on clear

### 3. Metric Scorecard Components

```html
<app-metrics-bar 
  [metrics$]="metrics$">
</app-metrics-bar>
```

Each metric displays:
- Live value with unit
- Trend indicator (up/down/stable)
- Sparkline chart (mini historical data)
- Status badge (normal/warning/critical)
- Last updated timestamp

### 4. Toast Notification System

Add to main app template:

```html
<app-toast-container></app-toast-container>
```

Usage in components:

```typescript
constructor(private toastService: ToastNotificationService) {}

showAlert() {
  this.toastService.critical(
    'Critical occupancy level exceeded',
    'Occupancy Alert',
    {
      label: 'View Details',
      callback: () => this.navigateToDetails()
    }
  );
}
```

---

## Service Configuration

### Dashboard Services Integration

The SOC dashboard connects to 4 main services:

#### 1. Occupancy Service
```typescript
this.occupancyService.facilityOccupancy$.subscribe(data => {
  // Live occupancy count: {occupancy_count, entering_count, exiting_count, density_level}
  this.updateMetric('occupancy', data.occupancy_count);
  this.addEvent({
    title: 'Occupancy Update',
    severity: data.density_level === 'HIGH' ? 'warning' : 'info',
  });
});
```

#### 2. Vehicle Service
```typescript
this.vehicleService.vehicleDetections$.subscribe(detections => {
  // Real-time vehicle detection
  detections.forEach(detection => {
    this.addEvent({
      title: `Vehicle Detected: ${detection.plate}`,
      metadata: { vehiclePlate: detection.plate },
    });
  });
});
```

#### 3. Attendance Service
```typescript
this.attendanceService.attendanceRecords$.subscribe(records => {
  // Check-in/out records
  records.forEach(record => {
    this.addEvent({
      title: `${record.employee_name} ${record.record_type}`,
      metadata: { personName: record.employee_name },
    });
  });
});
```

#### 4. Identity Service
```typescript
this.identityService.identities$.subscribe(identities => {
  // Face recognition results
  identities.forEach(identity => {
    this.addEvent({
      title: `Person Identified: ${identity.person_name}`,
      metadata: { personName: identity.person_name },
    });
  });
});
```

### API Endpoints Used

**Occupancy Module:**
- `GET /api/occupancy/live` - Live occupancy data
- `GET /api/occupancy/zones` - Zone configuration
- `GET /api/occupancy/alerts` - Active alerts

**Vehicle Module:**
- `GET /api/vehicles/detection` - Real-time detections
- `GET /api/vehicles/alerts` - Gate/perimeter alerts

**Attendance Module:**
- `GET /api/attendance/records` - Check-in/out logs
- `POST /api/attendance/override` - Manual correction form

**Identity Module:**
- `GET /api/identity/live` - Live identification
- `GET /api/identity/access` - Access control logs

---

## Styling & Theming

### Tailwind CSS Configuration

The dashboard uses a professional dark mode theme:

**Color Palette:**
- Background: Slate-900 (#0f172a)
- Surfaces: Slate-800 (#1e293b)
- Accents: Cyan-500 (#06b6d4) - Primary
- Success: Emerald-500 (#10b981)
- Alert: Rose-500 (#f43f5e)
- Warning: Amber-500 (#f59e0b)

**Custom Classes:**
- `.glow-cyan` - Cyan glow effect
- `.glow-emerald` - Emerald glow effect
- `.glow-rose` - Rose glow effect
- `.animate-siren` - Critical alert animation
- `.animate-glow` - Active indicator glow

### SCSS Animations

Pre-defined animations:
- `fadeInSlideUp` - Component entrance
- `slideInFromLeft` - Sidebar opening
- `scaleIn` - Modal appearance
- `siren` - Critical alert pulse
- `glow` - Active state indicator

### Responsive Design

Optimized breakpoints:
- **xs (320px)** - Mobile phones
- **sm (640px)** - Small tablets
- **md (768px)** - Standard tablets
- **lg (1024px)** - Small laptops
- **xl (1280px)** - Standard laptops (1080p)
- **2xl (1536px)** - Large monitors
- **3xl (1920px)** - Ultra-wide
- **4k (2560px)** - 4K monitors

---

## Real-Time Data Flow

### Event System

The dashboard implements a FIFO event queue:

```typescript
// Add event (automatically managed)
addEvent(event: ActivityEvent): void {
  const events = this.events$.value;
  events.unshift(event); // Add to front
  if (events.length > 50) events.pop(); // Remove oldest
  this.events$.next([...events]);
}

// Events flow from services → Dashboard → Activity Feed → Display
```

### Metric Updates

Metrics are updated with trend analysis:

```typescript
// Calculate trend
trend = currentValue > previousValue ? 'up' : currentValue < previousValue ? 'down' : 'stable';
trendPercent = Math.round((currentValue - previousValue) / previousValue * 100);

// Generate sparkline data for visualization
sparklineData: number[] = [...historical data points];
```

### WebSocket Integration (Optional)

For real-time updates without polling:

```typescript
// In service
private wsConnection = new WebSocket('ws://api.example.com/live');

wsConnection.onmessage = (event) => {
  const data = JSON.parse(event.data);
  this.dataSubject$.next(data);
};
```

---

## Usage Examples

### Example 1: Basic Dashboard Setup

```typescript
// In your route component
import { SocDashboardComponent } from './components/soc-dashboard/soc-dashboard.component';

@Component({
  selector: 'app-root',
  template: '<app-soc-dashboard></app-soc-dashboard>',
})
export class AppComponent {}
```

### Example 2: Custom Metric Addition

```typescript
// In dashboard component
const customMetric: MetricScorecard = {
  id: 'custom-metric',
  title: 'Custom Metric',
  value: 42,
  unit: 'units',
  color: 'purple',
  category: 'occupancy',
  icon: 'custom-icon',
  trend: 'up',
  trendPercent: 5,
  sparklineData: [10, 20, 30, 40, 42],
  lastUpdated: new Date(),
};

this.metrics$.next([...this.metrics$.value, customMetric]);
```

### Example 3: Displaying Toast Notifications

```typescript
// Success toast
this.toastService.success('Camera connected successfully', 'Connection');

// Error with action
this.toastService.error(
  'Failed to retrieve attendance records',
  'Attendance Error',
  {
    label: 'Retry',
    callback: () => this.retryLoad(),
  }
);

// Critical alert (persistent)
this.toastService.critical(
  'Critical occupancy threshold exceeded in Zone A',
  'Occupancy Alert'
);
```

### Example 4: Adding Detection Boxes

```typescript
// In video feed component
const detectionBox: DetectionBox = {
  x: 100,
  y: 50,
  width: 200,
  height: 300,
  label: 'Person',
  confidence: 0.95,
  color: 'cyan',
};

this.videoTile.addDetectionBox(detectionBox);
```

---

## Testing Checklist

### Unit Tests

- [ ] Dashboard component initializes with correct state
- [ ] Sidebar toggle animation works smoothly
- [ ] Events added to queue respect max size (50)
- [ ] Metrics update with correct trend calculation
- [ ] Modal form validation works
- [ ] Toast notifications auto-dismiss after duration

### Integration Tests

- [ ] Real-time streams from all 4 services flow correctly
- [ ] Activity feed displays events in correct order (newest first)
- [ ] Video tiles render canvas overlays
- [ ] Metric cards display sparkline charts
- [ ] Manual override modal submits to backend
- [ ] Export PDF/Excel buttons work

### E2E Tests

- [ ] Dashboard loads without errors
- [ ] All modules accessible via sidebar navigation
- [ ] View mode toggles between single/multi-camera
- [ ] Responsive layout on 1080p and 4K screens
- [ ] Toast notifications appear and disappear correctly
- [ ] Real-time updates reflect backend changes
- [ ] Performance: FPS stable (60+ in video tiles)

### Visual Tests

- [ ] Dark mode colors render correctly
- [ ] Animations are smooth and not jerky
- [ ] Responsive design looks good on mobile/tablet
- [ ] Text is readable with proper contrast
- [ ] Icons display correctly
- [ ] Canvas overlays align with video

---

## Troubleshooting

### Issue: Video feeds not displaying

**Solution:**
```typescript
// Check RTSP/HLS stream configuration
const stream = this.camera.stream_url;
console.log('Stream URL:', stream);

// Verify browser supports video codec
// For HLS: use hls.js library
import HLS from 'hls.js';

if (HLS.isSupported()) {
  const hls = new HLS();
  hls.loadSource(stream);
  hls.attachMedia(videoElement);
}
```

### Issue: Canvas overlay not rendering

**Solution:**
```typescript
// Ensure canvas size matches video dimensions
canvas.width = video.offsetWidth;
canvas.height = video.offsetHeight;

// Check context exists
const ctx = canvas.getContext('2d');
if (!ctx) console.error('Canvas context not available');

// Verify detection boxes have valid coordinates
console.log('Box:', box); // Ensure x, y, width, height are numbers
```

### Issue: Performance degradation with many events

**Solution:**
```typescript
// Limit event queue size (already done: max 50)
// Implement virtual scrolling for activity feed
import { ScrollingModule } from '@angular/cdk/scrolling';

// Use OnPush change detection strategy
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
})
```

### Issue: Real-time updates not flowing

**Solution:**
```typescript
// Verify service subscriptions in dashboard
this.setupRealTimeStreams();

// Check WebSocket connection
console.log('WebSocket state:', this.ws.readyState);

// Monitor BehaviorSubject emissions
this.occupancyService.facilityOccupancy$.subscribe(data => {
  console.log('Occupancy update:', data);
});
```

### Issue: Modal form not submitting

**Solution:**
```typescript
// Check form validation
console.log('Form valid:', this.overrideForm.valid);
console.log('Form value:', this.overrideForm.value);

// Verify backend endpoint
POST /api/attendance/override
Content-Type: application/json
{
  "employee_id": "E001",
  "date": "2024-01-15",
  "check_in": "09:00",
  "check_out": "17:30",
  "status": "approved",
  "reason": "Special approval"
}
```

---

## Performance Optimization Tips

### 1. Canvas Rendering
- Use `requestAnimationFrame()` for smooth 60 FPS
- Limit detection box count (max 50 per frame)
- Clear canvas before redrawing: `ctx.clearRect(0, 0, w, h)`

### 2. Real-Time Updates
- Use RxJS `throttleTime()` or `debounceTime()` to limit updates
- Implement OnPush change detection strategy
- Unsubscribe from observables in `ngOnDestroy()`

### 3. Video Playback
- Use HLS.js for adaptive bitrate streaming
- Implement canvas-based scaling for display
- Add error handling for stream failures

### 4. Memory Management
- Limit event queue (50 items max)
- Clear old metric sparkline data periodically
- Unload video streams when cameras deselected

---

## Next Steps

1. **Install Dependencies:**
   ```bash
   npm install hls.js chart.js
   npm install --save-dev @types/hls.js @types/chart.js
   ```

2. **Configure Backend APIs:**
   - Ensure all endpoints return correct JSON format
   - Implement WebSocket for real-time updates
   - Add CORS headers if needed

3. **Add Camera Configuration:**
   - Load camera list from backend
   - Display camera zones and detection areas
   - Configure alert thresholds per camera

4. **Implement Data Export:**
   - Add PDF/Excel export functionality
   - Include date range filtering
   - Generate compliance reports

5. **Add Role-Based Access:**
   - Implement Security vs HR views
   - Add permission checks
   - Restrict sensitive operations

---

## Support & Contributions

For issues, questions, or contributions:
1. Check the Troubleshooting section
2. Review component JSDoc comments
3. Check service integration guides
4. Contact: [your-email@company.com]

