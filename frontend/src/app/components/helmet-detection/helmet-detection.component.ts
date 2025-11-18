import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { HelmetService, HelmetStatus } from '../../services/helmet.service';
import { CameraService, Camera } from '../../services/camera.service';

@Component({
  selector: 'app-helmet-detection',
  templateUrl: './helmet-detection.component.html',
  styleUrls: ['./helmet-detection.component.css']
})
export class HelmetDetectionComponent implements OnInit, OnDestroy {
  helmetData: HelmetStatus = { totalPeople: 0, compliantCount: 0, violationCount: 0 };
  lastDetection: any = null;
  cameras: Camera[] = [];
  selectedCameraId: number | null = null;
  isDetecting = false;
  private subscription?: Subscription;
  private cameraSub?: Subscription;

  constructor(private helmetService: HelmetService, private cameraService: CameraService) {}

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
    // Fetch available cameras
    this.cameraSub = this.cameraService.getCameras().subscribe(
      (cameras) => this.cameras = cameras.filter(c => c.is_active),
      (error) => console.error('Failed to load cameras', error)
    );
  }

  detectHelmet(): void {
    if (!this.selectedCameraId || this.isDetecting) return;
    this.isDetecting = true;
    this.helmetService.detectFromCamera(this.selectedCameraId).subscribe({
      next: (result: any) => {
        this.lastDetection = {
          totalPeople: result.totalPeople || result.total_people || 0,
          compliantCount: result.compliantCount || result.compliant_count || 0,
          violationCount: result.violationCount || result.violation_count || 0
        };
        this.helmetData = this.lastDetection;
        this.isDetecting = false;
      },
      error: (error: any) => {
        console.error('Detection error:', error);
        this.isDetecting = false;
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.cameraSub?.unsubscribe();
  }

  get complianceRate(): number {
    if (this.helmetData.totalPeople === 0) return 100;
    return Math.round((this.helmetData.compliantCount / this.helmetData.totalPeople) * 100);
  }
}
