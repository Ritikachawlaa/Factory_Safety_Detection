import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry { timestamp: Date; value: any; label: string; }

@Component({
  selector: 'app-module-line-crossing',
  templateUrl: './module-line-crossing.component.html',
  styleUrls: ['./module-line-crossing.component.css']
})
export class ModuleLineCrossingComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  cameraActive = false;
  enabledFeatures: EnabledFeatures = {
    human: true, vehicle: false, helmet: false, loitering: false, crowd: false,
    box_count: false, line_crossing: true, tracking: true, motion: false,
    face_detection: false, face_recognition: false
  };
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;
  private lineX = 0;

  constructor(public webcamService: SharedWebcamService, private detectionService: UnifiedDetectionService) {}

  ngOnInit(): void {
    // Don't auto-start - wait for user to click Start Camera
  }

  ngAfterViewInit(): void {
    // Calculate line position after view init
    if (this.canvasElement) {
      const canvas = this.canvasElement.nativeElement;
      this.lineX = canvas.width / 2;
    }
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
        // Setup canvas overlay
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
      this.lineX = canvas.width / 2;
      this.drawLine();
    });
  }

  private drawLine(): void {
    if (!this.canvasElement) return;
    
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw vertical red line at center
    ctx.strokeStyle = '#FF0000';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(this.lineX, 0);
    ctx.lineTo(this.lineX, canvas.height);
    ctx.stroke();
    
    // Draw label
    ctx.fillStyle = '#FF0000';
    ctx.font = 'bold 16px Arial';
    ctx.fillText('LINE', this.lineX + 10, 30);
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
    
    // Redraw line on canvas
    this.drawLine();
    
    // Send frame with line_x position
    this.detectionService.detect(frameData, this.enabledFeatures, this.lineX).subscribe({
      next: (result: DetectionResult) => {
        this.detectionResult = result;
        this.updateHistory(result);
        this.drawDetectionBoxes(result);
      },
      error: (error: any) => console.error('Detection error:', error)
    });
  }

  private drawDetectionBoxes(result: DetectionResult): void {
    if (!this.canvasElement) return;
    
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Redraw line first
    this.drawLine();
    
    // Draw boxes if available in result
    const boxes = (result as any).boxes || [];
    boxes.forEach((box: any) => {
      ctx.strokeStyle = '#00FF00';
      ctx.lineWidth = 2;
      ctx.strokeRect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
      
      // Draw track ID
      if (box.track_id !== undefined) {
        ctx.fillStyle = '#00FF00';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(`ID: ${box.track_id}`, box.x1, box.y1 - 5);
      }
    });
  }

  private updateHistory(result: DetectionResult): void {
    const crossed = result.line_crossed;
    const total = result.total_crossings || 0;
    const label = crossed ? `⚠️ Line crossed (Total: ${total})` : `No crossing (Total: ${total})`;
    this.history.unshift({ timestamp: new Date(), value: crossed, label });
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }

  get recentHistory(): HistoryEntry[] { return this.history.slice(0, 10); }
  formatTime(date: Date): string { return date.toLocaleTimeString(); }
}
