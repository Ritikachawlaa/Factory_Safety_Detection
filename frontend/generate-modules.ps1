# Module Component Generator Script for Angular
# This script generates all 11 remaining module components using the human module as a template

$modules = @(
    @{
        id = "vehicle"
        name = "Vehicle Detection"
        icon = "🚗"
        subtitle = "Monitor vehicle traffic and count"
        feature = "vehicle"
        primaryLabel = "Vehicles Detected"
        primaryIcon = "🚙"
        primaryValue = "detectionResult?.vehicle_count || 0"
        historyLabel = "`${result.vehicle_count} vehicles detected`"
        historyValue = "result.vehicle_count"
    },
    @{
        id = "helmet"
        name = "Helmet / PPE Detection"
        icon = "⛑️"
        subtitle = "Safety compliance monitoring"
        feature = "helmet"
        primaryLabel = "Compliance Rate"
        primaryIcon = "✅"
        primaryValue = "`${detectionResult?.ppe_compliance_rate || 0}%`"
        historyLabel = "`${result.ppe_compliance_rate}% compliant, ${result.helmet_violations} violations`"
        historyValue = "result.ppe_compliance_rate"
    },
    @{
        id = "loitering"
        name = "Loitering Detection"
        icon = "⏱️"
        subtitle = "Detect unauthorized presence"
        feature = "loitering"
        primaryLabel = "Loitering Count"
        primaryIcon = "👤"
        primaryValue = "detectionResult?.loitering_count || 0"
        historyLabel = "result.loitering_detected ? `⚠️ Loitering detected (${result.loitering_count})` : 'Area clear'"
        historyValue = "result.loitering_count"
    },
    @{
        id = "labour-count"
        name = "People / Labour Count"
        icon = "👥"
        subtitle = "Workforce monitoring"
        feature = "human"
        primaryLabel = "Labour Count"
        primaryIcon = "👷"
        primaryValue = "detectionResult?.labour_count || 0"
        historyLabel = "`${result.labour_count} workers present`"
        historyValue = "result.labour_count"
    },
    @{
        id = "crowd"
        name = "Crowd Density"
        icon = "🏢"
        subtitle = "Monitor crowd levels"
        feature = "crowd"
        primaryLabel = "Density Level"
        primaryIcon = "📊"
        primaryValue = "detectionResult?.crowd_density || 'Normal'"
        historyLabel = "`${result.crowd_density} density, ${result.occupied_area}% occupied`"
        historyValue = "result.occupied_area"
    },
    @{
        id = "box-count"
        name = "Box Production Counting"
        icon = "📦"
        subtitle = "Track production output"
        feature = "box_count"
        primaryLabel = "Box Count"
        primaryIcon = "📦"
        primaryValue = "detectionResult?.box_count || 0"
        historyLabel = "`${result.box_count} boxes counted`"
        historyValue = "result.box_count"
    },
    @{
        id = "line-crossing"
        name = "Line Crossing"
        icon = "➡️"
        subtitle = "Monitor boundary violations"
        feature = "line_crossing"
        primaryLabel = "Total Crossings"
        primaryIcon = "🔢"
        primaryValue = "detectionResult?.total_crossings || 0"
        historyLabel = "result.line_crossed ? '⚠️ Line crossed detected' : 'No crossing'"
        historyValue = "result.total_crossings"
    },
    @{
        id = "tracking"
        name = "Auto Tracking"
        icon = "🎯"
        subtitle = "Object tracking system"
        feature = "tracking"
        primaryLabel = "Tracked Objects"
        primaryIcon = "🎯"
        primaryValue = "detectionResult?.tracked_objects || 0"
        historyLabel = "`${result.tracked_objects} objects tracked`"
        historyValue = "result.tracked_objects"
    },
    @{
        id = "motion"
        name = "Smart Motion Detection"
        icon = "💨"
        subtitle = "AI-validated motion analysis"
        feature = "motion"
        primaryLabel = "Motion Intensity"
        primaryIcon = "📊"
        primaryValue = "`${detectionResult?.motion_intensity || 0}%`"
        historyLabel = "result.motion_detected ? `💨 Motion: ${result.motion_intensity}%` : 'No motion'"
        historyValue = "result.motion_intensity"
    },
    @{
        id = "face-detection"
        name = "Face Detection"
        icon = "😊"
        subtitle = "Detect faces in real-time"
        feature = "face_detection"
        primaryLabel = "Faces Detected"
        primaryIcon = "😊"
        primaryValue = "detectionResult?.faces_detected || 0"
        historyLabel = "`${result.faces_detected} faces detected`"
        historyValue = "result.faces_detected"
    },
    @{
        id = "face-recognition"
        name = "Face Recognition"
        icon = "🔍"
        subtitle = "Identify known individuals"
        feature = "face_recognition"
        primaryLabel = "Recognized"
        primaryIcon = "✅"
        primaryValue = "detectionResult?.faces_recognized?.length || 0"
        historyLabel = "recognized > 0 ? `${recognized} faces recognized` : 'No faces recognized'"
        historyValue = "result.faces_recognized?.length || 0"
    }
)

