import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ============================================================================
// MODELS & INTERFACES
// ============================================================================

export interface TrackID {
  track_id: number;
  face_crop: string; // Base64 encoded face crop
}

export interface ProcessFrameRequest {
  frame: string;        // Base64 encoded frame
  track_ids: TrackID[];
  frame_id?: string;
}

export interface IdentityResult {
  track_id: number;
  name: string;
  confidence: number;
  is_cached: boolean;
  is_authorized: boolean;
  face_id?: string;
  access_log_id?: number;
}

export interface ProcessFrameResponse {
  success: boolean;
  identities: IdentityResult[];
  unknown_count: number;
  processing_time_ms: number;
  frame_id?: string;
  cache_stats: any;
  errors: string[];
}

export interface EnrollEmployeeRequest {
  name: string;
  department: string;
  email?: string;
  employee_id_code?: string;
  phone?: string;
  notes?: string;
  photo: File;
}

export interface EnrollEmployeeResponse {
  success: boolean;
  employee_id: number;
  face_id: string;
  message: string;
}

export interface EmployeeInfo {
  id: number;
  name: string;
  email: string;
  phone?: string;
  department: string;
  employee_id_code?: string;
  face_id?: string;
  is_enrolled: boolean;
  enrollment_date: string;
  notes?: string;
  last_seen?: string;
  access_count: number;
}

export interface AccessLog {
  id: number;
  employee_id: number;
  timestamp: string;
  face_confidence: number;
  camera_id?: string;
  access_status: string;
  face_id?: string;
}

export interface SearchFacesResponse {
  success: boolean;
  faces: EmployeeInfo[];
  total_matches: number;
  processing_time_ms: number;
}

