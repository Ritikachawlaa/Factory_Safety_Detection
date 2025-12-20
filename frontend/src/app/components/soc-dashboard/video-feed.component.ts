import { Component, Input, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

// ============================================================================
// TYPES
// ============================================================================

export interface DetectionBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
  color: 'cyan' | 'emerald' | 'rose' | 'amber';
}

export interface ZoneOverlay {
  name: string;
  type: 'line' | 'polygon' | 'rectangle';
  points: Array<{ x: number; y: number }>;
  color: string;
  alpha: number;
}

// ============================================================================
// VIDEO FEED TILE COMPONENT (for multi-camera view)
// ============================================================================

@Component({
  selector: 'app-video-feed-tile',
  template: `
    <div 
      [class.ring-2]="isSelected"
      [class.ring-cyan-500]="isSelected"
      class="relative bg-slate-800 border border-slate-700 rounded-lg overflow-hidden cursor-pointer hover:border-slate-600 transition-all group">
      
      <!-- Video Canvas -->
      <div class="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
        <video 
          #videoElement
          class="w-full h-full object-cover"
          autoplay
          muted
          playsinline>
        </video>
        
        <!-- Detection Canvas -->
        <canvas 
          #detectionCanvas
          class="absolute inset-0 w-full h-full">
        </canvas>

        <!-- Status Overlay Bar -->
        <div class="absolute top-0 left-0 right-0 bg-gradient-to-b from-black to-transparent p-2 text-xs font-mono">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-cyan-400">{{ camera?.name }}</span>
              <span class="text-emerald-400">● LIVE</span>
            </div>
            <div class="text-slate-400">{{ fps }}fps</div>
          </div>
          <div class="text-slate-400 mt-1">{{ resolution }}</div>
        </div>

        <!-- Zone Overlay Labels -->
        <div class="absolute bottom-2 left-2 text-xs text-slate-300 bg-black bg-opacity-50 px-2 py-1 rounded">
          {{ camera?.location }}
        </div>
      </div>

      <!-- Info Card (hover) -->
      <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
        <div class="text-sm font-semibold text-white">{{ camera?.name }}</div>
        <div class="text-xs text-slate-300">{{ camera?.location }}</div>
        <div class="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-300">
          <div>Capacity: <span class="text-cyan-400">{{ camera?.capacity }}</span></div>
          <div>Area: <span class="text-emerald-400">{{ camera?.view_area_sqm }}m²</span></div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class VideoFeedTileComponent implements OnInit, AfterViewInit {
  @Input() camera: any;
  @Input() isSelected: boolean = false;
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('detectionCanvas') canvasElement!: ElementRef<HTMLCanvasElement>;

  fps = 30;
  resolution = '1920x1080';
  detectionBoxes$ = new BehaviorSubject<DetectionBox[]>([]);
  zoneOverlays$ = new BehaviorSubject<ZoneOverlay[]>([]);

  ngOnInit(): void {
    // Initialize with mock stream (replace with actual RTSP stream)
    this.initializeVideoStream();
  }

  ngAfterViewInit(): void {
    this.startCanvasRendering();
  }

  private initializeVideoStream(): void {
    // TODO: Connect to actual RTSP/HLS stream
    // For now, using a mock stream or fallback to gray canvas
    const canvas = document.createElement('canvas');
    canvas.width = 1920;
    canvas.height = 1080;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
  }

  private startCanvasRendering(): void {
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const video = this.videoElement.nativeElement;
    const observer = new ResizeObserver(() => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    });

    if (canvas.parentElement) {
      observer.observe(canvas.parentElement);
    }

    // Animation loop for canvas
    const render = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw detection boxes
      this.detectionBoxes$.value.forEach(box => {
        this.drawDetectionBox(ctx, box, canvas);
      });

      // Draw zone overlays
      this.zoneOverlays$.value.forEach(zone => {
        this.drawZoneOverlay(ctx, zone, canvas);
      });

      requestAnimationFrame(render);
    };

    render();
  }

  private drawDetectionBox(ctx: CanvasRenderingContext2D, box: DetectionBox, canvas: HTMLCanvasElement): void {
    const scaleX = canvas.width / 1920;
    const scaleY = canvas.height / 1080;

    const x = box.x * scaleX;
    const y = box.y * scaleY;
    const width = box.width * scaleX;
    const height = box.height * scaleY;

    const colorMap: { [key: string]: string } = {
      cyan: '#06b6d4',
      emerald: '#10b981',
      rose: '#f43f5e',
      amber: '#f59e0b'
    };

    // Draw box
    ctx.strokeStyle = colorMap[box.color];
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x, y, width, height);

    // Draw label
    const labelText = `${box.label} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.fillStyle = colorMap[box.color];
    ctx.font = 'bold 11px monospace';
    ctx.fillText(labelText, x + 3, y - 3);

    // Draw corner dots
    const corners = [
      [x, y],
      [x + width, y],
      [x, y + height],
      [x + width, y + height]
    ];

    corners.forEach(([cx, cy]) => {
      ctx.fillStyle = colorMap[box.color];
      ctx.fillRect(cx - 2, cy - 2, 4, 4);
    });
  }

  private drawZoneOverlay(ctx: CanvasRenderingContext2D, zone: ZoneOverlay, canvas: HTMLCanvasElement): void {
    const scaleX = canvas.width / 1920;
    const scaleY = canvas.height / 1080;

    ctx.strokeStyle = zone.color;
    ctx.fillStyle = zone.color;
    ctx.globalAlpha = zone.alpha;
    ctx.lineWidth = 2;

    if (zone.type === 'line') {
      // Draw crossing line
      ctx.beginPath();
      zone.points.forEach((point, index) => {
        const x = point.x * scaleX;
        const y = point.y * scaleY;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Draw line direction arrows
      if (zone.points.length >= 2) {
        const p1 = zone.points[0];
        const p2 = zone.points[1];
        const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
        const arrowSize = 10;

        // Midpoint
        const mx = ((p1.x + p2.x) / 2) * scaleX;
        const my = ((p1.y + p2.y) / 2) * scaleY;

        // Arrow head
        ctx.beginPath();
        ctx.moveTo(mx, my);
        ctx.lineTo(mx - arrowSize * Math.cos(angle - Math.PI / 6), my - arrowSize * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(mx - arrowSize * Math.cos(angle + Math.PI / 6), my - arrowSize * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
      }
    } else if (zone.type === 'polygon' || zone.type === 'rectangle') {
      ctx.beginPath();
      zone.points.forEach((point, index) => {
        const x = point.x * scaleX;
        const y = point.y * scaleY;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.stroke();
      ctx.fill();
    }

    ctx.globalAlpha = 1.0;

    // Draw zone label
    if (zone.points.length > 0) {
      const firstPoint = zone.points[0];
      const labelX = firstPoint.x * scaleX + 5;
      const labelY = firstPoint.y * scaleY - 5;

      ctx.fillStyle = zone.color;
      ctx.font = 'bold 10px monospace';
      ctx.globalAlpha = 0.8;
      ctx.fillText(zone.name, labelX, labelY);
      ctx.globalAlpha = 1.0;
    }
  }

  addDetectionBox(box: DetectionBox): void {
    const boxes = this.detectionBoxes$.value;
    boxes.push(box);
    if (boxes.length > 50) boxes.shift();
    this.detectionBoxes$.next([...boxes]);
  }

  addZoneOverlay(zone: ZoneOverlay): void {
    this.zoneOverlays$.next([...this.zoneOverlays$.value, zone]);
  }
}

// ============================================================================
// VIDEO FEED DETAIL COMPONENT (for single camera view)
// ============================================================================

@Component({
  selector: 'app-video-feed-detail',
  template: `
    <div class="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden flex flex-col h-full">
      
      <!-- Video Container -->
      <div class="flex-1 relative bg-black flex items-center justify-center overflow-hidden">
        <video 
          #videoElement
          class="w-full h-full object-cover"
          autoplay
          muted
          playsinline>
        </video>

        <!-- Canvas Overlays -->
        <canvas 
          #detectionCanvas
          class="absolute inset-0 w-full h-full">
        </canvas>

        <!-- Status Bar -->
        <div class="absolute top-0 left-0 right-0 bg-gradient-to-b from-black to-transparent p-4 text-sm">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-3">
              <span class="text-cyan-400 font-bold">{{ camera?.name }}</span>
              <span class="text-emerald-400 font-bold flex items-center gap-1">
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                LIVE
              </span>
            </div>
            <div class="text-slate-400 font-mono">{{ fps }}fps · {{ resolution }}</div>
          </div>
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span>{{ camera?.location }}</span>
            <span>{{ currentTime }}</span>
          </div>
        </div>

        <!-- Camera Controls (bottom bar) -->
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4 text-xs text-slate-300">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" clip-rule="evenodd" /></svg>
                <span>Res: {{ camera?.view_area_sqm }}m²</span>
              </div>
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" /><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 100-2 4 4 0 00-4 4v10a4 4 0 004 4h12a4 4 0 004-4V5a4 4 0 00-4-4 1 1 0 100 2 2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2V5z" clip-rule="evenodd" /></svg>
                <span>Cap: {{ camera?.capacity }} people</span>
              </div>
            </div>

            <div class="flex gap-2">
              <button class="p-2 hover:bg-slate-700 rounded transition-colors text-slate-300 hover:text-white">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" /></svg>
              </button>
              <button class="p-2 hover:bg-slate-700 rounded transition-colors text-slate-300 hover:text-white">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4z" /><path fill-rule="evenodd" d="M3 10a1 1 0 011-1h6v2a2 2 0 11-4 0v-1a1 1 0 00-1-1H4a1 1 0 00-1 1v6a1 1 0 001 1h10a1 1 0 001-1v-6a1 1 0 00-1-1h-2v1a4 4 0 118-4v1a1 1 0 001 1H4z" clip-rule="evenodd" /></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Info Panel -->
      <div class="border-t border-slate-700 p-4 bg-slate-900 grid grid-cols-4 gap-4 text-sm">
        <div>
          <span class="text-slate-400">Current Count</span>
          <div class="text-2xl font-bold text-cyan-400">{{ liveData?.occupancy_count || 0 }}</div>
        </div>
        <div>
          <span class="text-slate-400">Entering</span>
          <div class="text-2xl font-bold text-emerald-400">{{ liveData?.entering_count || 0 }}</div>
        </div>
        <div>
          <span class="text-slate-400">Exiting</span>
          <div class="text-2xl font-bold text-rose-400">{{ liveData?.exiting_count || 0 }}</div>
        </div>
        <div>
          <span class="text-slate-400">Density</span>
          <div class="text-2xl font-bold text-amber-400">{{ liveData?.density_level || 'LOW' }}</div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }
  `]
})
export class VideoFeedDetailComponent implements OnInit, AfterViewInit {
  @Input() camera: any;
  @Input() liveData: any;
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('detectionCanvas') canvasElement!: ElementRef<HTMLCanvasElement>;

  fps = 30;
  resolution = '1920x1080';
  currentTime = new Date().toLocaleTimeString();

  detectionBoxes$ = new BehaviorSubject<DetectionBox[]>([]);
  zoneOverlays$ = new BehaviorSubject<ZoneOverlay[]>([]);

  ngOnInit(): void {
    // Update time display
    setInterval(() => {
      this.currentTime = new Date().toLocaleTimeString();
    }, 1000);
  }

  ngAfterViewInit(): void {
    this.startCanvasRendering();
  }

  private startCanvasRendering(): void {
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };

    resizeCanvas();
    const observer = new ResizeObserver(resizeCanvas);
    if (canvas.parentElement) {
      observer.observe(canvas.parentElement);
    }

    // Animation loop
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw detection boxes and zones
      this.detectionBoxes$.value.forEach(box => {
        this.drawBox(ctx, box, canvas);
      });

      this.zoneOverlays$.value.forEach(zone => {
        this.drawZone(ctx, zone, canvas);
      });

      requestAnimationFrame(render);
    };

    render();
  }

  private drawBox(ctx: CanvasRenderingContext2D, box: DetectionBox, canvas: HTMLCanvasElement): void {
    const scaleX = canvas.width / 1920;
    const scaleY = canvas.height / 1080;

    const x = box.x * scaleX;
    const y = box.y * scaleY;
    const width = box.width * scaleX;
    const height = box.height * scaleY;

    const colorMap: { [key: string]: string } = {
      cyan: '#06b6d4',
      emerald: '#10b981',
      rose: '#f43f5e',
      amber: '#f59e0b'
    };

    ctx.strokeStyle = colorMap[box.color];
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);

    ctx.fillStyle = colorMap[box.color];
    ctx.font = 'bold 12px monospace';
    const text = `${box.label} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.fillText(text, x + 5, y - 5);
  }

  private drawZone(ctx: CanvasRenderingContext2D, zone: ZoneOverlay, canvas: HTMLCanvasElement): void {
    const scaleX = canvas.width / 1920;
    const scaleY = canvas.height / 1080;

    ctx.strokeStyle = zone.color;
    ctx.fillStyle = zone.color;
    ctx.globalAlpha = zone.alpha;
    ctx.lineWidth = 2;

    ctx.beginPath();
    zone.points.forEach((p, i) => {
      const x = p.x * scaleX;
      const y = p.y * scaleY;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    if (zone.type !== 'line') ctx.closePath();
    ctx.stroke();
    if (zone.type !== 'line') ctx.fill();

    ctx.globalAlpha = 1.0;
  }
}
