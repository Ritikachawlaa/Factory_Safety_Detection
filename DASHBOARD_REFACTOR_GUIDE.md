# Dashboard-Centric Frontend Refactor - Implementation Guide

## ✅ What Has Been Completed

### 1. **Core Infrastructure** (100% Complete)
- ✅ **SharedWebcamService** - Persistent webcam across all pages
- ✅ **SidebarComponent** - Navigation with 12 feature links
- ✅ **DashboardMainComponent** - New entry point at `/dashboard`
- ✅ **ModuleHumanComponent** - Example module implementation
- ✅ **Routing** - Dashboard-centric routing structure
- ✅ **App Module** - Component registrations
- ✅ **App Layout** - Sidebar + content area layout

### 2. **Key Features Implemented**
- ✅ Webcam initialized once on dashboard load
- ✅ Persistent video stream shared across navigation
- ✅ Sidebar with 12 module links
- ✅ Dashboard as primary entry point (`/dashboard`)
- ✅ Per-module routing (`/dashboard/:module`)
- ✅ Historical stats panel (in-memory)
- ✅ Theme consistency maintained

---

## 🚧 What Needs To Be Completed

### **Remaining 11 Module Components**

You need to create 11 more module components following the exact same pattern as `module-human`.

**List of Modules:**
1. ✅ module-human (DONE - use as template)
2. ⚠️ module-vehicle
3. ⚠️ module-helmet
4. ⚠️ module-loitering
5. ⚠️ module-labour-count
6. ⚠️ module-crowd
7. ⚠️ module-box-count
8. ⚠️ module-line-crossing
9. ⚠️ module-tracking
10. ⚠️ module-motion
11. ⚠️ module-face-detection
12. ⚠️ module-face-recognition

---

## 📋 Step-by-Step Guide to Create Each Module

### Template Structure (Copy from module-human)

Each module needs **3 files**:
1. `module-{name}.component.ts`
2. `module-{name}.component.html`
3. `module-{name}.component.css` (copy from module-human)

### Configuration Reference

Use this table to customize each module:

| Module ID | Icon | Feature Flag | Primary Stat | Primary Value | History Label |
|-----------|------|--------------|--------------|---------------|---------------|
| **vehicle** | 🚗 | `vehicle: true` | "Vehicles Detected" | `detectionResult?.vehicle_count \|\| 0` | `${result.vehicle_count} vehicles detected` |
| **helmet** | ⛑️ | `helmet: true` | "Compliance Rate" | `${detectionResult?.ppe_compliance_rate \|\| 0}%` | `${result.ppe_compliance_rate}% compliant` |
| **loitering** | ⏱️ | `loitering: true` | "Loitering Count" | `detectionResult?.loitering_count \|\| 0` | `Loitering detected: ${result.loitering_count}` |
| **labour-count** | 👥 | `human: true` | "Labour Count" | `detectionResult?.labour_count \|\| 0` | `${result.labour_count} workers present` |
| **crowd** | 🏢 | `crowd: true` | "Density Level" | `detectionResult?.crowd_density \|\| 'Normal'` | `${result.crowd_density} density` |
| **box-count** | 📦 | `box_count: true` | "Box Count" | `detectionResult?.box_count \|\| 0` | `${result.box_count} boxes counted` |
| **line-crossing** | ➡️ | `line_crossing: true` | "Total Crossings" | `detectionResult?.total_crossings \|\| 0` | `${result.total_crossings} crossings` |
| **tracking** | 🎯 | `tracking: true` | "Tracked Objects" | `detectionResult?.tracked_objects \|\| 0` | `${result.tracked_objects} tracked` |
| **motion** | 💨 | `motion: true` | "Motion Intensity" | `${detectionResult?.motion_intensity \|\| 0}%` | `Motion: ${result.motion_intensity}%` |
| **face-detection** | 😊 | `face_detection: true` | "Faces Detected" | `detectionResult?.faces_detected \|\| 0` | `${result.faces_detected} faces detected` |
| **face-recognition** | 🔍 | `face_recognition: true` | "Recognized" | `detectionResult?.faces_recognized?.length \|\| 0` | `${result.faces_recognized?.length} identified` |

---

## 🔨 Manual Creation Steps (For Each Module)

