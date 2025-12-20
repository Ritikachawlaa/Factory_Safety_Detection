import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ============================================================================
// MODELS & INTERFACES
// ============================================================================

export interface ProcessFrameRequest {
  frame_base64: string;
  frame_index: number;
}

export interface VehicleDetection {
  frame_index: number;
  vehicles_detected: number;
  vehicles_tracked: number;
  plates_recognized: number;
  alerts_triggered: number;
  vehicle_counts: {
    cars: number;
    trucks: number;
    motorcycles: number;
    buses: number;
    vans: number;
  };
  recent_alerts: GateAlert[];
  processing_time_ms: number;
}

export interface GateAlert {
  alert_type: 'UNKNOWN_VEHICLE' | 'BLOCKED_VEHICLE' | 'SUSPICIOUS' | 'AUTHORIZED';
  track_id: number;
  vehicle_type: string;
  plate_number: string;
  timestamp: string;
  confidence: number;
  message: string;
}

export interface VehicleResponse {
  id: number;
  plate_number: string;
  owner_name: string;
  owner_email: string;
  vehicle_type: string;
  vehicle_model: string;
  category: string;
  department: string;
  phone_number?: string;
  notes?: string;
  status: 'ACTIVE' | 'BLOCKED' | 'SUSPENDED';
  registration_date: string;
  is_active: boolean;
  last_access?: string;
}

export interface VehicleRegisterRequest {
  plate_number: string;
  owner_name: string;
  owner_email: string;
  vehicle_type: string;
  vehicle_model: string;
  category: string;
  department: string;
  phone_number?: string;
  notes?: string;
  status: string;
}

export interface VehicleAccessLog {
  id: number;
  vehicle_id: number;
  plate_number: string;
  vehicle_type: string;
  access_time: string;
  is_authorized: boolean;
  confidence: number;
  camera_id?: string;
  snapshot_path?: string;
}

export interface DailySummaryResponse {
  date: string;
  total_vehicles: number;
  authorized_vehicles: number;
  unknown_vehicles: number;
  blocked_vehicles: number;
  vehicles_by_type: any;
  alerts_count: number;
}

export interface MonthlySummaryResponse {
  month: string;
  total_vehicles: number;
  authorized_vehicles: number;
  unknown_vehicles: number;
  daily_summaries: DailySummaryResponse[];
}

export interface StatisticsResponse {
  total_vehicles_tracked: number;
  total_plates_recognized: number;
  total_alerts: number;
  average_processing_time: number;
  unknown_vehicles_count: number;
  blocked_vehicles_count: number;
  vehicle_type_distribution: any;
}

