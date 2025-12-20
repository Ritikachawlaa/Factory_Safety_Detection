import { Component, OnInit, ViewChild, HostListener } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest, interval } from 'rxjs';
import { map, startWith, switchMap, tap } from 'rxjs/operators';
import { OccupancyService } from '../../services/occupancy.service';
import { VehicleService } from '../../services/vehicle.service';
import { IdentityService } from '../../services/identity.service';
import { AttendanceService } from '../../services/attendance-module.service';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface DashboardEvent {
  id: string;
  type: 'IDENTITY' | 'VEHICLE' | 'ATTENDANCE' | 'OCCUPANCY' | 'ALERT';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  timestamp: Date;
  title: string;
  description: string;
  icon: string;
  thumbnail?: string;
  action?: () => void;
}

export interface CameraViewMode {
  mode: 'single' | 'multi';
  selectedCameraId?: number;
  gridSize?: 2 | 4 | 6 | 9; // 2x1, 2x2, 2x3, 3x3 grid
}

export interface MetricData {
  label: string;
  value: number;
  unit: string;
  previousValue?: number;
  trend?: 'up' | 'down' | 'stable';
  sparklineData?: number[];
  color: 'cyan' | 'emerald' | 'rose' | 'amber';
}

// ============================================================================
// COMPONENT
// ============================================================================

@Component({
  selector: 'app-soc-dashboard',
  templateUrl: './soc-dashboard.component.html',
  styleUrls: ['./soc-dashboard.component.scss']
})
export class SocDashboardComponent implements OnInit {
  // ========================================================================
  // UI STATE
  // ========================================================================

  sidebarOpen$ = new BehaviorSubject<boolean>(true);
  activeModule$ = new BehaviorSubject<'identity' | 'vehicles' | 'attendance' | 'occupancy'>('occupancy');
  viewMode$ = new BehaviorSubject<CameraViewMode>({ mode: 'multi', gridSize: 4 });
  fullScreenCameraId$ = new BehaviorSubject<number | null>(null);
  
  isLoading$ = new BehaviorSubject<boolean>(false);
  currentUser$ = new BehaviorSubject<any>({ role: 'security', name: 'Security Operator' });

  // ========================================================================
  // EVENTS & ACTIVITY FEED
  // ========================================================================

  events$ = new BehaviorSubject<DashboardEvent[]>([]);
  private eventQueue: DashboardEvent[] = [];
  maxEventsInFeed = 50;

  // ========================================================================
  // METRICS
  // ========================================================================

  metrics$ = new BehaviorSubject<MetricData[]>([
    {
      label: 'Live Occupancy',
      value: 0,
      unit: 'people',
      color: 'cyan',
      sparklineData: []
    },
    {
      label: 'PPE Compliance',
      value: 0,
      unit: '%',
      color: 'emerald',
      sparklineData: []
    },
    {
      label: 'Active Alerts',
      value: 0,
      unit: 'alerts',
      color: 'rose',
      sparklineData: []
    },
    {
      label: 'System Health',
      value: 100,
      unit: '%',
      color: 'cyan',
      sparklineData: []
    }
  ]);

  // ========================================================================
  // MODAL & FORM STATE
  // ========================================================================

  showOverrideModal$ = new BehaviorSubject<boolean>(false);
  overrideEmployee$ = new BehaviorSubject<any>(null);
  overrideFormData = {
    employee_id: 0,
    attendance_date: new Date().toISOString().split('T')[0],
    check_in_time: '',
    check_out_time: '',
    status: 'PRESENT',
    reason: '',
    override_user: this.currentUser$.value.name
  };

  // ========================================================================
  // CAMERA & TIMELINE
  // ========================================================================

  cameras$ = new BehaviorSubject<any[]>([]);
  selectedCameras$ = new BehaviorSubject<number[]>([]);
  
  // For single camera mode
  selectedCameraDetails$ = new BehaviorSubject<any>(null);
  cameraLiveData$ = new BehaviorSubject<any>(null);

  // ========================================================================
  // REAL-TIME STREAMS (Observable subscriptions)
  // ========================================================================

