import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface EnabledFeatures {
  human: boolean;
  vehicle: boolean;
  helmet: boolean;
  loitering: boolean;
  crowd: boolean;
  box_count: boolean;
  line_crossing: boolean;
  tracking: boolean;
  motion: boolean;
  face_detection: boolean;
  face_recognition: boolean;
}

export interface DetectionResult {
  frame_width: number;
  frame_height: number;
  timestamp: string;
  
  people_count: number;
  vehicle_count: number;
  helmet_violations: number;
  helmet_compliant: number;
  ppe_compliance_rate: number;
  
  loitering_detected: boolean;
  loitering_count: number;
  people_groups: number;
  
  labour_count: number;
  
  crowd_detected: boolean;
  crowd_density: string;
  occupied_area: number;
  
  box_count: number;
  line_crossed: boolean;
  total_crossings: number;
  
  tracked_objects: number;
  
  motion_detected: boolean;
  motion_intensity: number;
  motion_ai_validated: boolean;
  ai_validated: boolean;
  
  faces_detected: number;
  faces_recognized: string[];
  unknown_faces: number;
  registered_faces_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class UnifiedDetectionService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  /**
   * Send frame for unified detection
   */
  detect(frameData: string, enabledFeatures: EnabledFeatures, lineX?: number): Observable<DetectionResult> {
    const payload: any = {
      frame: frameData,
      enabled_features: enabledFeatures
    };
    
    if (lineX !== undefined) {
      payload.line_x = lineX;
    }
    
    return this.http.post<DetectionResult>(`${this.apiUrl}/detect`, payload);
  }

  /**
   * Reset all counters
   */
  resetCounters(): Observable<any> {
    return this.http.post(`${this.apiUrl}/reset`, {});
  }

  /**
   * Get system statistics
   */
  getStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }

  /**
   * Get available features
   */
  getFeatures(): Observable<any> {
    return this.http.get('http://localhost:8000/features');
  }

  /**
   * Health check
   */
  healthCheck(): Observable<any> {
    return this.http.get('http://localhost:8000/health');
  }

  /**
   * Register a new employee with face image
   */
  registerEmployee(frameData: string, employeeName: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/employees/register`, {
      image: frameData,
      name: employeeName
    });
  }}