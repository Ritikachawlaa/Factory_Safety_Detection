import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/**
 * Shared Webcam Service
 * Manages a single persistent webcam stream across the entire application
 * Prevents multiple webcam initializations on navigation
 */
@Injectable({
  providedIn: 'root'
})
export class SharedWebcamService {
  // Webcam stream state
  private streamSubject = new BehaviorSubject<MediaStream | null>(null);
  public stream$: Observable<MediaStream | null> = this.streamSubject.asObservable();

  // Webcam status
  private activeSubject = new BehaviorSubject<boolean>(false);
  public active$: Observable<boolean> = this.activeSubject.asObservable();

  // Video element reference (shared)
  private videoElement: HTMLVideoElement | null = null;

  // Error state
  private errorSubject = new BehaviorSubject<string | null>(null);
  public error$: Observable<string | null> = this.errorSubject.asObservable();

  constructor() {}

  /**
   * Initialize webcam stream (call once)
   * @returns Promise resolving to MediaStream
   */
  async initializeWebcam(): Promise<MediaStream> {
    // If already initialized, return existing stream
    if (this.streamSubject.value) {
      return this.streamSubject.value;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: false
      });

      this.streamSubject.next(stream);
      this.activeSubject.next(true);
      this.errorSubject.next(null);

      console.log('✅ Shared webcam initialized');
      return stream;

    } catch (error: any) {
      const errorMsg = error?.message || 'Could not access webcam';
      this.errorSubject.next(errorMsg);
      this.activeSubject.next(false);
      
      console.error('❌ Webcam initialization failed:', error);
      throw error;
    }
  }

  /**
   * Attach video element to stream
   * @param videoEl HTMLVideoElement to attach stream to
   */
  attachVideoElement(videoEl: HTMLVideoElement): void {
    const stream = this.streamSubject.value;
    if (!stream) {
      console.warn('⚠️ No stream available to attach');
      return;
    }

    videoEl.srcObject = stream;
    videoEl.play().catch(err => {
      console.error('Video play failed:', err);
    });

    this.videoElement = videoEl;
  }

  /**
   * Get current stream
   */
  getStream(): MediaStream | null {
    return this.streamSubject.value;
  }

  /**
   * Check if webcam is active
   */
  isActive(): boolean {
    return this.activeSubject.value;
  }

  /**
   * Get video element reference
   */
  getVideoElement(): HTMLVideoElement | null {
    return this.videoElement;
  }

  /**
   * Stop webcam (cleanup on app destroy)
   */
  stopWebcam(): void {
    const stream = this.streamSubject.value;
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      this.streamSubject.next(null);
      this.activeSubject.next(false);
      this.videoElement = null;
      
      console.log('🛑 Shared webcam stopped');
    }
  }

  /**
   * Capture frame from current stream
   * @returns Base64 encoded image (without data URL prefix)
   */
  captureFrame(): string | null {
    if (!this.videoElement) {
      console.warn('⚠️ No video element attached');
      return null;
    }

    const canvas = document.createElement('canvas');
    canvas.width = this.videoElement.videoWidth || 640;
    canvas.height = this.videoElement.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);
    
    // Return only the base64 string without the data URL prefix
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    return dataUrl.split(',')[1] || '';
  }
}