$basePath = "c:\Users\ritik\Desktop\New Factory\Factory_Safety_Detection\frontend\src\app\components\modules"

Write-Host "🚀 Generating module components..." -ForegroundColor Cyan

foreach ($module in $modules) {
    $componentName = "module-$($module.id)"
    $className = $componentName.Split('-') | ForEach-Object { $_.Substring(0,1).ToUpper() + $_.Substring(1) }
    $className = $className -join ''
    $componentPath = Join-Path $basePath $componentName
    
    Write-Host "   Creating $componentName..." -ForegroundColor Yellow
    
    # TypeScript Component
    $tsContent = @"
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
  selector: 'app-$componentName',
  templateUrl: './$componentName.component.html',
  styleUrls: ['./$componentName.component.css']
})
export class $($className)Component implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;

  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;

  enabledFeatures: EnabledFeatures = {
    human: $($module.feature -eq 'human' -or $module.feature -eq 'labour'),
    vehicle: $($module.feature -eq 'vehicle'),
    helmet: $($module.feature -eq 'helmet'),
    loitering: $($module.feature -eq 'loitering'),
    crowd: $($module.feature -eq 'crowd'),
    box_count: $($module.feature -eq 'box_count'),
    line_crossing: $($module.feature -eq 'line_crossing'),
    tracking: $($module.feature -eq 'tracking'),
    motion: $($module.feature -eq 'motion'),
    face_detection: $($module.feature -eq 'face_detection'),
    face_recognition: $($module.feature -eq 'face_recognition')
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
      next: (result) => {
        this.detectionResult = result;
        this.updateHistory(result);
        this.updateStats(result);
      },
      error: (error) => {
        console.error('Detection error:', error);
      }
    });
  }

  private updateHistory(result: DetectionResult): void {
    const value = $($module.historyValue);
    const label = $($module.historyLabel);
    
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
    const currentValue = $($module.historyValue);
    if (typeof currentValue === 'number' && currentValue > this.peakCount) {
      this.peakCount = currentValue;
    }

    if (this.history.length > 0) {
      const numericValues = this.history.filter(e => typeof e.value === 'number');
      if (numericValues.length > 0) {
        const sum = numericValues.reduce((acc, entry) => acc + (entry.value || 0), 0);
        this.averageCount = Math.round(sum / numericValues.length);
      }
    }
  }

  get recentHistory(): HistoryEntry[] {
    return this.history.slice(0, 10);
  }

  formatTime(date: Date): string {
    return date.toLocaleTimeString();
  }
}
"@
    
    # HTML Template
    $htmlContent = @"
<div class="module-container">
  <div class="module-header">
    <div class="header-left">
      <span class="module-icon">$($module.icon)</span>
      <div>
        <h1 class="module-title">$($module.name)</h1>
        <p class="module-subtitle">$($module.subtitle)</p>
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
        <div class="stat-icon">$($module.primaryIcon)</div>
        <div class="stat-content">
          <p class="stat-label">$($module.primaryLabel)</p>
          <p class="stat-value">{{ $($module.primaryValue) }}</p>
        </div>
      </div>

      <div class="stat-card secondary">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <p class="stat-label">Peak Value</p>
          <p class="stat-value">{{ peakCount }}</p>
        </div>
      </div>

      <div class="stat-card tertiary">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <p class="stat-label">Average</p>
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
"@

    # Create files
    Set-Content -Path (Join-Path $componentPath "$componentName.component.ts") -Value $tsContent -Force
    Set-Content -Path (Join-Path $componentPath "$componentName.component.html") -Value $htmlContent -Force
    
    # Copy CSS from human module (they all use the same styles)
    Copy-Item -Path (Join-Path $basePath "module-human\module-human.component.css") -Destination (Join-Path $componentPath "$componentName.component.css") -Force
    
    Write-Host "   ✅ $componentName created" -ForegroundColor Green
}

Write-Host "`n✅ All module components generated successfully!" -ForegroundColor Green
Write-Host "   Next: Update app.module.ts to declare these components" -ForegroundColor Cyan
