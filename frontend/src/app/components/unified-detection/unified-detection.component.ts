import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-unified-detection',
  templateUrl: './unified-detection.component.html',
  styleUrls: ['./unified-detection.component.css']
})
export class UnifiedDetectionComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;

  // Webcam state
  webcamActive = false;
  stream: MediaStream | null = null;

  // Feature toggles (12 features)
  enabledFeatures: EnabledFeatures = {
    human: true,
    vehicle: false,
    helmet: true,
    loitering: false,
    crowd: false,
    box_count: false,
    line_crossing: false,
    tracking: false,
    motion: true,
    face_detection: false,
    face_recognition: false
  };

  // Detection results
  detectionResult: DetectionResult | null = null;
  
  // Processing state
  isProcessing = false;
  frameInterval = 400; // milliseconds between frames
  private detectionSubscription?: Subscription;

  // Stats
  totalFramesProcessed = 0;
  fps = 0;
  private lastFrameTime = Date.now();

  constructor(private detectionService: UnifiedDetectionService) {}

  ngOnInit(): void {
    // Auto-start webcam
    // this.startWebcam();
  }

  ngOnDestroy(): void {
    this.stopWebcam();
    this.stopDetection();
  }

  /**
   * Start webcam
   */
  async startWebcam(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      });

      if (this.videoElement) {
        this.videoElement.nativeElement.srcObject = this.stream;
        this.videoElement.nativeElement.play();
        this.webcamActive = true;
        
        // Auto-start detection
        setTimeout(() => this.startDetection(), 1000);
      }
    } catch (error) {
      console.error('Webcam access failed:', error);
      alert('Could not access webcam. Please check permissions.');
    }
  }

  /**
   * Stop webcam
   */
  stopWebcam(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
      this.webcamActive = false;
    }
  }

  /**
   * Start detection loop
   */
  startDetection(): void {
    if (!this.webcamActive) {
      alert('Please start webcam first');
      return;
    }

    this.isProcessing = true;
    
    // Process frames at specified interval
    this.detectionSubscription = interval(this.frameInterval).subscribe(() => {
      this.processFrame();
    });
  }

  /**
   * Stop detection
   */
  stopDetection(): void {
    this.isProcessing = false;
    if (this.detectionSubscription) {
      this.detectionSubscription.unsubscribe();
    }
  }

  /**
   * Process current frame
   */
  private processFrame(): void {
    if (!this.videoElement || !this.canvasElement) return;

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const context = canvas.getContext('2d');

    if (!context || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Draw video frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get base64 image data
    const frameData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

    // Send to backend
    this.detectionService.detect(frameData, this.enabledFeatures).subscribe({
      next: (result) => {
        this.detectionResult = result;
        this.totalFramesProcessed++;
        this.calculateFPS();
      },
      error: (error) => {
        console.error('Detection error:', error);
      }
    });
  }

  /**
   * Calculate FPS
   */
  private calculateFPS(): void {
    const now = Date.now();
    const timeDiff = (now - this.lastFrameTime) / 1000;
    this.fps = Math.round(1 / timeDiff);
    this.lastFrameTime = now;
  }

  /**
   * Reset counters
   */
  resetCounters(): void {
    this.detectionService.resetCounters().subscribe({
      next: () => {
        alert('Counters reset successfully');
      },
      error: (error) => {
        console.error('Reset failed:', error);
      }
    });
  }

  /**
   * Toggle feature
   */
  toggleFeature(feature: keyof EnabledFeatures): void {
    this.enabledFeatures[feature] = !this.enabledFeatures[feature];
  }

  /**
   * Get alert class based on detection results
   */
  getAlertClass(type: string): string {
    if (!this.detectionResult) return 'badge-secondary';

    switch (type) {
      case 'helmet':
        return this.detectionResult.helmet_violations > 0 ? 'badge-danger' : 'badge-success';
      case 'loitering':
        return this.detectionResult.loitering_detected ? 'badge-warning' : 'badge-success';
      case 'crowd':
        return this.detectionResult.crowd_detected ? 'badge-warning' : 'badge-success';
      case 'motion':
        return this.detectionResult.motion_detected ? 'badge-info' : 'badge-secondary';
      default:
        return 'badge-secondary';
    }
  }
}
