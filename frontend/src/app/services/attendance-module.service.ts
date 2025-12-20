import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ============================================================================
// MODELS & INTERFACES
// ============================================================================

export interface FaceDetectionRequest {
  aws_rekognition_id: string;
  camera_id: string;
  confidence: number;
  is_exit?: boolean;
  exit_reason?: string;
}

export interface AttendanceRecord {
  id: number;
  employee_id: number;
  employee_name: string;
  attendance_date: string;
  check_in_time: string;
  check_out_time?: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE' | 'HALF_DAY' | 'ON_LEAVE';
  is_late: boolean;
  duration_minutes?: number;
  department: string;
  camera_id: string;
  confidence: number;
  is_override: boolean;
  override_reason?: string;
  override_user?: string;
}

export interface CheckInResult {
  success: boolean;
  employee_id: number;
  employee_name: string;
  check_in_time: string;
  is_late: boolean;
  message: string;
  record_id?: number;
}

export interface CheckOutResult {
  success: boolean;
  employee_id: number;
  check_out_time: string;
  duration_minutes: number;
  message: string;
  record_id?: number;
}

export interface ManualOverrideRequest {
  employee_id: number;
  attendance_date: string;
  check_in_time?: string;
  check_out_time?: string;
  status?: string;
  reason: string;
  override_user: string;
}

export interface AttendanceReport {
  employee_id: number;
  employee_name: string;
  department: string;
  total_days: number;
  present_days: number;
  absent_days: number;
  late_count: number;
  half_days: number;
  leaves: number;
  attendance_percentage: number;
  period: string;
}

export interface DepartmentResponse {
  id: number;
  name: string;
  manager: string;
  contact_email: string;
  description?: string;
  employee_count: number;
  created_date: string;
}

export interface ShiftResponse {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  department?: string;
  is_active: boolean;
  created_date: string;
}

export interface AttendanceSummary {
  today_present: number;
  today_absent: number;
  today_late: number;
  total_employees: number;
  attendance_percentage: number;
  department_summaries: any;
}