### Example: Creating `module-vehicle`

#### Step 1: Create Directory
```bash
mkdir src/app/components/modules/module-vehicle
```

#### Step 2: Create TypeScript Component

**File:** `module-vehicle.component.ts`

```typescript
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry {
  timestamp: Date;
  value: any;
  label: string;
}

@Component({
  selector: 'app-module-vehicle',
  templateUrl: './module-vehicle.component.html',
  styleUrls: ['./module-vehicle.component.css']
})
export class ModuleVehicleComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;

  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;

  // IMPORTANT: Enable ONLY the vehicle feature
  enabledFeatures: EnabledFeatures = {
    human: false,
    vehicle: true,  // ← Only this is true
    helmet: false,
    loitering: false,
    crowd: false,
    box_count: false,
    line_crossing: false,
    tracking: false,
    motion: false,
    face_detection: false,
    face_recognition: false
  };

  history: HistoryEntry[] = [];
  maxHistoryItems = 50;
  peakCount = 0;
  averageCount = 0;

  constructor(
    public webcamService: SharedWebcamService,
    private detectionService: UnifiedDetectionService
  ) {}

  ngOnInit(): void {
    setTimeout(() => {
      if (this.videoElement && this.webcamService.isActive()) {
        this.webcamService.attachVideoElement(this.videoElement.nativeElement);
      }
    }, 100);
    this.startDetection();
  }

  ngOnDestroy(): void {
    this.stopDetection();
  }

  startDetection(): void {
    this.isDetecting = true;
    this.detectionSubscription = interval(500).subscribe(() => {
      this.processFrame();
    });
  }

  stopDetection(): void {
    if (this.detectionSubscription) {
      this.detectionSubscription.unsubscribe();
      this.isDetecting = false;
    }
  }

  private processFrame(): void {
    const frameData = this.webcamService.captureFrame();
    if (!frameData) return;

    this.detectionService.detect(frameData, this.enabledFeatures).subscribe({
      next: (result: DetectionResult) => {
        this.detectionResult = result;
        this.updateHistory(result);
        this.updateStats(result);
      },
      error: (error: any) => {
        console.error('Detection error:', error);
      }
    });
  }

  private updateHistory(result: DetectionResult): void {
    // Extract vehicle-specific data
    const value = result.vehicle_count;
    const label = `${result.vehicle_count} vehicles detected`;
    
    this.history.unshift({
      timestamp: new Date(),
      value: value,
      label: label
    });

    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }

  private updateStats(result: DetectionResult): void {
    const currentValue = result.vehicle_count;
    if (currentValue > this.peakCount) {
      this.peakCount = currentValue;
    }

    if (this.history.length > 0) {
      const sum = this.history.reduce((acc, entry) => acc + (entry.value || 0), 0);
      this.averageCount = Math.round(sum / this.history.length);
    }
  }

  get recentHistory(): HistoryEntry[] {
    return this.history.slice(0, 10);
  }

  formatTime(date: Date): string {
    return date.toLocaleTimeString();
  }
}
```

#### Step 3: Create HTML Template

**File:** `module-vehicle.component.html`

```html
<div class="module-container">
  <div class="module-header">
    <div class="header-left">
      <span class="module-icon">🚗</span>
      <div>
        <h1 class="module-title">Vehicle Detection</h1>
        <p class="module-subtitle">Monitor vehicle traffic and count</p>
      </div>
    </div>
    <div class="status-badge" [class.active]="isDetecting">
      <span class="badge-dot"></span>
      {{ isDetecting ? 'Detecting' : 'Standby' }}
    </div>
  </div>

  <div class="content-grid">
    <div class="video-section">
      <div class="video-container">
        <video #videoElement autoplay playsinline class="video-feed"></video>
        <div class="live-indicator">
          <span class="live-dot"></span>
          LIVE
        </div>
      </div>
    </div>

    <div class="stats-panel">
      <div class="stat-card primary">
        <div class="stat-icon">🚙</div>
        <div class="stat-content">
          <p class="stat-label">Vehicles Detected</p>
          <p class="stat-value">{{ detectionResult?.vehicle_count || 0 }}</p>
        </div>
      </div>

      <div class="stat-card secondary">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <p class="stat-label">Peak Vehicles</p>
          <p class="stat-value">{{ peakCount }}</p>
        </div>
      </div>

      <div class="stat-card tertiary">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <p class="stat-label">Average Traffic</p>
          <p class="stat-value">{{ averageCount }}</p>
        </div>
      </div>
    </div>
  </div>

  <div class="history-section">
    <h2 class="history-title">Recent Activity</h2>
    <div class="history-list">
      <div *ngFor="let entry of recentHistory" class="history-item">
        <div class="history-time">{{ formatTime(entry.timestamp) }}</div>
        <div class="history-label">{{ entry.label }}</div>
        <div class="history-value">{{ entry.value }}</div>
      </div>

      <div *ngIf="recentHistory.length === 0" class="history-empty">
        <p>No activity recorded yet</p>
      </div>
    </div>
  </div>
</div>
```

