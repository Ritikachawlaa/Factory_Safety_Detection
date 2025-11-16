import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface ProductionCount {
  id?: number;
  timestamp?: string;
  itemCount: number;
  sessionDate?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductionService {
  private apiUrl = `${environment.apiUrl}/live/production/`;
  private resetUrl = `${environment.apiUrl}/live/production/reset/`;
  private statsUrl = `${environment.apiUrl}/stats/production/`;

  constructor(private http: HttpClient) {}

  // Send webcam frame for live detection
  detectFromFrame(frameData: string): Observable<ProductionCount> {
    return this.http.post<ProductionCount>(this.apiUrl, { frame: frameData });
  }

  // Reset production counter
  resetCounter(): Observable<any> {
    return this.http.post<any>(this.resetUrl, {});
  }

  // Get statistics
  getProductionStats(): Observable<any> {
    return this.http.get<any>(this.statsUrl);
  }

  // Get historical records
  getProductionRecords(limit: number = 10): Observable<ProductionCount[]> {
    return this.http.get<ProductionCount[]>(`${environment.apiUrl}/production-counter/?limit=${limit}`);
  }

  // Get today's count
  getTodayCount(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/production-counter/today/`);
  }
}
