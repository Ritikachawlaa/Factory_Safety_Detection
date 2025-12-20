import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, interval } from 'rxjs';
import { catchError, tap, switchMap, startWith } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ============================================================================
// MODELS & INTERFACES
// ============================================================================

export interface CameraResponse {
  id: number;
  name: string;
  location: string;
  rtsp_url: string;
  view_area_sqm: number;
  capacity: number;
  is_active: boolean;
  created_date: string;
}

export interface CameraCreateRequest {
  name: string;
  location: string;
  rtsp_url: string;
  view_area_sqm: number;
  capacity: number;
}

export interface VirtualLineResponse {
  id: number;
  camera_id: number;
  line_name: string;
  line_coordinates: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  direction: 'BIDIRECTIONAL' | 'INCOMING' | 'OUTGOING';
  count_threshold: number;
  is_active: boolean;
  created_date: string;
}

export interface VirtualLineCreateRequest {
  camera_id: number;
  line_name: string;
  line_coordinates: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  direction: string;
  count_threshold?: number;
}

export interface OccupancyLiveResponse {
  camera_id: number;
  timestamp: string;
  current_occupancy: number;
  capacity: number;
  occupancy_percentage: number;
  people_entering: number;
  people_exiting: number;
  density_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  virtual_lines: {
    line_id: number;
    line_name: string;
    total_crossings: number;
    incoming_count: number;
    outgoing_count: number;
  }[];
}

export interface FacilityOccupancyResponse {
  timestamp: string;
  total_occupancy: number;
  total_capacity: number;
  overall_percentage: number;
  cameras: {
    camera_id: number;
    camera_name: string;
    occupancy: number;
    capacity: number;
    percentage: number;
    density_level: string;
  }[];
  high_density_areas: any[];
  alerts_count: number;
}

export interface OccupancyLogResponse {
  id: number;
  camera_id: number;
  timestamp: string;
  occupancy_count: number;
  entering_count: number;
  exiting_count: number;
  density_level: string;
}

export interface HourlyOccupancyResponse {
  camera_id: number;
  hour: string;
  average_occupancy: number;
  peak_occupancy: number;
  minimum_occupancy: number;
  entering_count: number;
  exiting_count: number;
}

export interface DailyOccupancyResponse {
  camera_id: number;
  date: string;
  average_occupancy: number;
  peak_occupancy: number;
  total_entering: number;
  total_exiting: number;
  hours: HourlyOccupancyResponse[];
}

export interface MonthlyOccupancyResponse {
  camera_id: number;
  month: string;
  average_daily_occupancy: number;
  peak_daily_occupancy: number;
  days: DailyOccupancyResponse[];
}

export interface OccupancyAlertResponse {
  id: number;
  camera_id: number;
  alert_type: 'OVERCAPACITY' | 'UNUSUAL_ACTIVITY' | 'DENSITY_HIGH' | 'EMERGENCY';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  timestamp: string;
  occupancy_count: number;
  capacity: number;
  message: string;
  is_resolved: boolean;
  resolved_time?: string;
}

export interface FacilityStatsResponse {
  total_cameras: number;
  total_capacity: number;
  current_occupancy: number;
  occupancy_percentage: number;
  areas_by_density: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  today_peak_occupancy: number;
  average_stay_time_minutes: number;
  total_entries_today: number;
  total_exits_today: number;
}

