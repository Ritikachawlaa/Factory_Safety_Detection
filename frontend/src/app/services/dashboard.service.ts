import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

export interface DashboardSummary {
  date: string;
  helmet_violations: number;
  loitering_alerts: number;
  production_count: number;
  attendance: {
    total_employees: number;
    present: number;
    attendance_rate: number;
  };
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private summaryUrl = `${environment.apiUrl}/dashboard/summary/`;
  private helmetUrl = `${environment.apiUrl}/stats/helmet/`;
  private loiteringUrl = `${environment.apiUrl}/stats/loitering/`;
  private productionUrl = `${environment.apiUrl}/stats/production/`;
  private attendanceUrl = `${environment.apiUrl}/stats/attendance/`;

  constructor(private http: HttpClient) {}

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(this.summaryUrl);
  }

  getHelmetStats(): Observable<any> {
    return this.http.get<any>(this.helmetUrl);
  }

  getLoiteringStats(): Observable<any> {
    return this.http.get<any>(this.loiteringUrl);
  }

  getProductionStats(): Observable<any> {
    return this.http.get<any>(this.productionUrl);
  }

  getAttendanceStats(): Observable<any> {
    return this.http.get<any>(this.attendanceUrl);
  }
}
