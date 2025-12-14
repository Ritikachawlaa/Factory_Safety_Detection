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
  selector: 'app-module-human',
  templateUrl: './module-human.component.html',
  styleUrls: ['./module-human.component.css']
})
export class ModuleHumanComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;

  // Detection state
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  cameraActive = false;

  // Feature configuration - ONLY human detection enabled
  enabledFeatures: EnabledFeatures = {
    human: true,
    vehicle: false,
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

  // History tracking (in-memory)
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;

  // Module-specific stats
  peakCount = 0;
  averageCount = 0;

  constructor(
    public webcamService: SharedWebcamService,
    private detectionService: UnifiedDetectionService
  ) {}

  ngOnInit(): void {
    // Don't auto-start - wait for user to click Start Camera
  }

  ngOnDestroy(): void {
    this.stopDetection();
    this.stopCamera();
  }

  /**
   * Start camera
   */
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

  /**
   * Stop camera
   */
  stopCamera(): void {
    this.stopDetection(); // Stop detection if running
    this.webcamService.stopWebcam();
    this.cameraActive = false;
  }

  /**
   * Start detection loop
   */
  startDetection(): void {
    this.isDetecting = true;

    this.detectionSubscription = interval(500).subscribe(() => {
      this.processFrame();
    });
  }

  /**
   * Stop detection
   */
  stopDetection(): void {
    if (this.detectionSubscription) {
      this.detectionSubscription.unsubscribe();
      this.isDetecting = false;
    }
  }

  /**
   * Process frame
   */
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

  /**
   * Update history
   */
  private updateHistory(result: DetectionResult): void {
    this.history.unshift({
      timestamp: new Date(),
      value: result.people_count,
      label: `${result.people_count} people detected`
    });

    // Keep only last N items
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }

  /**
   * Update module stats
   */
  private updateStats(result: DetectionResult): void {
    // Update peak
    if (result.people_count > this.peakCount) {
      this.peakCount = result.people_count;
    }

    // Calculate average
    if (this.history.length > 0) {
      const sum = this.history.reduce((acc, entry) => acc + (entry.value || 0), 0);
      this.averageCount = Math.round(sum / this.history.length);
    }
  }

  /**
   * Get recent history (last 10)
   */
  get recentHistory(): HistoryEntry[] {
    return this.history.slice(0, 10);
  }

  /**
   * Format timestamp
   */
  formatTime(date: Date): string {
    return date.toLocaleTimeString();
  }
}