// ============================================================================
// SERVICE IMPLEMENTATION
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class OccupancyService {
  private apiUrl = `${environment.apiUrl}/module4`;

  // Observables for real-time updates
  private camerasSubject = new BehaviorSubject<CameraResponse[]>([]);
  public cameras$ = this.camerasSubject.asObservable();

  private virtualLinesSubject = new BehaviorSubject<VirtualLineResponse[]>([]);
  public virtualLines$ = this.virtualLinesSubject.asObservable();

  private facilityOccupancySubject = new BehaviorSubject<FacilityOccupancyResponse | null>(null);
  public facilityOccupancy$ = this.facilityOccupancySubject.asObservable();

  private cameraOccupancySubject = new BehaviorSubject<Map<number, OccupancyLiveResponse>>(new Map());
  public cameraOccupancy$ = this.cameraOccupancySubject.asObservable();

  private alertsSubject = new BehaviorSubject<OccupancyAlertResponse[]>([]);
  public alerts$ = this.alertsSubject.asObservable();

  private statsSubject = new BehaviorSubject<FacilityStatsResponse | null>(null);
  public stats$ = this.statsSubject.asObservable();

  private healthSubject = new BehaviorSubject<any>(null);
  public health$ = this.healthSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeHealthCheck();
    this.loadInitialData();
    this.startRealTimeUpdates();
  }

  // ============================================================================
  // CAMERAS
  // ============================================================================

  /**
   * Create new camera
   */
  createCamera(request: CameraCreateRequest): Observable<CameraResponse> {
    return this.http.post<CameraResponse>(`${this.apiUrl}/cameras`, request)
      .pipe(
        tap(() => this.refreshCameras()),
        catchError(this.handleError)
      );
  }

  /**
   * Get all cameras
   */
  listCameras(): Observable<CameraResponse[]> {
    return this.http.get<CameraResponse[]>(`${this.apiUrl}/cameras`)
      .pipe(
        tap(cameras => this.camerasSubject.next(cameras)),
        catchError(this.handleError)
      );
  }

  /**
   * Get camera by ID
   */
  getCamera(cameraId: number): Observable<CameraResponse> {
    return this.http.get<CameraResponse>(`${this.apiUrl}/cameras/${cameraId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update camera
   */
  updateCamera(cameraId: number, updates: Partial<CameraResponse>): Observable<CameraResponse> {
    return this.http.put<CameraResponse>(`${this.apiUrl}/cameras/${cameraId}`, updates)
      .pipe(
        tap(() => this.refreshCameras()),
        catchError(this.handleError)
      );
  }

  /**
   * Get cameras stream
   */
  getCamerasStream(): Observable<CameraResponse[]> {
    return this.cameras$;
  }

  /**
   * Refresh cameras
   */
  private refreshCameras(): void {
    this.listCameras().subscribe();
  }

  // ============================================================================
  // VIRTUAL LINES
  // ============================================================================

  /**
   * Create virtual line for counting
   */
  createVirtualLine(request: VirtualLineCreateRequest): Observable<VirtualLineResponse> {
    return this.http.post<VirtualLineResponse>(`${this.apiUrl}/lines`, request)
      .pipe(
        tap(() => this.refreshVirtualLines()),
        catchError(this.handleError)
      );
  }

  /**
   * Get virtual lines for camera
   */
  getCameraVirtualLines(cameraId: number): Observable<VirtualLineResponse[]> {
    return this.http.get<VirtualLineResponse[]>(`${this.apiUrl}/cameras/${cameraId}/lines`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get all virtual lines
   */
  listVirtualLines(): Observable<VirtualLineResponse[]> {
    return this.http.get<VirtualLineResponse[]>(`${this.apiUrl}/lines`)
      .pipe(
        tap(lines => this.virtualLinesSubject.next(lines)),
        catchError(this.handleError)
      );
  }

  /**
   * Get virtual line by ID
   */
  getVirtualLine(lineId: number): Observable<VirtualLineResponse> {
    return this.http.get<VirtualLineResponse>(`${this.apiUrl}/lines/${lineId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update virtual line
   */
  updateVirtualLine(lineId: number, updates: Partial<VirtualLineResponse>): Observable<VirtualLineResponse> {
    return this.http.put<VirtualLineResponse>(`${this.apiUrl}/lines/${lineId}`, updates)
      .pipe(
        tap(() => this.refreshVirtualLines()),
        catchError(this.handleError)
      );
  }

  /**
   * Get virtual lines stream
   */
  getVirtualLinesStream(): Observable<VirtualLineResponse[]> {
    return this.virtualLines$;
  }

  /**
   * Refresh virtual lines
   */
  private refreshVirtualLines(): void {
    this.listVirtualLines().subscribe();
  }

  // ============================================================================
  // OCCUPANCY - REAL-TIME
  // ============================================================================

  /**
   * Get live occupancy for specific camera
   */
  getLiveCameraOccupancy(cameraId: number): Observable<OccupancyLiveResponse> {
    return this.http.get<OccupancyLiveResponse>(`${this.apiUrl}/cameras/${cameraId}/live`)
      .pipe(
        tap(occupancy => {
          const map = this.cameraOccupancySubject.value;
          map.set(cameraId, occupancy);
          this.cameraOccupancySubject.next(map);
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Get live facility occupancy
   */
  getLiveFacilityOccupancy(): Observable<FacilityOccupancyResponse> {
    return this.http.get<FacilityOccupancyResponse>(`${this.apiUrl}/facility/live`)
      .pipe(
        tap(occupancy => this.facilityOccupancySubject.next(occupancy)),
        catchError(this.handleError)
      );
  }

  /**
   * Get facility occupancy stream
   */
  getFacilityOccupancyStream(): Observable<FacilityOccupancyResponse | null> {
    return this.facilityOccupancy$;
  }

  /**
   * Get camera occupancy from map
   */
  getCameraOccupancyMap(): Observable<Map<number, OccupancyLiveResponse>> {
    return this.cameraOccupancy$;
  }

  /**
   * Calibrate camera (setup counting line)
   */
  calibrateCamera(cameraId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/cameras/${cameraId}/calibrate`, {})
      .pipe(catchError(this.handleError));
  }

  // ============================================================================
  // OCCUPANCY - LOGS
  // ============================================================================

  /**
   * Get occupancy logs for camera
   */
  getCameraOccupancyLogs(cameraId: number, limit: number = 100): Observable<OccupancyLogResponse[]> {
    return this.http.get<OccupancyLogResponse[]>(
      `${this.apiUrl}/cameras/${cameraId}/logs?limit=${limit}`
    ).pipe(catchError(this.handleError));
  }

  // ============================================================================
  // OCCUPANCY - ANALYTICS
  // ============================================================================

  /**
   * Get hourly occupancy data
   */
  getCameraHourlyOccupancy(cameraId: number, date: string): Observable<HourlyOccupancyResponse[]> {
    return this.http.get<HourlyOccupancyResponse[]>(
      `${this.apiUrl}/cameras/${cameraId}/hourly?date=${date}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get daily occupancy data
   */
  getCameraDailyOccupancy(cameraId: number, month: string): Observable<DailyOccupancyResponse[]> {
    return this.http.get<DailyOccupancyResponse[]>(
      `${this.apiUrl}/cameras/${cameraId}/daily?month=${month}`
    ).pipe(catchError(this.handleError));
  }

  /**
   * Get monthly occupancy data
   */
  getCameraMonthlyOccupancy(cameraId: number, year: string): Observable<MonthlyOccupancyResponse[]> {
    return this.http.get<MonthlyOccupancyResponse[]>(
      `${this.apiUrl}/cameras/${cameraId}/monthly?year=${year}`
    ).pipe(catchError(this.handleError));
  }

  // ============================================================================
  // ALERTS
  // ============================================================================

  /**
   * Get occupancy alerts
   */
  getAlerts(limit: number = 100): Observable<OccupancyAlertResponse[]> {
    return this.http.get<OccupancyAlertResponse[]>(`${this.apiUrl}/alerts?limit=${limit}`)
      .pipe(
        tap(alerts => this.alertsSubject.next(alerts)),
        catchError(this.handleError)
      );
  }

  /**
   * Get alerts stream
   */
  getAlertsStream(): Observable<OccupancyAlertResponse[]> {
    return this.alerts$;
  }

  /**
   * Resolve alert
   */
  resolveAlert(alertId: number): Observable<OccupancyAlertResponse> {
    return this.http.put<OccupancyAlertResponse>(
      `${this.apiUrl}/alerts/${alertId}/resolve`,
      {}
    ).pipe(
      tap(() => this.getAlerts().subscribe()),
      catchError(this.handleError)
    );
  }

  // ============================================================================
  // STATISTICS
  // ============================================================================

  /**
   * Get facility statistics
   */
  getFacilityStats(): Observable<FacilityStatsResponse> {
    return this.http.get<FacilityStatsResponse>(`${this.apiUrl}/facility/stats`)
      .pipe(
        tap(stats => this.statsSubject.next(stats)),
        catchError(this.handleError)
      );
  }

  /**
   * Get stats stream
   */
  getStatsStream(): Observable<FacilityStatsResponse | null> {
    return this.stats$;
  }

  // ============================================================================
  // DATA AGGREGATION
  // ============================================================================

  /**
   * Trigger data aggregation
   */
  triggerAggregation(): Observable<any> {
    return this.http.post(`${this.apiUrl}/aggregate`, {})
      .pipe(catchError(this.handleError));
  }

  // ============================================================================
  // INITIALIZATION & REAL-TIME UPDATES
  // ============================================================================

  /**
   * Load initial data
   */
  private loadInitialData(): void {
    this.listCameras().subscribe();
    this.listVirtualLines().subscribe();
    this.getLiveFacilityOccupancy().subscribe();
    this.getFacilityStats().subscribe();
    this.getAlerts().subscribe();
  }

  /**
   * Start real-time updates every 5 seconds
   */
  private startRealTimeUpdates(): void {
    interval(5000)
      .pipe(
        startWith(0),
        switchMap(() => this.getLiveFacilityOccupancy())
      )
      .subscribe(
        (occupancy) => this.facilityOccupancySubject.next(occupancy),
        (error) => console.error('Error updating facility occupancy:', error)
      );

    // Update facility stats every 30 seconds
    interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.getFacilityStats())
      )
      .subscribe(
        (stats) => this.statsSubject.next(stats),
        (error) => console.error('Error updating facility stats:', error)
      );
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
        (error) => console.error('Occupancy Module Health check failed:', error)
      );
    }, 30000);
  }

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred in Occupancy Module';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }

    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
