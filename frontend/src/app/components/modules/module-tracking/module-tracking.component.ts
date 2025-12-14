import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry { timestamp: Date; value: any; label: string; }

@Component({
  selector: 'app-module-tracking',
  templateUrl: './module-tracking.component.html',
  styleUrls: ['./module-tracking.component.css']
})
export class ModuleTrackingComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  cameraActive = false;
  enabledFeatures: EnabledFeatures = {
    human: true, vehicle: false, helmet: false, loitering: false, crowd: false,
    box_count: false, line_crossing: false, tracking: true, motion: false,
    face_detection: false, face_recognition: false
  };
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;

  constructor(public webcamService: SharedWebcamService, private detectionService: UnifiedDetectionService) {}

  ngOnInit(): void {
    // Don't auto-start - wait for user to click Start Camera
  }

  ngAfterViewInit(): void {
    // Setup canvas after view init
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
        this.setupCanvasOverlay();
      }
    }).catch(err => {
      console.error('Failed to start camera:', err);
    });
  }

  private setupCanvasOverlay(): void {
    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    
    video.addEventListener('loadedmetadata', () => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    });
  }

  stopCamera(): void {
    this.stopDetection();
    this.webcamService.stopWebcam();
    this.cameraActive = false;
  }
  startDetection(): void {
    this.isDetecting = true;
    this.detectionSubscription = interval(300).subscribe(() => this.processFrame());
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
        this.drawTrackingBoxes(result);
      },
      error: (error: any) => console.error('Detection error:', error)
    });
  }

  private drawTrackingBoxes(result: DetectionResult): void {
    if (!this.canvasElement) return;
    
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw boxes if available in result
    const boxes = (result as any).boxes || [];
    boxes.forEach((box: any) => {
      // Draw bounding box
      ctx.strokeStyle = '#00FF00';
      ctx.lineWidth = 3;
      ctx.strokeRect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
      
      // Draw track ID with background
      if (box.track_id !== undefined) {
        const label = `ID: ${box.track_id}`;
        ctx.font = 'bold 18px Arial';
        const textWidth = ctx.measureText(label).width;
        
        // Background rectangle
        ctx.fillStyle = '#00FF00';
        ctx.fillRect(box.x1, box.y1 - 30, textWidth + 10, 25);
        
        // Text
        ctx.fillStyle = '#000000';
        ctx.fillText(label, box.x1 + 5, box.y1 - 10);
      }
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
