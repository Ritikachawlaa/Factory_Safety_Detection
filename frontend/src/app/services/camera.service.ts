import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Camera {
  id?: number;
  name: string;
  location?: string;
  stream_url: string;
  camera_type: string;
  is_active: boolean;
  added_at?: string;
  updated_at?: string;
  notes?: string;
}

@Injectable({ providedIn: 'root' })
export class CameraService {
  private apiUrl = environment.apiUrl + '/cameras/';

  constructor(private http: HttpClient) {}

  getCameras(): Observable<Camera[]> {
    return this.http.get<any>(this.apiUrl).pipe(
      map((response: any) => Array.isArray(response) ? response : response.results || [])
    );
  }

  getCamera(id: number): Observable<Camera> {
    return this.http.get<Camera>(`${this.apiUrl}${id}/`);
  }

  addCamera(camera: Camera): Observable<Camera> {
    return this.http.post<Camera>(this.apiUrl, camera);
  }

  updateCamera(id: number, camera: Camera): Observable<Camera> {
    return this.http.put<Camera>(`${this.apiUrl}${id}/`, camera);
  }

  deleteCamera(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}${id}/`);
  }
}
