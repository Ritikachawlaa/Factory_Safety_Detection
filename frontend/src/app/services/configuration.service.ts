import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface ModuleConfig {
  module_name: string;
  display_name: string;
  is_enabled: boolean;
  settings: any;
  description?: string;
  updated_at?: string;
}

export interface SystemConfig {
  config_key: string;
  config_value: any;
  description?: string;
  updated_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConfigurationService {
  private moduleConfigUrl = `${environment.apiUrl}/config/modules/`;
  private systemConfigUrl = `${environment.apiUrl}/config/system/`;

  // BehaviorSubject to cache and share module configurations
  private modulesSubject = new BehaviorSubject<ModuleConfig[]>([]);
  public modules$ = this.modulesSubject.asObservable();

  constructor(private http: HttpClient) {
    // Load modules on service initialization
    this.loadModules();
  }

  // ============================================================================
  // MODULE CONFIGURATION METHODS
  // ============================================================================

  /**
   * Load all module configurations from backend
   */
  loadModules(): void {
    this.http.get<ModuleConfig[]>(this.moduleConfigUrl).subscribe({
      next: (modules) => {
        this.modulesSubject.next(modules);
      },
      error: (err) => {
        console.error('Failed to load module configurations:', err);
      }
    });
  }

  /**
   * Get all module configurations
   */
  getModules(): Observable<ModuleConfig[]> {
    return this.http.get<ModuleConfig[]>(this.moduleConfigUrl).pipe(
      tap(modules => this.modulesSubject.next(modules))
    );
  }

  /**
   * Get current cached modules
   */
  getCurrentModules(): ModuleConfig[] {
    return this.modulesSubject.value;
  }

  /**
   * Check if a specific module is enabled
   */
  isModuleEnabled(moduleName: string): boolean {
    const module = this.modulesSubject.value.find(m => m.module_name === moduleName);
    return module ? module.is_enabled : false;
  }

  /**
   * Update module configuration (enable/disable or update settings)
   */
  updateModule(config: Partial<ModuleConfig>): Observable<any> {
    return this.http.post<any>(this.moduleConfigUrl, config).pipe(
      tap(() => this.loadModules()) // Reload modules after update
    );
  }

  /**
   * Toggle module enabled/disabled state
   */
  toggleModule(moduleName: string, enabled: boolean): Observable<any> {
    return this.updateModule({
      module_name: moduleName,
      is_enabled: enabled
    });
  }

  // ============================================================================
  // SYSTEM CONFIGURATION METHODS
  // ============================================================================

  /**
   * Get all system configurations
   */
  getSystemConfigs(): Observable<SystemConfig[]> {
    return this.http.get<SystemConfig[]>(this.systemConfigUrl);
  }

  /**
   * Get a specific system configuration by key
   */
  getSystemConfig(key: string): Observable<SystemConfig> {
    return this.http.get<SystemConfig>(`${this.systemConfigUrl}?key=${key}`);
  }

  /**
   * Update or create a system configuration
   */
  updateSystemConfig(config: SystemConfig): Observable<any> {
    return this.http.post<any>(this.systemConfigUrl, config);
  }

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  /**
   * Get display name for a module
   */
  getModuleDisplayName(moduleName: string): string {
    const module = this.modulesSubject.value.find(m => m.module_name === moduleName);
    return module?.display_name || moduleName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Initialize default modules if not exist
   */
  initializeDefaultModules(): Observable<any[]> {
    const defaultModules = [
      {
        module_name: 'helmet_detection',
        display_name: '🪖 Helmet Detection',
        is_enabled: true,
        settings: {},
        description: 'Real-time helmet safety compliance monitoring'
      },
      {
        module_name: 'loitering_detection',
        display_name: '👥 Loitering Detection',
        is_enabled: true,
        settings: { time_threshold: 10, distance_threshold: 150 },
        description: 'Monitor and detect group formations and suspicious activity'
      },
      {
        module_name: 'production_counter',
        display_name: '📦 Production Counter',
        is_enabled: true,
        settings: {},
        description: 'Automated production counting and tracking'
      },
      {
        module_name: 'attendance_system',
        display_name: '✓ Attendance System',
        is_enabled: true,
        settings: {},
        description: 'Facial recognition-based attendance management'
      }
    ];

    const requests = defaultModules.map(module => this.updateModule(module));
    return this.http.get<any[]>(this.moduleConfigUrl); // Return all modules after initialization
  }
}
