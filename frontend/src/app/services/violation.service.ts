import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface LoiteringViolation {
  id: string;
  timestamp: string;
  location: string;
  cameraId: string;
  employeeId: string;
  employeeName: string;
  duration: number; // seconds
  groupSize: number;
  snapshotUrl: string;
  status: 'active' | 'resolved' | 'ignored';
  resolvedAt?: string;
  resolvedBy?: string;
  notes?: string;
}

export interface HelmetViolation {
  id: string;
  timestamp: string;
  location: string;
  cameraId: string;
  employeeId: string;
  employeeName: string;
  snapshotUrl: string;
  confidence: number;
  status: 'active' | 'resolved' | 'ignored';
  resolvedAt?: string;
  resolvedBy?: string;
  notes?: string;
}

export interface ProductionRecord {
  id: string;
  timestamp: string;
  shiftId: string;
  itemType: string;
  itemCount: number;
  cameraId: string;
  efficiency: number; // percentage
}

export interface AttendanceRecord {
  id: string;
  employeeId: string;
  employeeName: string;
  timestamp: string;
  type: 'check-in' | 'check-out';
  photoUrl: string;
  confidence: number;
  status: 'verified' | 'unknown';
}

@Injectable({
  providedIn: 'root'
})
export class ViolationService {
  private readonly API_URL = 'http://localhost:8000/api';
  
  // Loitering violations
  loiteringViolations = signal<LoiteringViolation[]>([]);
  activeLoiteringCount = signal(0);
  
  // Helmet violations
  helmetViolations = signal<HelmetViolation[]>([]);
  activeHelmetCount = signal(0);
  
  // Production records
  productionRecords = signal<ProductionRecord[]>([]);
  todayProduction = signal(0);
  
  // Attendance records
  attendanceRecords = signal<AttendanceRecord[]>([]);
  unknownPersons = signal<AttendanceRecord[]>([]);
  
  isLoading = signal(false);
  error = signal<string | null>(null);

  constructor(private http: HttpClient) {
    this.loadAllData();
  }

  /**
   * Load all violation and attendance data
   */
  loadAllData(): void {
    this.loadLoiteringViolations();
    this.loadHelmetViolations();
    this.loadProductionRecords();
    this.loadAttendanceRecords();
  }

  // ============================================================================
  // LOITERING VIOLATIONS
  // ============================================================================

  loadLoiteringViolations(date?: string): void {
    const url = date 
      ? `${this.API_URL}/violations/loitering/?date=${date}`
      : `${this.API_URL}/violations/loitering/`;
    
    this.http.get<LoiteringViolation[]>(url)
      .pipe(
        tap({
          next: (violations) => {
            this.loiteringViolations.set(violations);
            this.activeLoiteringCount.set(
              violations.filter(v => v.status === 'active').length
            );
          },
          error: (err) => console.error('Error loading loitering violations:', err)
        })
      )
      .subscribe();
  }

  resolveLoiteringViolation(id: string, notes: string, resolvedBy: string): Observable<LoiteringViolation> {
    return this.http.patch<LoiteringViolation>(`${this.API_URL}/violations/loitering/${id}/`, {
      status: 'resolved',
      resolvedAt: new Date().toISOString(),
      resolvedBy,
      notes
    }).pipe(
      tap({
        next: (updated) => {
          this.loiteringViolations.update(violations =>
            violations.map(v => v.id === id ? updated : v)
          );
          this.activeLoiteringCount.update(count => count - 1);
        }
      })
    );
  }

  // ============================================================================
  // HELMET VIOLATIONS
  // ============================================================================

  loadHelmetViolations(date?: string): void {
    const url = date 
      ? `${this.API_URL}/violations/helmet/?date=${date}`
      : `${this.API_URL}/violations/helmet/`;
    
    this.http.get<HelmetViolation[]>(url)
      .pipe(
        tap({
          next: (violations) => {
            this.helmetViolations.set(violations);
            this.activeHelmetCount.set(
              violations.filter(v => v.status === 'active').length
            );
          },
          error: (err) => console.error('Error loading helmet violations:', err)
        })
      )
      .subscribe();
  }

  resolveHelmetViolation(id: string, notes: string, resolvedBy: string): Observable<HelmetViolation> {
    return this.http.patch<HelmetViolation>(`${this.API_URL}/violations/helmet/${id}/`, {
      status: 'resolved',
      resolvedAt: new Date().toISOString(),
      resolvedBy,
      notes
    }).pipe(
      tap({
        next: (updated) => {
          this.helmetViolations.update(violations =>
            violations.map(v => v.id === id ? updated : v)
          );
          this.activeHelmetCount.update(count => count - 1);
        }
      })
    );
  }

  // ============================================================================
  // PRODUCTION RECORDS
  // ============================================================================

  loadProductionRecords(date?: string): void {
    const url = date 
      ? `${this.API_URL}/production/?date=${date}`
      : `${this.API_URL}/production/today/`;
    
    this.http.get<ProductionRecord[]>(url)
      .pipe(
        tap({
          next: (records) => {
            this.productionRecords.set(records);
            this.todayProduction.set(
              records.reduce((sum, r) => sum + r.itemCount, 0)
            );
          },
          error: (err) => console.error('Error loading production records:', err)
        })
      )
      .subscribe();
  }

  getProductionByShift(shiftId: string): ProductionRecord[] {
    return this.productionRecords().filter(r => r.shiftId === shiftId);
  }

  getProductionByItemType(itemType: string): ProductionRecord[] {
    return this.productionRecords().filter(r => r.itemType === itemType);
  }

  // ============================================================================
  // ATTENDANCE RECORDS
  // ============================================================================

  loadAttendanceRecords(date?: string): void {
    const url = date 
      ? `${this.API_URL}/attendance/?date=${date}`
      : `${this.API_URL}/attendance/today/`;
    
    this.http.get<AttendanceRecord[]>(url)
      .pipe(
        tap({
          next: (records) => {
            this.attendanceRecords.set(records);
            this.unknownPersons.set(
              records.filter(r => r.status === 'unknown')
            );
          },
          error: (err) => console.error('Error loading attendance records:', err)
        })
      )
      .subscribe();
  }

  verifyUnknownPerson(recordId: string, employeeId: string): Observable<AttendanceRecord> {
    return this.http.patch<AttendanceRecord>(`${this.API_URL}/attendance/${recordId}/verify/`, {
      employeeId,
      status: 'verified'
    }).pipe(
      tap({
        next: (updated) => {
          this.attendanceRecords.update(records =>
            records.map(r => r.id === recordId ? updated : r)
          );
          this.unknownPersons.update(unknowns =>
            unknowns.filter(r => r.id !== recordId)
          );
        }
      })
    );
  }

  // ============================================================================
  // ANALYTICS
  // ============================================================================

  getViolationsByDate(startDate: string, endDate: string): Observable<any> {
    return this.http.get(`${this.API_URL}/analytics/violations/`, {
      params: { startDate, endDate }
    });
  }

  getProductionAnalytics(startDate: string, endDate: string): Observable<any> {
    return this.http.get(`${this.API_URL}/analytics/production/`, {
      params: { startDate, endDate }
    });
  }

  getAttendanceAnalytics(startDate: string, endDate: string): Observable<any> {
    return this.http.get(`${this.API_URL}/analytics/attendance/`, {
      params: { startDate, endDate }
    });
  }
}