  occupancyData$: Observable<any> = new Observable();
  vehicleData$: Observable<any> = new Observable();
  attendanceData$: Observable<any> = new Observable();
  identityData$: Observable<any> = new Observable();

  constructor(
    private occupancyService: OccupancyService,
    private vehicleService: VehicleService,
    private identityService: IdentityService,
    private attendanceService: AttendanceService
  ) {
    this.setupRealTimeStreams();
  }

  ngOnInit(): void {
    this.loadInitialData();
    this.setupEventListeners();
    this.startMetricsRefresh();
  }

  // ========================================================================
  // INITIALIZATION
  // ========================================================================

  private setupRealTimeStreams(): void {
    // Module 4: Occupancy (real-time 5s updates)
    this.occupancyData$ = this.occupancyService.facilityOccupancy$.pipe(
      tap(occupancy => {
        if (occupancy) {
          this.updateMetric('Live Occupancy', occupancy.total_occupancy);
          this.addEvent({
            id: `occupancy-${Date.now()}`,
            type: 'OCCUPANCY',
            severity: occupancy.overall_percentage > 85 ? 'WARNING' : 'INFO',
            timestamp: new Date(),
            title: `Occupancy: ${occupancy.overall_percentage}%`,
            description: `${occupancy.total_occupancy}/${occupancy.total_capacity} people`,
            icon: 'users'
          });
        }
      })
    );

    // Module 2: Vehicle (real-time detections)
    this.vehicleData$ = this.vehicleService.vehicleDetections$.pipe(
      tap(detection => {
        if (detection) {
          this.addEvent({
            id: `vehicle-${detection.frame_index}`,
            type: 'VEHICLE',
            severity: detection.alerts_triggered > 0 ? 'CRITICAL' : 'INFO',
            timestamp: new Date(),
            title: `Vehicles Detected: ${detection.vehicles_detected}`,
            description: `Plates: ${detection.plates_recognized}, Alerts: ${detection.alerts_triggered}`,
            icon: 'vehicle'
          });
        }
      })
    );

    // Module 1: Identity (real-time identifications)
    this.identityData$ = this.identityService.identities$.pipe(
      tap(identities => {
        if (identities && identities.length > 0) {
          identities.forEach(identity => {
            this.addEvent({
              id: `identity-${identity.track_id}-${Date.now()}`,
              type: 'IDENTITY',
              severity: identity.is_authorized ? 'INFO' : 'WARNING',
              timestamp: new Date(),
              title: identity.is_authorized ? `✓ ${identity.name}` : `? Unknown Person`,
              description: `Confidence: ${(identity.confidence * 100).toFixed(1)}%`,
              icon: 'user-check'
            });
          });
        }
      })
    );

    // Module 3: Attendance (real-time check-ins)
    this.attendanceData$ = this.attendanceService.attendanceRecords$.pipe(
      tap(records => {
        if (records && records.length > 0) {
          const latestRecord = records[0];
          this.addEvent({
            id: `attendance-${latestRecord.id}`,
            type: 'ATTENDANCE',
            severity: latestRecord.is_late ? 'WARNING' : 'INFO',
            timestamp: new Date(latestRecord.check_in_time || ''),
            title: `${latestRecord.employee_name} - ${latestRecord.is_late ? 'LATE' : 'ON TIME'}`,
            description: `Check-in: ${new Date(latestRecord.check_in_time || '').toLocaleTimeString()}`,
            icon: 'clock'
          });
        }
      })
    );
  }

  private loadInitialData(): void {
    this.isLoading$.next(true);
    
    // Load cameras
    this.occupancyService.listCameras().subscribe(cameras => {
      this.cameras$.next(cameras);
      if (cameras.length > 0) {
        this.selectedCameras$.next([cameras[0].id]);
        this.loadCameraData(cameras[0].id);
      }
      this.isLoading$.next(false);
    });

    // Load initial metrics
    combineLatest([
      this.occupancyService.getFacilityStats(),
      this.occupancyService.getAlerts()
    ]).subscribe(([stats, alerts]) => {
      if (stats) {
        this.updateMetric('Live Occupancy', stats.current_occupancy);
        this.updateMetric('System Health', 100);
      }
      if (alerts) {
        this.updateMetric('Active Alerts', alerts.filter(a => !a.is_resolved).length);
      }
    });
  }

