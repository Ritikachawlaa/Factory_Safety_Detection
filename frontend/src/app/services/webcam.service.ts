import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class WebcamService {
  private stream: MediaStream | null = null;

// WebcamService removed. All webcam logic is now obsolete. Use CameraService and CCTV streams only.
}
