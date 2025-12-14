import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard-main',
  templateUrl: './dashboard-main.component.html',
  styleUrls: ['./dashboard-main.component.css']
})
export class DashboardMainComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;

  // Webcam state
  webcamInitialized = false;
  webcamError: string | null = null;

  // Detection state
  isDetecting = false;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;

  // All features enabled for overview
  enabledFeatures: EnabledFeatures = {
    human: true,
    vehicle: true,
    helmet: true,
    loitering: true,
    crowd: true,
    box_count: true,
    line_crossing: true,
    tracking: true,
    motion: true,
    face_detection: true,
    face_recognition: true
  };

  // Stats
  totalFramesProcessed = 0;
  private frameInterval = 500; // ms

  constructor(
    public webcamService: SharedWebcamService,
    private detectionService: UnifiedDetectionService,
    private router: Router
  ) {}

  async ngOnInit(): Promise<void> {
    // Initialize webcam immediately on dashboard load
    await this.initializeWebcam();
  }

  ngOnDestroy(): void {
    this.stopDetection();
    // Don't stop webcam - it's shared across app
  }

  /**
   * Initialize shared webcam
   */
  async initializeWebcam(): Promise<void> {
    try {
      await this.webcamService.initializeWebcam();
      
      // Wait for view to initialize
      setTimeout(() => {
        if (this.videoElement) {
          this.webcamService.attachVideoElement(this.videoElement.nativeElement);
          this.webcamInitialized = true;
          
          // Auto-start detection after webcam is ready
          setTimeout(() => this.startDetection(), 1000);
        }
      }, 100);

    } catch (error: any) {
      this.webcamError = error?.message || 'Could not access webcam';
      console.error('Webcam initialization failed:', error);
    }
  }

  /**
   * Start detection loop
   */
  startDetection(): void {
    if (!this.webcamInitialized || this.isDetecting) {
      return;
    }

    this.isDetecting = true;

    this.detectionSubscription = interval(this.frameInterval).subscribe(() => {
      this.processFrame();
    });

    console.log('✅ Detection started on dashboard');
  }

  /**
   * Stop detection loop
   */
  stopDetection(): void {
    if (this.detectionSubscription) {
      this.detectionSubscription.unsubscribe();
      this.isDetecting = false;
      console.log('🛑 Detection stopped');
    }
  }

  /**
   * Process single frame
   */
  private processFrame(): void {
    const frameData = this.webcamService.captureFrame();
    if (!frameData) return;

    this.detectionService.detect(frameData, this.enabledFeatures).subscribe({
      next: (result: DetectionResult) => {
        this.detectionResult = result;
        this.totalFramesProcessed++;
      },
      error: (error: any) => {
        console.error('Detection error:', error);
      }
    });
  }

  /**
   * Navigate to specific module
   */
  navigateToModule(moduleRoute: string): void {
    this.router.navigate([`/dashboard/${moduleRoute}`]);
  }

  /**
   * Quick stats for overview
   */
  get quickStats() {
    if (!this.detectionResult) {
      return {
        people: 0,
        vehicles: 0,
        alerts: 0,
        production: 0
      };
    }

    return {
      people: this.detectionResult.people_count,
      vehicles: this.detectionResult.vehicle_count,
      alerts: this.detectionResult.helmet_violations + (this.detectionResult.loitering_detected ? 1 : 0),
      production: this.detectionResult.box_count
    };
  }
}