// ============================================================================
// SERVICE IMPLEMENTATION
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class VehicleService {
  private apiUrl = `${environment.apiUrl}/module2`;

  // Observables for real-time updates
  private vehicleDetectionsSubject = new BehaviorSubject<VehicleDetection | null>(null);
  public vehicleDetections$ = this.vehicleDetectionsSubject.asObservable();

  private vehiclesSubject = new BehaviorSubject<VehicleResponse[]>([]);
  public vehicles$ = this.vehiclesSubject.asObservable();

  private accessLogsSubject = new BehaviorSubject<VehicleAccessLog[]>([]);
  public accessLogs$ = this.accessLogsSubject.asObservable();

  private alertsSubject = new BehaviorSubject<GateAlert[]>([]);
  public alerts$ = this.alertsSubject.asObservable();

  private healthSubject = new BehaviorSubject<any>(null);
  public health$ = this.healthSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeHealthCheck();
  }

  // ============================================================================
  // PROCESS FRAME - Real-time Vehicle Detection
  // ============================================================================

  /**
   * Process a video frame for vehicle detection and ANPR
   * @param request Frame data and metadata
   * @returns Observable of detection results
   */
  processFrame(request: ProcessFrameRequest): Observable<VehicleDetection> {
    return this.http.post<VehicleDetection>(`${this.apiUrl}/process-frame`, request)
      .pipe(
        tap(response => {
          this.vehicleDetectionsSubject.next(response);
          if (response.recent_alerts && response.recent_alerts.length > 0) {
            const currentAlerts = this.alertsSubject.value;
            const newAlerts = [...response.recent_alerts, ...currentAlerts].slice(0, 100);
            this.alertsSubject.next(newAlerts);
          }
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Get latest vehicle detection results
   */
  getLatestDetection(): Observable<VehicleDetection | null> {
    return this.vehicleDetections$;
  }

  // ============================================================================
  // VEHICLE REGISTRATION & MANAGEMENT
  // ============================================================================

  /**
   * Register a new authorized vehicle
   */
  registerVehicle(request: VehicleRegisterRequest): Observable<VehicleResponse> {
    return this.http.post<VehicleResponse>(`${this.apiUrl}/vehicle/register`, request)
      .pipe(
        tap(() => this.refreshVehicles()),
        catchError(this.handleError)
      );
  }

  /**
   * List all authorized vehicles
   */
  listVehicles(
    category?: string,
    status?: string,
    limit: number = 100
  ): Observable<VehicleResponse[]> {
    let url = `${this.apiUrl}/vehicles?limit=${limit}`;
    if (category) url += `&category=${category}`;
    if (status) url += `&status=${status}`;

    return this.http.get<VehicleResponse[]>(url)
      .pipe(
        tap(vehicles => this.vehiclesSubject.next(vehicles)),
        catchError(this.handleError)
      );
  }

  /**
   * Get vehicle by ID
   */
  getVehicle(vehicleId: number): Observable<VehicleResponse> {
    return this.http.get<VehicleResponse>(`${this.apiUrl}/vehicles/${vehicleId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update vehicle status
   */
  updateVehicleStatus(vehicleId: number, status: string): Observable<VehicleResponse> {
    return this.http.put<VehicleResponse>(
      `${this.apiUrl}/vehicles/${vehicleId}/status`,
      { status }
    ).pipe(
      tap(() => this.refreshVehicles()),
      catchError(this.handleError)
    );
  }

  /**
   * Delete vehicle
   */
  deleteVehicle(vehicleId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/vehicles/${vehicleId}`)
      .pipe(
        tap(() => this.refreshVehicles()),
        catchError(this.handleError)
      );
  }

  /**
   * Refresh vehicle list
   */
  private refreshVehicles(): void {
    this.listVehicles().subscribe();
  }

  /**
   * Get vehicles as observable stream
   */
  getVehiclesStream(): Observable<VehicleResponse[]> {
    return this.vehicles$;
  }

  // ============================================================================
  // ACCESS LOGS
  // ============================================================================

  /**
   * Get vehicle access logs
   */
  getAccessLogs(limit: number = 100): Observable<VehicleAccessLog[]> {
    return this.http.get<VehicleAccessLog[]>(`${this.apiUrl}/access-logs?limit=${limit}`)
      .pipe(
        tap(logs => this.accessLogsSubject.next(logs)),
        catchError(this.handleError)
      );
  }

  /**
   * Get access logs for specific vehicle
   */
  getVehicleAccessLogs(vehicleId: number, limit: number = 50): Observable<VehicleAccessLog[]> {
    return this.http.get<VehicleAccessLog[]>(
      `${this.apiUrl}/vehicles/${vehicleId}/access-logs?limit=${limit}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get today's access logs
   */
  getTodayAccessLogs(): Observable<VehicleAccessLog[]> {
    return this.http.get<VehicleAccessLog[]>(`${this.apiUrl}/access-logs/today`)
      .pipe(
        tap(logs => this.accessLogsSubject.next(logs)),
        catchError(this.handleError)
      );
  }

  /**
   * Get access log streams
   */
  getAccessLogsStream(): Observable<VehicleAccessLog[]> {
    return this.accessLogs$;
  }

  /**
   * Get access log by ID
   */
  getAccessLog(logId: number): Observable<VehicleAccessLog> {
    return this.http.get<VehicleAccessLog>(`${this.apiUrl}/access-logs/${logId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Flag access log for review
   */
  flagAccessLog(logId: number): Observable<VehicleAccessLog> {
    return this.http.post<VehicleAccessLog>(
      `${this.apiUrl}/access-logs/${logId}/flag`,
      {}
    ).pipe(
      tap(() => this.getTodayAccessLogs().subscribe()),
      catchError(this.handleError)
    );
  }

  // ============================================================================
  // SUMMARIES & REPORTS
  // ============================================================================

  /**
   * Get daily summary
   */
  getDailySummary(date: string): Observable<DailySummaryResponse> {
    return this.http.get<DailySummaryResponse>(
      `${this.apiUrl}/access-logs/daily-summary?date=${date}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get monthly summary
   */
  getMonthlySummary(month: string): Observable<MonthlySummaryResponse> {
    return this.http.get<MonthlySummaryResponse>(
      `${this.apiUrl}/access-logs/monthly-summary?month=${month}`
    ).pipe(catchError(this.handleError));
  }

  // ============================================================================
  // ALERTS
  // ============================================================================

  /**
   * Get gate alerts
   */
  getAlerts(limit: number = 100): Observable<GateAlert[]> {
    return this.http.get<GateAlert[]>(`${this.apiUrl}/alerts?limit=${limit}`)
      .pipe(
        tap(alerts => this.alertsSubject.next(alerts)),
        catchError(this.handleError)
      );
  }

  /**
   * Get alerts stream
   */
  getAlertsStream(): Observable<GateAlert[]> {
    return this.alerts$;
  }

  // ============================================================================
  // STATISTICS
  // ============================================================================

  /**
   * Get module statistics
   */
  getStatistics(): Observable<StatisticsResponse> {
    return this.http.get<StatisticsResponse>(`${this.apiUrl}/statistics`)
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
    setInterval(() => {
      this.healthCheck().subscribe(
        () => { /* Health check passed */ },
        (error) => console.error('Vehicle Module Health check failed:', error)
      );
    }, 30000);
  }

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred in Vehicle Module';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }

    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
