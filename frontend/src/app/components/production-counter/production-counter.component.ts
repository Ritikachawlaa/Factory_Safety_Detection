import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { ProductionService, ProductionCount } from '../../services/production.service';
import { CameraService, Camera } from '../../services/camera.service';

@Component({
  selector: 'app-production-counter',
  templateUrl: './production-counter.component.html',
  styleUrls: ['./production-counter.component.css']
})
export class ProductionCounterComponent implements OnInit, OnDestroy {
  productionData: ProductionCount = { itemCount: 0 };
  lastDetection: any = null;
  sessionTotal = 0;
  cameras: Camera[] = [];
  selectedCameraId: number | null = null;
  isCounting = false;
  private subscription?: Subscription;
  private cameraSub?: Subscription;

  constructor(private productionService: ProductionService, private cameraService: CameraService) {}

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
    // Fetch available cameras
    this.cameraSub = this.cameraService.getCameras().subscribe(
      (cameras) => this.cameras = cameras.filter(c => c.is_active),
      (error) => console.error('Failed to load cameras', error)
    );
  }

  countProduction(): void {
    if (!this.selectedCameraId || this.isCounting) return;
    this.isCounting = true;
    this.productionService.detectFromCamera(this.selectedCameraId).subscribe({
      next: (result: any) => {
        const itemCount = result.item_count || 0;
        if (itemCount > 0) {
          this.lastDetection = {
            itemCount: itemCount,
            timestamp: result.timestamp || new Date()
          };
          this.sessionTotal += itemCount;
          this.productionData.itemCount = this.sessionTotal;
        }
        this.isCounting = false;
      },
      error: (error: any) => {
        console.error('Counting error:', error);
        this.isCounting = false;
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
    this.cameraSub?.unsubscribe();
  }
}