#### Step 4: Copy CSS

```bash
cp src/app/components/modules/module-human/module-human.component.css \
   src/app/components/modules/module-vehicle/module-vehicle.component.css
```

#### Step 5: Update app.module.ts

Add to imports:
```typescript
import { ModuleVehicleComponent } from './components/modules/module-vehicle/module-vehicle.component';
```

Add to declarations array:
```typescript
declarations: [
  // ...existing...
  ModuleVehicleComponent
]
```

#### Step 6: Update app-routing.module.ts

Add to imports:
```typescript
import { ModuleVehicleComponent } from './components/modules/module-vehicle/module-vehicle.component';
```

Add to routes:
```typescript
{ path: 'dashboard/vehicle', component: ModuleVehicleComponent },
```

---

## 🎯 Quick Checklist for Each Module

For each of the 11 remaining modules:

- [ ] Create component directory
- [ ] Create `.ts` file (copy from human, modify feature flags + data extraction)
- [ ] Create `.html` file (copy from human, modify icon + labels + values)
- [ ] Copy `.css` file from module-human
- [ ] Import component in `app.module.ts`
- [ ] Add to declarations in `app.module.ts`
- [ ] Import component in `app-routing.module.ts`
- [ ] Add route in `app-routing.module.ts`
- [ ] Test navigation and detection

---

## 🧪 Testing Checklist

After creating all modules:

### 1. **Navigation Test**
- [ ] `/dashboard` loads with webcam
- [ ] Clicking each sidebar link navigates correctly
- [ ] Webcam stays active during navigation
- [ ] No console errors

### 2. **Detection Test**
- [ ] Each module shows live video feed
- [ ] Each module displays correct stats
- [ ] History panel updates
- [ ] Peak/average calculations work

### 3. **Performance Test**
- [ ] Webcam opens only once
- [ ] Navigation is smooth
- [ ] No memory leaks on route changes
- [ ] Frame processing is stable

---

## 🚀 Next Steps

1. **Create remaining 11 modules** using the pattern above
2. **Test each module** individually
3. **Verify routing** works for all 12 modules
4. **Remove old components** (`/unified-live`, old dashboard) if no longer needed
5. **Deploy** and show to client

---

## 📝 Notes

- **Backend remains unchanged** - all API calls use `/api/detect`
- **No authentication** required for now (can add later)
- **No database** needed - history is in-memory
- **Theme consistent** - all modules use same CSS

---

## 🆘 Troubleshooting

**Issue:** Component not found
- Solution: Check import paths are `../../../services/...` (3 levels up)

**Issue:** Routing not working
- Solution: Verify component is imported AND added to declarations in app.module.ts

**Issue:** Webcam not showing
- Solution: Check SharedWebcamService is initialized in DashboardMainComponent

**Issue:** Detection not working
- Solution: Verify correct feature flag is set to `true` in enabledFeatures

---

## ✅ Summary

**What's Done:**
- Complete infrastructure for dashboard system
- Shared webcam service
- Sidebar navigation
- Main dashboard entry point
- Full example module (human)

**What You Need To Do:**
- Create 11 more module components (15 min each = ~3 hours)
- Following exact pattern of module-human
- Copy/paste/modify approach

**Result:**
- Professional dashboard-centric system
- Persistent webcam across modules
- Clean, modular architecture
- Client-ready UI

Good luck! 🎉
