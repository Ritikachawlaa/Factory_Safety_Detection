import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface Camera {
  id: string;
  name: string;
  rtspUrl: string;
  assignedModule: 'helmet' | 'loitering' | 'production' | 'attendance' | 'none';
  status: 'active' | 'inactive' | 'error';
  lastSeen?: string;
  errorMessage?: string;
}

export interface CameraFormData {
  name: string;
  rtspUrl: string;
  assignedModule: 'helmet' | 'loitering' | 'production' | 'attendance' | 'none';
}

// ============================================================================
// CAMERA CONFIGURATION SERVICE
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class CameraConfigService {
  private readonly apiUrl = `${environment.apiUrl}/cameras`;

  // Signal-based camera list
  cameras = signal<Camera[]>([]);
  selectedCamera = signal<Camera | null>(null);
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);

  constructor(private http: HttpClient) {
    // Auto-load cameras on service initialization
    this.loadCameras();
  }

  // ============================================================================
  // CRUD OPERATIONS
  // ============================================================================

  /**
   * Load all cameras from backend
   */
  loadCameras(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.http.get<Camera[]>(this.apiUrl).subscribe({
      next: (cameras) => {
        this.cameras.set(cameras);
        this.isLoading.set(false);
        console.log('📷 Loaded cameras:', cameras.length);
      },
      error: (err) => {
        this.error.set('Failed to load cameras');
        this.isLoading.set(false);
        console.error('🔥 Camera load error:', err);
      }
    });
  }

  /**
   * Get single camera by ID
   */
  getCameraById(id: string): Observable<Camera> {
    return this.http.get<Camera>(`${this.apiUrl}/${id}`);
  }

  /**
   * Add new camera
   */
  addCamera(cameraData: CameraFormData): Observable<Camera> {
    return this.http.post<Camera>(this.apiUrl, cameraData).pipe(
      tap((newCamera) => {
        this.cameras.update(cameras => [...cameras, newCamera]);
        console.log('✅ Camera added:', newCamera.name);
      })
    );
  }

  /**
   * Update existing camera
   */
  updateCamera(id: string, cameraData: Partial<CameraFormData>): Observable<Camera> {
    return this.http.put<Camera>(`${this.apiUrl}/${id}`, cameraData).pipe(
      tap((updatedCamera) => {
        this.cameras.update(cameras => 
          cameras.map(c => c.id === id ? updatedCamera : c)
        );
        console.log('✏️ Camera updated:', updatedCamera.name);
      })
    );
  }

  /**
   * Delete camera
   */
  deleteCamera(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`).pipe(
      tap(() => {
        this.cameras.update(cameras => cameras.filter(c => c.id !== id));
        console.log('🗑️ Camera deleted:', id);
      })
    );
  }

  // ============================================================================
  // CAMERA STATUS MANAGEMENT
  // ============================================================================

  /**
   * Update camera status (called by backend)
   */
  updateCameraStatus(id: string, status: Camera['status'], errorMessage?: string): void {
    this.cameras.update(cameras =>
      cameras.map(c => 
        c.id === id 
          ? { ...c, status, errorMessage, lastSeen: new Date().toISOString() }
          : c
      )
    );
  }

  /**
   * Test camera connection
   */
  testCamera(id: string): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(
      `${this.apiUrl}/${id}/test`,
      {}
    );
  }

  // ============================================================================
  // CAMERA ASSIGNMENT HELPERS
  // ============================================================================

  /**
   * Get cameras assigned to a specific module
   */
  getCamerasForModule(module: Camera['assignedModule']): Camera[] {
    return this.cameras().filter(c => c.assignedModule === module);
  }

  /**
   * Check if a module has an assigned camera
   */
  hasAssignedCamera(module: Camera['assignedModule']): boolean {
    return this.cameras().some(c => c.assignedModule === module);
  }

  /**
   * Get unassigned cameras
   */
  getUnassignedCameras(): Camera[] {
    return this.cameras().filter(c => c.assignedModule === 'none');
  }

  // ============================================================================
  // VALIDATION
  // ============================================================================

  /**
   * Validate RTSP URL format
   */
  validateRtspUrl(url: string): { valid: boolean; error?: string } {
    const rtspPattern = /^rtsp:\/\/.+/i;
    
    if (!url) {
      return { valid: false, error: 'RTSP URL is required' };
    }
    
    if (!rtspPattern.test(url)) {
      return { valid: false, error: 'Invalid RTSP URL format. Should start with rtsp://' };
    }
    
    return { valid: true };
  }

  /**
   * Check if camera name is unique
   */
  isCameraNameUnique(name: string, excludeId?: string): boolean {
    return !this.cameras().some(c => 
      c.name.toLowerCase() === name.toLowerCase() && c.id !== excludeId
    );
  }

  // ============================================================================
  // SELECTION MANAGEMENT
  // ============================================================================

  /**
   * Select a camera for editing
   */
  selectCamera(camera: Camera): void {
    this.selectedCamera.set(camera);
  }

  /**
   * Clear camera selection
   */
  clearSelection(): void {
    this.selectedCamera.set(null);
  }
}
