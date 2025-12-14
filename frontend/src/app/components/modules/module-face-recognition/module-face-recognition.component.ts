import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry { timestamp: Date; value: any; label: string; }

@Component({
  selector: 'app-module-face-recognition',
  templateUrl: './module-face-recognition.component.html',
  styleUrls: ['./module-face-recognition.component.css']
})
export class ModuleFaceRecognitionComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  cameraActive = false;
  isRegisteringEmployee = false;
  registrationMessage = '';
  registrationStatus: 'idle' | 'registering' | 'success' | 'error' = 'idle';
  enabledFeatures: EnabledFeatures = {
    human: false, vehicle: false, helmet: false, loitering: false, crowd: false,
    box_count: false, line_crossing: false, tracking: false, motion: false,
    face_detection: false, face_recognition: true
  };
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;

  constructor(public webcamService: SharedWebcamService, private detectionService: UnifiedDetectionService) {}

  ngOnInit(): void {
    // Don't auto-start - wait for user to click Start Camera
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
      }
    }).catch(err => {
      console.error('Failed to start camera:', err);
    });
  }

  stopCamera(): void {
    this.stopDetection();
    this.webcamService.stopWebcam();
    this.cameraActive = false;
  }
  startDetection(): void {
    this.isDetecting = true;
    this.detectionSubscription = interval(500).subscribe(() => this.processFrame());
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
      },
      error: (error: any) => console.error('Detection error:', error)
    });
  }
  private updateHistory(result: DetectionResult): void {
    const recognized = result.faces_recognized || [];
    const unknown = result.unknown_faces || 0;
    const label = `${recognized.length} faces recognized, ${unknown} unknown`;
    this.history.unshift({ timestamp: new Date(), value: recognized.length, label });
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }

  registerEmployee(): void {
    const employeeName = prompt('Enter employee name:');
    if (!employeeName || employeeName.trim() === '') {
      this.registrationMessage = 'Registration cancelled';
      this.registrationStatus = 'error';
      setTimeout(() => this.resetRegistrationStatus(), 3000);
      return;
    }

    this.registrationStatus = 'registering';
    this.registrationMessage = 'Processing...';
    this.isRegisteringEmployee = true;

    const frameData = this.webcamService.captureFrame();
    if (!frameData) {
      this.registrationMessage = 'Failed to capture frame. Start camera first.';
      this.registrationStatus = 'error';
      this.isRegisteringEmployee = false;
      setTimeout(() => this.resetRegistrationStatus(), 3000);
      return;
    }

    this.detectionService.registerEmployee(frameData, employeeName.trim()).subscribe({
      next: (response: any) => {
        this.isRegisteringEmployee = false;
        if (response.status === 'success') {
          this.registrationMessage = `✓ ${employeeName} registered successfully!`;
          this.registrationStatus = 'success';
        } else if (response.status === 'partial') {
          this.registrationMessage = response.message || 'Employee registered but face detection incomplete.';
          this.registrationStatus = 'error';
        } else {
          this.registrationMessage = response.message || 'Registration failed.';
          this.registrationStatus = 'error';
        }
        setTimeout(() => this.resetRegistrationStatus(), 3000);
      },
      error: (error: any) => {
        this.isRegisteringEmployee = false;
        this.registrationMessage = error?.error?.message || 'Registration failed. Please try again.';
        this.registrationStatus = 'error';
        console.error('Registration error:', error);
        setTimeout(() => this.resetRegistrationStatus(), 3000);
      }
    });
  }

  private resetRegistrationStatus(): void {
    this.registrationStatus = 'idle';
    this.registrationMessage = '';
  }

  get recentHistory(): HistoryEntry[] { return this.history.slice(0, 10); }
  formatTime(date: Date): string { return date.toLocaleTimeString(); }
}

