import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { ProductionService, ProductionCount } from '../../services/production.service';
import { FrameLimiter, RECOMMENDED_FPS } from '../../utils/frame-limiter';

@Component({
  selector: 'app-production-counter',
  templateUrl: './production-counter.component.html',
  styleUrls: ['./production-counter.component.css']
})
export class ProductionCounterComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  productionData: ProductionCount = { itemCount: 0 };
  lastDetection: any = null;
  sessionTotal = 0;
  isWebcamActive = false;
  isCounting = false;
  private subscription?: Subscription;
  private stream?: MediaStream;
  private frameLimiter = new FrameLimiter(RECOMMENDED_FPS.PRODUCTION); // 12 FPS
  private detectionInterval?: number;

  constructor(private productionService: ProductionService) {}

  ngOnInit(): void {
    this.subscription = this.productionService.getProductionStats().subscribe(
      (data: any) => {
        this.productionData = data;
        if (data.total_count !== undefined) {
          this.sessionTotal = data.total_count;
        }
      },
      (error: any) => console.error('Error:', error)
    );
  }

  async toggleWebcam(): Promise<void> {
    if (this.isWebcamActive) {
      this.stopWebcam();
    } else {
      await this.startWebcam();
    }
  }

  async startWebcam(): Promise<void> {
    try {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
      }
      
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } 
      });
      this.videoElement.nativeElement.srcObject = this.stream;
      this.isWebcamActive = true;
    } catch (error: any) {
      console.error('Error accessing webcam:', error);
      let errorMsg = 'Failed to access webcam.';
      if (error.name === 'NotReadableError') {
        errorMsg = 'Camera is being used by another application. Please close other apps using the camera and try again.';
      } else if (error.name === 'NotAllowedError') {
        errorMsg = 'Camera permission denied. Please allow camera access.';
      }
      alert(errorMsg);
      this.isWebcamActive = false;
    }
  }

  stopWebcam(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.videoElement.nativeElement.srcObject = null;
      this.isWebcamActive = false;
      this.isCounting = false;
      this.frameLimiter.reset();
      
      // Clear detection interval
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval);
        this.detectionInterval = undefined;
      }
    }
  }

  countProduction(): void {
    if (!this.isWebcamActive || this.isCounting) return;

    // Start continuous detection with frame rate limiting
    this.isCounting = true;
    this.frameLimiter.reset();
    
    // Process frames at recommended FPS (12 FPS for production)
    this.detectionInterval = window.setInterval(() => {
      if (!this.isWebcamActive || !this.isCounting) {
        if (this.detectionInterval) {
          clearInterval(this.detectionInterval);
          this.detectionInterval = undefined;
        }
        return;
      }
      
      // Only process if frame limiter allows
      if (this.frameLimiter.shouldProcessFrame()) {
        this.processFrame();
      }
    }, 100); // Check every 100ms, but actual processing limited by FrameLimiter
  }

  private processFrame(): void {
    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const context = canvas.getContext('2d');

    if (!context || !video.videoWidth) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    context.drawImage(video, 0, 0);

    // Convert canvas to base64 (compressed JPEG for better performance)
    const frameData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

    // Send to backend for detection
    this.productionService.detectFromFrame(frameData).subscribe({
      next: (result: any) => {
        console.log('Production counting result:', result);
        const itemCount = result.item_count || 0;
        
        if (itemCount > 0) {
          this.lastDetection = {
            itemCount: itemCount,
            timestamp: result.timestamp || new Date()
          };
          this.sessionTotal += itemCount;
          this.productionData.itemCount = this.sessionTotal;
        }
      },
      error: (error: any) => {
        console.error('Counting error:', error);
      }
    });
  }

  resetCounter(): void {
    this.productionService.resetCounter().subscribe({
      next: (response) => {
        this.sessionTotal = 0;
        this.productionData.itemCount = 0;
        this.lastDetection = null;
        alert('Counter reset successfully!');
      },
      error: (error) => {
        console.error('Reset error:', error);
        // Reset locally even if API fails
        this.sessionTotal = 0;
        this.productionData.itemCount = 0;
        this.lastDetection = null;
        alert('Counter reset locally (backend may be unavailable)');
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.stopWebcam();
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
    }
  }
}
