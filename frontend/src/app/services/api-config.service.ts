import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * Centralized API Configuration Service
 * Manages all API endpoints for the 4 modules
 * Provides a single source of truth for backend URL configuration
 */
@Injectable({
  providedIn: 'root'
})
export class ApiConfigService {
  private baseUrl: string;

  // ============================================================================
  // MODULE 1: IDENTITY & ACCESS INTELLIGENCE
  // ============================================================================
  readonly MODULE1_ENDPOINTS = {
    // Real-time processing
    processFrame: '/module1/process-frame',
    
    // Employee enrollment
    enroll: '/module1/enroll',
    
    // Employee management
    employees: '/module1/employees',
    getEmployee: (id: number) => `/module1/employees/${id}`,
    updateEmployee: (id: number) => `/module1/employees/${id}`,
    deleteEmployee: (id: number) => `/module1/employees/${id}`,
    
    // Access logs
    accessLogs: '/module1/access-logs',
    getAccessLog: (id: number) => `/module1/access-logs/${id}`,
    todayAccessLogs: '/module1/access-logs/today',
    
    // Face recognition
    searchFaces: '/module1/search-faces',
    getFaceDetails: (faceId: string) => `/module1/faces/${faceId}`,
    unknownFaces: '/module1/unknown-faces',
    
    // Reports
    statistics: '/module1/statistics',
    employeeDailyReport: (id: number) => `/module1/employees/${id}/daily-report`,
    employeeMonthlyReport: (id: number) => `/module1/employees/${id}/monthly-report`,
    
    // Health
    health: '/module1/health'
  };

  // ============================================================================
  // MODULE 2: VEHICLE & GATE MANAGEMENT
  // ============================================================================
  readonly MODULE2_ENDPOINTS = {
    // Real-time processing
    processFrame: '/module2/process-frame',
    
    // Vehicle registration
    registerVehicle: '/module2/vehicle/register',
    
    // Vehicle management
    vehicles: '/module2/vehicles',
    getVehicle: (id: number) => `/module2/vehicles/${id}`,
    updateVehicleStatus: (id: number) => `/module2/vehicles/${id}/status`,
    deleteVehicle: (id: number) => `/module2/vehicles/${id}`,
    
    // Access logs
    accessLogs: '/module2/access-logs',
    getAccessLog: (id: number) => `/module2/access-logs/${id}`,
    todayAccessLogs: '/module2/access-logs/today',
    vehicleAccessLogs: (id: number) => `/module2/vehicles/${id}/access-logs`,
    flagAccessLog: (id: number) => `/module2/access-logs/${id}/flag`,
    
    // Summaries
    dailySummary: '/module2/access-logs/daily-summary',
    monthlySummary: '/module2/access-logs/monthly-summary',
    
    // Alerts
    alerts: '/module2/alerts',
    
    // Statistics
    statistics: '/module2/statistics',
    
    // Health
    health: '/module2/health'
  };

  // ============================================================================
  // MODULE 3: ATTENDANCE TRACKING
  // ============================================================================
  readonly MODULE3_ENDPOINTS = {
    // Face detection & attendance
    processFaceDetection: '/module3/process-face-detection',
    
    // Manual override
    override: '/module3/override',
    
    // Attendance records
    getRecord: (id: number) => `/module3/record/${id}`,
    reports: '/module3/reports',
    employeeRecords: (id: number) => `/module3/employee/${id}/records`,
    
    // Reports
    employeeMonthlyReport: (id: number) => `/module3/employee/${id}/monthly-report`,
    
    // Summary
    summary: '/module3/summary',
    
    // Shifts
    shifts: '/module3/shifts',
    getShift: (id: number) => `/module3/shifts/${id}`,
    
    // Departments
    departments: '/module3/departments',
    getDepartment: (id: number) => `/module3/departments/${id}`,
    
    // Health
    health: '/module3/health'
  };

  // ============================================================================
  // MODULE 4: OCCUPANCY & SPACE MANAGEMENT
  // ============================================================================
  readonly MODULE4_ENDPOINTS = {
    // Cameras
    cameras: '/module4/cameras',
    getCamera: (id: number) => `/module4/cameras/${id}`,
    updateCamera: (id: number) => `/module4/cameras/${id}`,
    calibrateCamera: (id: number) => `/module4/cameras/${id}/calibrate`,
    
    // Virtual lines
    lines: '/module4/lines',
    getLine: (id: number) => `/module4/lines/${id}`,
    updateLine: (id: number) => `/module4/lines/${id}`,
    cameraLines: (cameraId: number) => `/module4/cameras/${cameraId}/lines`,
    
    // Live occupancy
    liveCamera: (cameraId: number) => `/module4/cameras/${cameraId}/live`,
    liveFacility: '/module4/facility/live',
    
    // Logs
    cameraLogs: (cameraId: number) => `/module4/cameras/${cameraId}/logs`,
    
    // Analytics
    hourlyOccupancy: (cameraId: number) => `/module4/cameras/${cameraId}/hourly`,
    dailyOccupancy: (cameraId: number) => `/module4/cameras/${cameraId}/daily`,
    monthlyOccupancy: (cameraId: number) => `/module4/cameras/${cameraId}/monthly`,
    
    // Alerts
    alerts: '/module4/alerts',
    resolveAlert: (alertId: number) => `/module4/alerts/${alertId}/resolve`,
    
    // Statistics
    facilityStats: '/module4/facility/stats',
    
    // Aggregation
    aggregate: '/module4/aggregate',
    
    // Health
    health: '/module4/health'
  };

  constructor() {
    this.baseUrl = environment.apiUrl || 'http://localhost:8000/api';
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Get full URL for an endpoint
   * @param endpoint Relative endpoint path
   * @returns Full URL
   */
  getUrl(endpoint: string): string {
    return `${this.baseUrl}${endpoint}`;
  }

  /**
   * Get base API URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Set custom base URL (useful for testing or multiple environments)
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  /**
   * Get module endpoints
   */
  getModuleEndpoints(module: 1 | 2 | 3 | 4) {
    switch (module) {
      case 1:
        return this.MODULE1_ENDPOINTS;
      case 2:
        return this.MODULE2_ENDPOINTS;
      case 3:
        return this.MODULE3_ENDPOINTS;
      case 4:
        return this.MODULE4_ENDPOINTS;
      default:
        throw new Error(`Unknown module: ${module}`);
    }
  }

  /**
   * Get all endpoints reference
   */
  getAllEndpoints() {
    return {
      module1: this.MODULE1_ENDPOINTS,
      module2: this.MODULE2_ENDPOINTS,
      module3: this.MODULE3_ENDPOINTS,
      module4: this.MODULE4_ENDPOINTS
    };
  }

  /**
   * Build query parameters
   */
  buildQueryParams(params: { [key: string]: any }): string {
    const queryParts: string[] = [];
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined) {
        queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
      }
    }
    return queryParts.length > 0 ? '?' + queryParts.join('&') : '';
  }

  /**
   * Check if backend is reachable
   */
  isBackendReachable(): Promise<boolean> {
    return fetch(`${this.baseUrl}/health`)
      .then(response => response.ok)
      .catch(() => false);
  }

  /**
   * Validate backend connection
   */
  validateConnection(): Promise<{ status: string; modules: string[] }> {
    return fetch(`${this.baseUrl}/health`)
      .then(response => response.json())
      .then(data => ({
        status: 'connected',
        modules: data.modules || []
      }))
      .catch(error => {
        throw new Error(`Backend connection failed: ${error.message}`);
      });
  }
}
