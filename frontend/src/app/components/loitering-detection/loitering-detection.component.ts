import { Component, OnInit, OnDestroy, ViewChild, ElementRef, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';
import { LoiteringService, LoiteringStatus } from '../../services/loitering.service';
import { ViolationService, LoiteringViolation } from '../../services/violation.service';
import { FrameLimiter, RECOMMENDED_FPS } from '../../utils/frame-limiter';

@Component({
  selector: 'app-loitering-detection',
  templateUrl: './loitering-detection.component.html',
  styleUrls: ['./loitering-detection.component.css']
})
export class LoiteringDetectionComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  // Injected services
  private violationService = inject(ViolationService);

  // Signals for violation management
  violations = this.violationService.loiteringViolations;
  showResolveModal = signal(false);
  selectedViolation = signal<LoiteringViolation | null>(null);
  resolutionNotes = signal('');
  resolvedBy = signal('');

  // Computed signals
  activeViolations = computed(() => 
    this.violations().filter(v => v.status === 'active')
  );

  loiteringData: LoiteringStatus = { activeGroups: 0 };
  lastDetection: any = null;
  isWebcamActive = false;
  isDetecting = false;
  private subscription?: Subscription;
  private stream?: MediaStream;
  private frameLimiter = new FrameLimiter(RECOMMENDED_FPS.LOITERING); // 4 FPS
  private detectionInterval?: number;

  constructor(private loiteringService: LoiteringService) {}

  ngOnInit(): void {
    // Load today's violations
    this.loadViolations();
    
    this.subscription = this.loiteringService.getLoiteringStats().subscribe(
      (data: any) => this.loiteringData = data,
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
      this.isDetecting = false;
      this.frameLimiter.reset();
      
      // Clear detection interval
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval);
        this.detectionInterval = undefined;
      }
    }
  }

  detectLoitering(): void {
    if (!this.isWebcamActive || this.isDetecting) return;

    // Start continuous detection with frame rate limiting
    this.isDetecting = true;
    this.frameLimiter.reset();
    
    // Process frames at recommended FPS (4 FPS for loitering)
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
    this.loiteringService.detectFromFrame(frameData).subscribe({
      next: (result: any) => {
        console.log('Loitering detection result:', result);
        this.lastDetection = {
          activeGroups: result.active_groups || 0,
          timestamp: result.timestamp || new Date()
        };
        this.loiteringData.activeGroups = this.lastDetection.activeGroups;
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

  // ============================================================================
  // VIOLATION MANAGEMENT METHODS
  // ============================================================================

  /**
   * Load today's loitering violations
   */
  loadViolations(): void {
    const today = new Date().toISOString().split('T')[0];
    this.violationService.loadLoiteringViolations(today);
  }

  /**
   * Format date-time for display
   */
  formatDateTime(timestamp: string): string {
    return new Date(timestamp).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  /**
   * Open resolve modal for a violation
   */
  openResolveModal(violation: LoiteringViolation): void {
    this.selectedViolation.set(violation);
    this.resolutionNotes.set('');
    this.resolvedBy.set('');
    this.showResolveModal.set(true);
  }

  /**
   * Close resolve modal
   */
  closeResolveModal(): void {
    this.showResolveModal.set(false);
    this.selectedViolation.set(null);
    this.resolutionNotes.set('');
    this.resolvedBy.set('');
  }

  /**
   * Resolve the selected violation
   */
  resolveViolation(): void {
    const violation = this.selectedViolation();
    const notes = this.resolutionNotes();
    const by = this.resolvedBy();
    
    if (!violation || !notes || !by) return;
    
    this.violationService.resolveLoiteringViolation(violation.id, notes, by).subscribe({
      next: () => {
        alert('✅ Violation resolved successfully!');
        this.closeResolveModal();
      },
      error: (err) => {
        alert('❌ Failed to resolve violation: ' + err.message);
      }
    });
  }
}