// ============================================================================
// SERVICE IMPLEMENTATION
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class IdentityService {
  private apiUrl = `${environment.apiUrl}/module1`;
  
  // Observables for real-time updates
  private identitiesSubject = new BehaviorSubject<IdentityResult[]>([]);
  public identities$ = this.identitiesSubject.asObservable();

  private employeesSubject = new BehaviorSubject<EmployeeInfo[]>([]);
  public employees$ = this.employeesSubject.asObservable();

  private accessLogsSubject = new BehaviorSubject<AccessLog[]>([]);
  public accessLogs$ = this.accessLogsSubject.asObservable();

  private healthSubject = new BehaviorSubject<any>(null);
  public health$ = this.healthSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeHealthCheck();
  }

  // ============================================================================
  // PROCESS FRAME - Real-time Identity Detection
  // ============================================================================

  /**
   * Process a video frame to identify tracked persons
   * @param frame Base64 encoded frame
   * @param trackIds List of tracked persons with face crops
   * @returns Observable of identification results
   */
  processFrame(request: ProcessFrameRequest): Observable<ProcessFrameResponse> {
    return this.http.post<ProcessFrameResponse>(`${this.apiUrl}/process-frame`, request)
      .pipe(
        tap(response => {
          if (response.success && response.identities) {
            this.identitiesSubject.next(response.identities);
          }
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Get real-time stream of identities from camera feed
   */
  getIdentitiesStream(): Observable<IdentityResult[]> {
    return this.identities$;
  }

  // ============================================================================
  // EMPLOYEE ENROLLMENT
  // ============================================================================

  /**
   * Enroll a new employee in the facial recognition system
   * @param request Enrollment request with photo
   * @returns Observable of enrollment response
   */
  enrollEmployee(request: EnrollEmployeeRequest): Observable<EnrollEmployeeResponse> {
    const formData = new FormData();
    formData.append('name', request.name);
    formData.append('department', request.department);
    if (request.email) formData.append('email', request.email);
    if (request.employee_id_code) formData.append('employee_id_code', request.employee_id_code);
    if (request.phone) formData.append('phone', request.phone);
    if (request.notes) formData.append('notes', request.notes);
    formData.append('photo', request.photo);

    return this.http.post<EnrollEmployeeResponse>(`${this.apiUrl}/enroll`, formData)
      .pipe(
        tap(response => {
          if (response.success) {
            this.refreshEmployees();
          }
        }),
        catchError(this.handleError)
      );
  }

  // ============================================================================
  // EMPLOYEE MANAGEMENT
  // ============================================================================

  /**
   * Get employee details
   */
  getEmployee(employeeId: number): Observable<EmployeeInfo> {
    return this.http.get<EmployeeInfo>(`${this.apiUrl}/employees/${employeeId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * List all employees
   */
  listEmployees(limit: number = 100): Observable<EmployeeInfo[]> {
    return this.http.get<EmployeeInfo[]>(`${this.apiUrl}/employees?limit=${limit}`)
      .pipe(
        tap(employees => this.employeesSubject.next(employees)),
        catchError(this.handleError)
      );
  }

  /**
   * Get employees with enrollment status
   */
  getEnrolledEmployees(): Observable<EmployeeInfo[]> {
    return this.listEmployees(1000).pipe(
      map(employees => employees.filter(e => e.is_enrolled))
    );
  }

  /**
   * Refresh employee list
   */
  refreshEmployees(): void {
    this.listEmployees().subscribe();
  }

  /**
   * Update employee information
   */
  updateEmployee(employeeId: number, updates: Partial<EmployeeInfo>): Observable<EmployeeInfo> {
    return this.http.put<EmployeeInfo>(`${this.apiUrl}/employees/${employeeId}`, updates)
      .pipe(
        tap(() => this.refreshEmployees()),
        catchError(this.handleError)
      );
  }

  /**
   * Delete employee (soft delete)
   */
  deleteEmployee(employeeId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/employees/${employeeId}`)
      .pipe(
        tap(() => this.refreshEmployees()),
        catchError(this.handleError)
      );
  }

  // ============================================================================
  // ACCESS LOGS
  // ============================================================================

  /**
   * Get access logs with filters
   */
  getAccessLogs(
    startDate?: string,
    endDate?: string,
    employeeId?: number,
    limit: number = 100
  ): Observable<AccessLog[]> {
    let url = `${this.apiUrl}/access-logs?limit=${limit}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (employeeId) url += `&employee_id=${employeeId}`;

    return this.http.get<AccessLog[]>(url)
      .pipe(
        tap(logs => this.accessLogsSubject.next(logs)),
        catchError(this.handleError)
      );
  }

  /**
   * Get today's access logs
   */
  getTodayAccessLogs(): Observable<AccessLog[]> {
    return this.http.get<AccessLog[]>(`${this.apiUrl}/access-logs/today`)
      .pipe(
        tap(logs => this.accessLogsSubject.next(logs)),
        catchError(this.handleError)
      );
  }

  /**
   * Get access log by ID
   */
  getAccessLog(logId: number): Observable<AccessLog> {
    return this.http.get<AccessLog>(`${this.apiUrl}/access-logs/${logId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get access log streams as observable
   */
  getAccessLogsStream(): Observable<AccessLog[]> {
    return this.accessLogs$;
  }

  // ============================================================================
  // FACE RECOGNITION
  // ============================================================================

  /**
   * Search for faces similar to provided face image
   */
  searchFaces(faceImage: string, threshold: number = 0.95): Observable<SearchFacesResponse> {
    return this.http.post<SearchFacesResponse>(
      `${this.apiUrl}/search-faces`,
      { face_image: faceImage, similarity_threshold: threshold }
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get face details
   */
  getFaceDetails(faceId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/faces/${faceId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get unknown faces
   */
  getUnknownFaces(limit: number = 50): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/unknown-faces?limit=${limit}`)
      .pipe(catchError(this.handleError));
  }

  // ============================================================================
  // STATISTICS & REPORTS
  // ============================================================================

  /**
   * Get module statistics
   */
  getStatistics(startDate?: string, endDate?: string): Observable<any> {
    let url = `${this.apiUrl}/statistics`;
    if (startDate || endDate) {
      url += '?';
      if (startDate) url += `start_date=${startDate}`;
      if (endDate) url += (startDate ? '&' : '') + `end_date=${endDate}`;
    }
    return this.http.get<any>(url)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get daily report for employee
   */
  getEmployeeDailyReport(employeeId: number, date: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/employees/${employeeId}/daily-report?date=${date}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get monthly report for employee
   */
  getEmployeeMonthlyReport(employeeId: number, month: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/employees/${employeeId}/monthly-report?month=${month}`)
      .pipe(catchError(this.handleError));
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
    // Check health every 30 seconds
    setInterval(() => {
      this.healthCheck().subscribe(
        () => { /* Health check passed */ },
        (error) => console.error('Health check failed:', error)
      );
    }, 30000);
  }

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }

    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