// ============================================================================
// SERVICE IMPLEMENTATION
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {
  private apiUrl = `${environment.apiUrl}/module3`;

  // Observables for real-time updates
  private attendanceRecordsSubject = new BehaviorSubject<AttendanceRecord[]>([]);
  public attendanceRecords$ = this.attendanceRecordsSubject.asObservable();

  private summarySubject = new BehaviorSubject<AttendanceSummary | null>(null);
  public summary$ = this.summarySubject.asObservable();

  private shiftsSubject = new BehaviorSubject<ShiftResponse[]>([]);
  public shifts$ = this.shiftsSubject.asObservable();

  private departmentsSubject = new BehaviorSubject<DepartmentResponse[]>([]);
  public departments$ = this.departmentsSubject.asObservable();

  private healthSubject = new BehaviorSubject<any>(null);
  public health$ = this.healthSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeHealthCheck();
    this.loadInitialData();
  }

  // ============================================================================
  // FACE DETECTION & ATTENDANCE
  // ============================================================================

  /**
   * Process face detection from camera
   * Entry point for identity service integration
   */
  processFaceDetection(request: FaceDetectionRequest): Observable<CheckInResult> {
    return this.http.post<CheckInResult>(
      `${this.apiUrl}/process-face-detection`,
      request
    ).pipe(
      tap(result => {
        if (result.success) {
          this.refreshAttendanceRecords();
          this.refreshSummary();
        }
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Process exit detection
   */
  processExitDetection(
    awsRekognitionId: string,
    cameraId: string,
    confidence: number
  ): Observable<CheckOutResult> {
    return this.http.post<CheckOutResult>(
      `${this.apiUrl}/process-face-detection`,
      {
        aws_rekognition_id: awsRekognitionId,
        camera_id: cameraId,
        confidence,
        is_exit: true,
        exit_reason: 'AUTOMATIC'
      }
    ).pipe(
      tap(() => {
        this.refreshAttendanceRecords();
        this.refreshSummary();
      }),
      catchError(this.handleError)
    );
  }

  // ============================================================================
  // MANUAL OVERRIDE
  // ============================================================================

  /**
   * Create manual attendance override
   */
  createOverride(request: ManualOverrideRequest): Observable<AttendanceRecord> {
    return this.http.post<AttendanceRecord>(
      `${this.apiUrl}/override`,
      request
    ).pipe(
      tap(() => {
        this.refreshAttendanceRecords();
        this.refreshSummary();
      }),
      catchError(this.handleError)
    );
  }

  // ============================================================================
  // ATTENDANCE RECORDS
  // ============================================================================

  /**
   * Get specific attendance record
   */
  getRecord(recordId: number): Observable<AttendanceRecord> {
    return this.http.get<AttendanceRecord>(`${this.apiUrl}/record/${recordId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get all attendance records with filters
   */
  getAttendanceRecords(
    employeeId?: number,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Observable<AttendanceRecord[]> {
    let url = `${this.apiUrl}/reports?limit=${limit}`;
    if (employeeId) url += `&employee_id=${employeeId}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;

    return this.http.get<AttendanceRecord[]>(url)
      .pipe(
        tap(records => this.attendanceRecordsSubject.next(records)),
        catchError(this.handleError)
      );
  }

  /**
   * Get today's attendance records
   */
  getTodayAttendance(): Observable<AttendanceRecord[]> {
    return this.http.get<AttendanceRecord[]>(`${this.apiUrl}/reports?date=today`)
      .pipe(
        tap(records => this.attendanceRecordsSubject.next(records)),
        catchError(this.handleError)
      );
  }

  /**
   * Get employee records
   */
  getEmployeeRecords(employeeId: number, limit: number = 50): Observable<AttendanceRecord[]> {
    return this.http.get<AttendanceRecord[]>(
      `${this.apiUrl}/employee/${employeeId}/records?limit=${limit}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get records stream
   */
  getAttendanceRecordsStream(): Observable<AttendanceRecord[]> {
    return this.attendanceRecords$;
  }

  /**
   * Refresh attendance records
   */
  private refreshAttendanceRecords(): void {
    this.getTodayAttendance().subscribe();
  }

  // ============================================================================
  // REPORTS
  // ============================================================================

  /**
   * Get employee monthly report
   */
  getEmployeeMonthlyReport(employeeId: number, month: string): Observable<AttendanceReport> {
    return this.http.get<AttendanceReport>(
      `${this.apiUrl}/employee/${employeeId}/monthly-report?month=${month}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get all reports
   */
  getReports(
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Observable<AttendanceReport[]> {
    let url = `${this.apiUrl}/reports?limit=${limit}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;

    return this.http.get<AttendanceReport[]>(url)
      .pipe(catchError(this.handleError));
  }

  // ============================================================================
  // SUMMARY
  // ============================================================================

  /**
   * Get attendance summary
   */
  getSummary(): Observable<AttendanceSummary> {
    return this.http.get<AttendanceSummary>(`${this.apiUrl}/summary`)
      .pipe(
        tap(summary => this.summarySubject.next(summary)),
        catchError(this.handleError)
      );
  }

  /**
   * Get summary stream
   */
  getSummaryStream(): Observable<AttendanceSummary | null> {
    return this.summary$;
  }

  /**
   * Refresh summary
   */
  private refreshSummary(): void {
    this.getSummary().subscribe();
  }

  // ============================================================================
  // SHIFTS
  // ============================================================================

  /**
   * Create new shift
   */
  createShift(shift: Partial<ShiftResponse>): Observable<ShiftResponse> {
    return this.http.post<ShiftResponse>(`${this.apiUrl}/shifts`, shift)
      .pipe(
        tap(() => this.refreshShifts()),
        catchError(this.handleError)
      );
  }

  /**
   * Get all shifts
   */
  listShifts(): Observable<ShiftResponse[]> {
    return this.http.get<ShiftResponse[]>(`${this.apiUrl}/shifts`)
      .pipe(
        tap(shifts => this.shiftsSubject.next(shifts)),
        catchError(this.handleError)
      );
  }

  /**
   * Get shift by ID
   */
  getShift(shiftId: number): Observable<ShiftResponse> {
    return this.http.get<ShiftResponse>(`${this.apiUrl}/shifts/${shiftId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get shifts stream
   */
  getShiftsStream(): Observable<ShiftResponse[]> {
    return this.shifts$;
  }

  /**
   * Refresh shifts
   */
  private refreshShifts(): void {
    this.listShifts().subscribe();
  }

  // ============================================================================
  // DEPARTMENTS
  // ============================================================================

  /**
   * Create new department
   */
  createDepartment(dept: Partial<DepartmentResponse>): Observable<DepartmentResponse> {
    return this.http.post<DepartmentResponse>(`${this.apiUrl}/departments`, dept)
      .pipe(
        tap(() => this.refreshDepartments()),
        catchError(this.handleError)
      );
  }

  /**
   * Get all departments
   */
  listDepartments(): Observable<DepartmentResponse[]> {
    return this.http.get<DepartmentResponse[]>(`${this.apiUrl}/departments`)
      .pipe(
        tap(departments => this.departmentsSubject.next(departments)),
        catchError(this.handleError)
      );
  }

  /**
   * Get department by ID
   */
  getDepartment(deptId: number): Observable<DepartmentResponse> {
    return this.http.get<DepartmentResponse>(`${this.apiUrl}/departments/${deptId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get departments stream
   */
  getDepartmentsStream(): Observable<DepartmentResponse[]> {
    return this.departments$;
  }

  /**
   * Refresh departments
   */
  private refreshDepartments(): void {
    this.listDepartments().subscribe();
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  /**
   * Load initial data on service creation
   */
  private loadInitialData(): void {
    this.getTodayAttendance().subscribe();
    this.getSummary().subscribe();
    this.listShifts().subscribe();
    this.listDepartments().subscribe();
  }

  // ============================================================================
  // HEALTH CHECK
  // ============================================================================

  /**
   * Check module health status
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`)
      .pipe(
        tap(health => this.healthSubject.next(health)),
        catchError(this.handleError)
      );
  }

  /**
   * Initialize periodic health checks
   */
  private initializeHealthCheck(): void {
    setInterval(() => {
      this.healthCheck().subscribe(
        () => { /* Health check passed */ },
        (error) => console.error('Attendance Module Health check failed:', error)
      );
    }, 30000);
  }

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred in Attendance Module';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }

    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
