import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit, signal } from '@angular/core';

/**
 * Detection object from backend
 */
export interface Detection {
  class: string;  // 'helmet', 'head', 'person', 'box', etc.
  confidence: number;
  bbox: [number, number, number, number];  // [x, y, width, height]
  trackingId?: number;
  label?: string;
}

/**
 * Live Feed Configuration
 */
export interface LiveFeedConfig {
  showBoundingBoxes: boolean;
  showTrackingIds: boolean;
  showConfidence: boolean;
  showCountingLine: boolean;
  countingLineY?: number;  // Y position for production counter line
  colorMap?: { [key: string]: string };  // Custom colors per class
}

/**
 * Reusable Live Feed Component with Canvas Overlay
 * 
 * This component renders:
 * - Base64 JPEG frames from webcam
 * - Real-time bounding boxes from ML detection
 * - Tracking IDs
 * - Virtual counting line (for production counter)
 * - Color-coded labels
 * 
 * Usage:
 * <app-live-feed 
 *   [frameData]="currentFrame"
 *   [detections]="detectionResults"
 *   [config]="feedConfig">
 * </app-live-feed>
 */
@Component({
  selector: 'app-live-feed',
  template: `
    <div class="live-feed-container relative bg-black rounded-lg overflow-hidden" 
         [style.aspect-ratio]="'16/9'">
      
      <!-- Base Video Frame (JPEG from webcam) -->
      <img 
        #videoFrame
        [src]="frameData() || 'data:image/gif;base64,R0lGODlhAQABAAAAACw='"
        class="absolute inset-0 w-full h-full object-contain"
        (load)="onFrameLoad()"
        alt="Live Feed">

      <!-- Canvas Overlay (for bounding boxes) -->
      <canvas 
        #overlayCanvas
        class="absolute inset-0 w-full h-full pointer-events-none"
        [width]="canvasWidth()"
        [height]="canvasHeight()">
      </canvas>

      <!-- Status Badge -->
      <div class="absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-bold"
           [ngClass]="isActive() ? 'bg-green-500 text-white animate-pulse' : 'bg-gray-700 text-gray-300'">
        <span class="inline-block w-2 h-2 rounded-full mr-1"
              [ngClass]="isActive() ? 'bg-white' : 'bg-gray-500'"></span>
        {{ isActive() ? 'LIVE' : 'NO SIGNAL' }}
      </div>

      <!-- FPS Counter -->
      <div class="absolute top-3 right-3 px-3 py-1 bg-black bg-opacity-70 rounded text-white text-xs font-mono"
           *ngIf="fps() > 0">
        {{ fps() }} FPS
      </div>

      <!-- Detection Count -->
      <div class="absolute bottom-3 left-3 px-3 py-1 bg-black bg-opacity-70 rounded text-white text-sm font-semibold"
           *ngIf="detections().length > 0">
        {{ detections().length }} Object{{ detections().length > 1 ? 's' : '' }} Detected
      </div>
    </div>
  `,
  styles: [`
    .live-feed-container {
      min-height: 400px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
  `]
})
export class LiveFeedComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('overlayCanvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('videoFrame') videoFrameRef!: ElementRef<HTMLImageElement>;

  // ============================================================================
  // INPUTS
  // ============================================================================

  @Input() set frameDataInput(value: string | null) {
    if (value) {
      this.frameData.set(value);
      this.frameCount++;
      this.calculateFPS();
    }
  }

  @Input() set detectionsInput(value: Detection[]) {
    this.detections.set(value || []);
  }

  @Input() config: LiveFeedConfig = {
    showBoundingBoxes: true,
    showTrackingIds: true,
    showConfidence: true,
    showCountingLine: false,
    colorMap: {
      'helmet': '#00ff00',  // Green
      'head': '#ff0000',     // Red
      'person': '#00d9ff',   // Cyan
      'box': '#ffff00',      // Yellow
      'verified': '#00ff00', // Green (attendance)
      'unknown': '#ff0000'   // Red (attendance)
    }
  };

  // ============================================================================
  // SIGNALS
  // ============================================================================

  frameData = signal<string | null>(null);
  detections = signal<Detection[]>([]);
  canvasWidth = signal<number>(640);
  canvasHeight = signal<number>(480);
  isActive = signal<boolean>(false);
  fps = signal<number>(0);

  // ============================================================================
  // STATE
  // ============================================================================

  private ctx: CanvasRenderingContext2D | null = null;
  private animationFrameId: number | null = null;
  private frameCount = 0;
  private lastFpsUpdate = Date.now();

  // ============================================================================
  // LIFECYCLE
  // ============================================================================

  ngOnInit(): void {
    console.log('📹 LiveFeed component initialized');
  }

  ngAfterViewInit(): void {
    this.initCanvas();
    this.startRendering();
  }

  ngOnDestroy(): void {
    this.stopRendering();
  }

  // ============================================================================
  // CANVAS INITIALIZATION
  // ============================================================================

  private initCanvas(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) return;

    this.ctx = canvas.getContext('2d');
    
    // Set canvas size to match parent container
    const container = canvas.parentElement;
    if (container) {
      this.canvasWidth.set(container.clientWidth);
      this.canvasHeight.set(container.clientHeight);
    }
  }

  onFrameLoad(): void {
    const img = this.videoFrameRef?.nativeElement;
    if (!img) return;

    // Update canvas size to match loaded frame
    this.canvasWidth.set(img.naturalWidth || 640);
    this.canvasHeight.set(img.naturalHeight || 480);
    this.isActive.set(true);
  }

  // ============================================================================
  // RENDERING LOOP
  // ============================================================================

  private startRendering(): void {
    const render = () => {
      this.drawOverlay();
      this.animationFrameId = requestAnimationFrame(render);
    };
    render();
  }

  private stopRendering(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Main render function - draws all overlays
   */
  private drawOverlay(): void {
    if (!this.ctx) return;

    const canvas = this.canvasRef.nativeElement;
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    this.ctx.clearRect(0, 0, width, height);

    // Draw counting line (if enabled)
    if (this.config.showCountingLine && this.config.countingLineY) {
      this.drawCountingLine(this.config.countingLineY);
    }

    // Draw bounding boxes
    if (this.config.showBoundingBoxes) {
      this.detections().forEach(detection => {
        this.drawBoundingBox(detection);
      });
    }
  }

  /**
   * Draw a single bounding box with label
   */
  private drawBoundingBox(detection: Detection): void {
    if (!this.ctx) return;

    const [x, y, width, height] = detection.bbox;
    const color = this.config.colorMap?.[detection.class] || '#00d9ff';

    // Draw box
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 3;
    this.ctx.strokeRect(x, y, width, height);

    // Draw label background
    const labelText = this.buildLabel(detection);
    const padding = 8;
    const fontSize = 14;
    this.ctx.font = `bold ${fontSize}px 'Inter', sans-serif`;
    const textWidth = this.ctx.measureText(labelText).width;
    
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x, y - fontSize - padding * 2, textWidth + padding * 2, fontSize + padding * 2);

    // Draw label text
    this.ctx.fillStyle = '#000';
    this.ctx.fillText(labelText, x + padding, y - padding - 2);

    // Draw tracking ID (if enabled)
    if (this.config.showTrackingIds && detection.trackingId) {
      this.ctx.fillStyle = color;
      this.ctx.fillRect(x, y, 30, 20);
      this.ctx.fillStyle = '#000';
      this.ctx.font = 'bold 12px monospace';
      this.ctx.fillText(`#${detection.trackingId}`, x + 5, y + 14);
    }
  }

  /**
   * Build label text for detection
   */
  private buildLabel(detection: Detection): string {
    let label = detection.label || detection.class.toUpperCase();
    
    if (this.config.showConfidence) {
      label += ` ${(detection.confidence * 100).toFixed(0)}%`;
    }
    
    return label;
  }

  /**
   * Draw virtual counting line (for production counter)
   */
  private drawCountingLine(y: number): void {
    if (!this.ctx) return;

    const canvas = this.canvasRef.nativeElement;
    const width = canvas.width;

    // Draw dashed line
    this.ctx.strokeStyle = '#ff9500';  // Orange
    this.ctx.lineWidth = 3;
    this.ctx.setLineDash([10, 5]);
    this.ctx.beginPath();
    this.ctx.moveTo(0, y);
    this.ctx.lineTo(width, y);
    this.ctx.stroke();
    this.ctx.setLineDash([]);

    // Draw label
    this.ctx.fillStyle = '#ff9500';
    this.ctx.fillRect(10, y - 25, 120, 20);
    this.ctx.fillStyle = '#000';
    this.ctx.font = 'bold 12px sans-serif';
    this.ctx.fillText('COUNTING LINE', 15, y - 10);
  }

  /**
   * Calculate FPS
   */
  private calculateFPS(): void {
    const now = Date.now();
    const elapsed = now - this.lastFpsUpdate;
    
    if (elapsed >= 1000) {
      this.fps.set(this.frameCount);
      this.frameCount = 0;
      this.lastFpsUpdate = now;
    }
  }
}
