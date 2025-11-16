import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval } from 'rxjs';
import { switchMap, startWith, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface HelmetStatus {
  id?: number;
  timestamp?: string;
  totalPeople: number;
  compliantCount: number;
  violationCount: number;
  complianceRate?: number;
}

@Injectable({
  providedIn: 'root'
})
export class HelmetService {
  private apiUrl = `${environment.apiUrl}/live/helmet/`;
  private statsUrl = `${environment.apiUrl}/stats/helmet/`;

  constructor(private http: HttpClient) {}

  // Send webcam frame for live detection
  detectFromFrame(frameData: string): Observable<HelmetStatus> {
    return this.http.post<HelmetStatus>(this.apiUrl, { frame: frameData });
  }

  // Get statistics
  getHelmetStats(): Observable<any> {
    return this.http.get<any>(this.statsUrl);
  }

  // Get historical records
  getHelmetRecords(limit: number = 10): Observable<HelmetStatus[]> {
    return this.http.get<HelmetStatus[]>(`${environment.apiUrl}/helmet-detection/?limit=${limit}`);
  }
}