  private setupEventListeners(): void {
    // Listen for critical alerts
    this.occupancyService.alerts$.subscribe(alerts => {
      const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL' && !a.is_resolved);
      criticalAlerts.forEach(alert => {
        this.addEvent({
          id: `alert-${alert.id}`,
          type: 'ALERT',
          severity: 'CRITICAL',
          timestamp: new Date(alert.timestamp),
          title: `🚨 ${alert.alert_type}`,
          description: alert.message,
          icon: 'alert-triangle'
        });
      });
    });

    // Listen for vehicle alerts
    this.vehicleService.alerts$.subscribe(alerts => {
      alerts.forEach(alert => {
        this.addEvent({
          id: `vehicle-alert-${alert.track_id}`,
          type: 'ALERT',
          severity: alert.alert_type === 'UNKNOWN_VEHICLE' ? 'WARNING' : 'INFO',
          timestamp: new Date(alert.timestamp),
          title: `🚗 ${alert.alert_type}`,
          description: `Plate: ${alert.plate_number}`,
          icon: 'alert-circle'
        });
      });
    });
  }

  private startMetricsRefresh(): void {
    // Refresh metrics every 30 seconds
    interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.occupancyService.getFacilityStats())
      )
      .subscribe(stats => {
        if (stats) {
          this.updateMetric('Live Occupancy', stats.current_occupancy);
          this.updateMetric('System Health', 100 - (stats.areas_by_density.critical * 10));
        }
      });
  }

  // ========================================================================
  // EVENT MANAGEMENT
  // ========================================================================

  private addEvent(event: DashboardEvent): void {
    this.eventQueue.unshift(event);
    if (this.eventQueue.length > this.maxEventsInFeed) {
      this.eventQueue.pop();
    }
    this.events$.next([...this.eventQueue]);
  }

  clearEvents(): void {
    this.eventQueue = [];
    this.events$.next([]);
  }

  // ========================================================================
  // METRICS MANAGEMENT
  // ========================================================================

  private updateMetric(label: string, value: number): void {
    const metrics = this.metrics$.value;
    const metricIndex = metrics.findIndex(m => m.label === label);
    if (metricIndex !== -1) {
      const oldValue = metrics[metricIndex].value;
      metrics[metricIndex].value = value;
      metrics[metricIndex].trend = value > oldValue ? 'up' : value < oldValue ? 'down' : 'stable';
      
      // Update sparkline
      if (!metrics[metricIndex].sparklineData) {
        metrics[metricIndex].sparklineData = [];
      }
      metrics[metricIndex].sparklineData?.push(value);
      if (metrics[metricIndex].sparklineData!.length > 24) {
        metrics[metricIndex].sparklineData?.shift();
      }
      
      this.metrics$.next([...metrics]);
    }
  }

  // ========================================================================
  // CAMERA MANAGEMENT
  // ========================================================================

  loadCameraData(cameraId: number): void {
    this.occupancyService.getLiveCameraOccupancy(cameraId).subscribe(occupancy => {
      this.selectedCameraDetails$.next(occupancy);
    });

    this.occupancyService.getCameraOccupancyLogs(cameraId, 10).subscribe(logs => {
      this.cameraLiveData$.next(logs);
    });
  }

  selectCamera(cameraId: number): void {
    if (this.viewMode$.value.mode === 'single') {
      this.loadCameraData(cameraId);
    } else {
      const selected = this.selectedCameras$.value;
      if (selected.includes(cameraId)) {
        this.selectedCameras$.next(selected.filter(id => id !== cameraId));
      } else {
        this.selectedCameras$.next([...selected, cameraId]);
      }
    }
  }

  toggleViewMode(): void {
    const currentMode = this.viewMode$.value;
    if (currentMode.mode === 'single') {
      this.viewMode$.next({ mode: 'multi', gridSize: 4 });
    } else {
      this.viewMode$.next({ mode: 'single' });
    }
  }

  // ========================================================================
  // MANUAL OVERRIDE MODAL
  // ========================================================================

  openOverrideModal(employeeId?: string): void {
    if (employeeId) {
      this.overrideFormData.employee_id = parseInt(employeeId);
      this.identityService.getEmployee(parseInt(employeeId)).subscribe(employee => {
        this.overrideEmployee$.next(employee);
      });
    }
    this.showOverrideModal$.next(true);
  }

  closeOverrideModal(): void {
    this.showOverrideModal$.next(false);
  }

  submitOverride(): void {
    if (!this.overrideFormData.employee_id) {
      alert('Please select an employee');
      return;
    }

    this.attendanceService.createOverride(this.overrideFormData).subscribe(
      (result) => {
        this.addEvent({
          id: `override-${Date.now()}`,
          type: 'ATTENDANCE',
          severity: 'INFO',
          timestamp: new Date(),
          title: '✓ Manual Override Applied',
          description: `Employee ID: ${this.overrideFormData.employee_id}`,
          icon: 'check-circle'
        });
        this.closeOverrideModal();
        this.resetOverrideForm();
      },
      (error) => {
        alert('Error: ' + error.message);
      }
    );
  }

  private resetOverrideForm(): void {
    this.overrideFormData = {
      employee_id: 0,
      attendance_date: new Date().toISOString().split('T')[0],
      check_in_time: '',
      check_out_time: '',
      status: 'PRESENT',
      reason: '',
      override_user: this.currentUser$.value.name
    };
  }

  // ========================================================================
  // MODULE NAVIGATION
  // ========================================================================

  switchModule(module: 'identity' | 'vehicles' | 'attendance' | 'occupancy'): void {
    this.activeModule$.next(module);
  }

  toggleSidebar(): void {
    this.sidebarOpen$.next(!this.sidebarOpen$.value);
  }

  // ========================================================================
  // EXPORT & REPORTING
  // ========================================================================

  exportReport(format: 'pdf' | 'excel'): void {
    const metrics = this.metrics$.value;
    const events = this.events$.value;
    
    const reportData = {
      timestamp: new Date().toISOString(),
      metrics: metrics.map(m => ({ label: m.label, value: m.value, unit: m.unit })),
      events: events.slice(0, 20).map(e => ({
        type: e.type,
        title: e.title,
        timestamp: e.timestamp.toISOString()
      }))
    };

    if (format === 'pdf') {
      this.exportToPDF(reportData);
    } else {
      this.exportToExcel(reportData);
    }
  }

  private exportToPDF(data: any): void {
    // Implementation would use a library like pdfmake or jsPDF
    console.log('Exporting to PDF:', data);
    // TODO: Implement PDF export
  }

  private exportToExcel(data: any): void {
    // Implementation would use a library like xlsx
    console.log('Exporting to Excel:', data);
    // TODO: Implement Excel export
  }

  // ========================================================================
  // RESPONSIVE DESIGN
  // ========================================================================

  @HostListener('window:resize', ['$event'])
  onResize(event: any): void {
    const width = window.innerWidth;
    // Adjust grid size based on screen width
    if (width < 1440) {
      this.viewMode$.next({ ...this.viewMode$.value, gridSize: 2 });
    } else if (width < 1920) {
      this.viewMode$.next({ ...this.viewMode$.value, gridSize: 4 });
    } else {
      this.viewMode$.next({ ...this.viewMode$.value, gridSize: 6 });
    }
  }

  // ========================================================================
  // UTILITY METHODS
  // ========================================================================

  getTrendIcon(trend?: string): string {
    switch (trend) {
      case 'up': return '↑';
      case 'down': return '↓';
      default: return '→';
    }
  }

  getTrendColor(trend?: string): string {
    switch (trend) {
      case 'up': return 'text-emerald-400';
      case 'down': return 'text-rose-400';
      default: return 'text-cyan-400';
    }
  }

  formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  formatDate(date: Date): string {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
}
