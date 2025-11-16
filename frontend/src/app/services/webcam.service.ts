import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class WebcamService {
  private stream: MediaStream | null = null;

  async startWebcam(): Promise<MediaStream> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });
      return this.stream;
    } catch (error) {
      console.error('Error accessing webcam:', error);
      throw error;
    }
  }

  stopWebcam(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
  }

  captureFrame(videoElement: HTMLVideoElement): string {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    
    if (ctx) {
      ctx.drawImage(videoElement, 0, 0);
      return canvas.toDataURL('image/jpeg', 0.8);
    }
    
    return '';
  }

  isActive(): boolean {
    return this.stream !== null && this.stream.active;
  }
}
