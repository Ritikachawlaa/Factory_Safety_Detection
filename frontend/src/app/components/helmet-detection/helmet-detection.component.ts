import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { HelmetService, HelmetStatus } from '../../services/helmet.service';
import { FrameLimiter, RECOMMENDED_FPS } from '../../utils/frame-limiter';

@Component({
  selector: 'app-helmet-detection',
  templateUrl: './helmet-detection.component.html',
  styleUrls: ['./helmet-detection.component.css']
})
export class HelmetDetectionComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  helmetData: HelmetStatus = { totalPeople: 0, compliantCount: 0, violationCount: 0 };
  lastDetection: any = null;
  isWebcamActive = false;
  isDetecting = false;
  private subscription?: Subscription;
  private stream?: MediaStream;
  private frameLimiter = new FrameLimiter(RECOMMENDED_FPS.HELMET); // 8 FPS
  private detectionInterval?: number;

  constructor(private helmetService: HelmetService) {}

  ngOnInit(): void {
    // Fetch helmet detection statistics
    this.subscription = this.helmetService.getHelmetStats().subscribe(
      (data: any) => {
        if (data.latest_detection) {
          this.helmetData = data.latest_detection;
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
      // Stop any existing streams first
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
        errorMsg = 'Camera is being used by another application. Please close other apps using the camera.';
      } else if (error.name === 'NotAllowedError') {
        errorMsg = 'Camera permission denied. Please allow camera access in browser settings.';
      } else if (error.name === 'NotFoundError') {
        errorMsg = 'No camera found on this device.';
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
      this.isDetecting = false;
      this.frameLimiter.reset();
      
      // Clear detection interval
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval);
        this.detectionInterval = undefined;
      }
    }
  }

  detectHelmet(): void {
    if (!this.isWebcamActive || this.isDetecting) return;

    // Start continuous detection with frame rate limiting
    this.isDetecting = true;
    this.frameLimiter.reset();
    
    // Process frames at recommended FPS (8 FPS)
    this.detectionInterval = window.setInterval(() => {
      if (!this.isWebcamActive || !this.isDetecting) {
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
    this.helmetService.detectFromFrame(frameData).subscribe({
      next: (result: any) => {
        console.log('Detection result:', result);
        this.lastDetection = {
          totalPeople: result.totalPeople || result.total_people || 0,
          compliantCount: result.compliantCount || result.compliant_count || 0,
          violationCount: result.violationCount || result.violation_count || 0
        };
        this.helmetData = this.lastDetection;
      },
      error: (error: any) => {
        console.error('Detection error:', error);
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

  get complianceRate(): number {
    if (this.helmetData.totalPeople === 0) return 100;
    return Math.round((this.helmetData.compliantCount / this.helmetData.totalPeople) * 100);
  }
}
