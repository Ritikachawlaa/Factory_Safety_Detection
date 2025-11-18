import { Component, OnInit } from '@angular/core';
import { Camera, CameraService } from '../../services/camera.service';

@Component({
  selector: 'app-camera-management',
  templateUrl: './camera-management.component.html',
  styleUrls: ['./camera-management.component.css']
})
export class CameraManagementComponent implements OnInit {
  cameras: Camera[] = [];
  showModal = false;
  editingCamera: Camera | null = null;
  cameraForm: Camera = this.getEmptyCamera();

  constructor(private cameraService: CameraService) {}

  ngOnInit() {
    this.loadCameras();
  }

  loadCameras() {
    this.cameraService.getCameras().subscribe(cameras => this.cameras = cameras);
  }

  openAddCamera() {
    this.editingCamera = null;
    this.cameraForm = this.getEmptyCamera();
    this.showModal = true;
  }

  editCamera(camera: Camera) {
    this.editingCamera = camera;
    this.cameraForm = { ...camera };
    this.showModal = true;
  }

  saveCamera() {
    if (this.editingCamera && this.editingCamera.id) {
      this.cameraService.updateCamera(this.editingCamera.id, this.cameraForm).subscribe(() => {
        this.loadCameras();
        this.closeModal();
      });
    } else {
      this.cameraService.addCamera(this.cameraForm).subscribe(() => {
        this.loadCameras();
        this.closeModal();
      });
    }
  }

  deleteCamera(id?: number) {
    if (!id) return;
    if (confirm('Delete this camera?')) {
      this.cameraService.deleteCamera(id).subscribe(() => this.loadCameras());
    }
  }

  closeModal() {
    this.showModal = false;
  }

  getEmptyCamera(): Camera {
    return {
      name: '',
      location: '',
      stream_url: '',
      camera_type: 'rtsp',
      is_active: true,
      notes: ''
    };
  }
}
