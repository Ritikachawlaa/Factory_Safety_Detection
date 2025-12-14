import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry { timestamp: Date; value: any; label: string; }

@Component({
  selector: 'app-module-tracking',
  templateUrl: './module-tracking.component.html',
  styleUrls: ['./module-tracking.component.css']
})
export class ModuleTrackingComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  cameraActive = false;
  enabledFeatures: EnabledFeatures = {
    human: false, vehicle: false, helmet: false, loitering: false, crowd: false,
    box_count: false, line_crossing: false, tracking: true, motion: false,
    face_detection: false, face_recognition: false
  };
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;

  constructor(public webcamService: SharedWebcamService, private detectionService: UnifiedDetectionService) {}

  ngOnInit(): void {
    // Don't auto-start - wait for user to click Start Camera
  }

  ngOnDestroy(): void {
    this.stopDetection();
    this.stopCamera();
  }

  startCamera(): void {
    this.webcamService.initializeWebcam().then(() => {
      this.cameraActive = true;
      if (this.videoElement && this.webcamService.isActive()) {
        this.webcamService.attachVideoElement(this.videoElement.nativeElement);
      }
    }).catch(err => {
      console.error('Failed to start camera:', err);
    });
  }

  stopCamera(): void {
    this.stopDetection();
    this.webcamService.stopWebcam();
    this.cameraActive = false;
  }
  startDetection(): void {
    this.isDetecting = true;
    this.detectionSubscription = interval(500).subscribe(() => this.processFrame());
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
      },
      error: (error: any) => console.error('Detection error:', error)
    });
  }
  private updateHistory(result: DetectionResult): void {
    const value = result.tracked_objects || 0;
    const label = `${value} objects tracked`;
    this.history.unshift({ timestamp: new Date(), value, label });
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }
  get recentHistory(): HistoryEntry[] { return this.history.slice(0, 10); }
  formatTime(date: Date): string { return date.toLocaleTimeString(); }
}
