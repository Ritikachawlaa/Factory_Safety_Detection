import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface AttendanceStatus {
  verifiedCount: number;
  lastPersonSeen: string;
  attendanceLog?: any[];
}

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {
  private apiUrl = `${environment.apiUrl}/live/attendance/`;
  private statsUrl = `${environment.apiUrl}/stats/attendance/`;

  constructor(private http: HttpClient) {}

  // Send webcam frame for live detection
  detectFromFrame(frameData: string): Observable<AttendanceStatus> {
    return this.http.post<AttendanceStatus>(this.apiUrl, { frame: frameData });
  }

  // Get statistics
  getAttendanceStats(): Observable<any> {
    return this.http.get<any>(this.statsUrl);
  }

  // Get today's attendance
  getTodayAttendance(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/attendance/today/`);
  }

  // Get all attendance records
  getAttendanceRecords(limit: number = 10): Observable<any[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/attendance/?limit=${limit}`);
  }
}
