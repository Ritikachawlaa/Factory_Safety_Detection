import { Component, computed, inject, signal } from '@angular/core';
import { SocketService } from '../../services/socket.service';
import { ConfigurationService, ModuleConfig } from '../../services/configuration.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  // Inject the centralized Socket Service
  private socketService = inject(SocketService);
  private configService = inject(ConfigurationService);

  // Module configuration
  modules = signal<ModuleConfig[]>([]);
  showModuleSettings = signal(false);
  
  // Expose Object to template
  Object = Object;

  // ============================================================================
  // SIGNAL-BASED DATA (Auto-updates from WebSocket)
  // ============================================================================

  // Direct access to real-time data Signals
  helmetData = this.socketService.helmetData;
  loiteringData = this.socketService.loiteringData;
  productionData = this.socketService.productionData;
  attendanceData = this.socketService.attendanceData;
  
  // Critical alerts for the banner
  criticalAlerts = this.socketService.criticalAlerts;
  latestAlert = this.socketService.latestAlert;
  
  // Connection status
  connectionStatus = this.socketService.connectionStatus;
  isConnected = this.socketService.isConnected;

  // ============================================================================
  // COMPUTED SIGNALS (Derived data - auto-recalculates)
  // ============================================================================

  /**
   * Helmet compliance rate (0-100%)
   */
  helmetComplianceRate = computed(() => {
    const data = this.helmetData();
    if (data.totalPeople === 0) return 100;
    return Math.round((data.compliantCount / data.totalPeople) * 100);
  });

  /**
   * System health status
   */
  systemHealth = computed(() => {
    if (!this.isConnected()) return 'error';
    if (this.criticalAlerts().length > 0) return 'warning';
    return 'healthy';
  });

  /**
   * Has any violations?
   */
  hasViolations = computed(() => 
    this.helmetData().violationCount > 0 || 
    this.loiteringData().activeGroups > 0
  );

  /**
   * Total alerts count
   */
  totalAlerts = computed(() => this.criticalAlerts().length);

  // ============================================================================
  // METHODS
  // ============================================================================

  /**
   * Clear a specific alert
   */
  clearAlert(alertId: string): void {
    this.socketService.clearAlert(alertId);
  }

  /**
   * Clear all alerts
   */
  clearAllAlerts(): void {
    this.socketService.clearAllAlerts();
  }

  /**
   * Manually refresh all data
   */
  refreshData(): void {
    this.socketService.requestAllUpdates();
  }

  /**
   * Get status badge color
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }

  /**
   * Get alert icon based on severity
   */
  getAlertIcon(severity: 'critical' | 'warning' | 'info'): string {
    switch (severity) {
      case 'critical':
        return '🚨';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  }

  // ============================================================================
  // MODULE CONFIGURATION METHODS
  // ============================================================================

  ngOnInit(): void {
    this.loadModules();
  }

  /**
   * Load module configurations
   */
  loadModules(): void {
    this.configService.getModules().subscribe({
      next: (modules) => {
        this.modules.set(modules);
      },
      error: (err) => {
        console.error('Failed to load modules:', err);
      }
    });
  }

  /**
   * Toggle module settings panel
   */
  toggleModuleSettings(): void {
    this.showModuleSettings.set(!this.showModuleSettings());
  }

  /**
   * Toggle a module on/off
   */
  toggleModule(moduleName: string, enabled: boolean): void {
    this.configService.toggleModule(moduleName, enabled).subscribe({
      next: (response) => {
        console.log('Module toggled:', response);
        this.loadModules(); // Reload modules
        alert(`✅ Module ${enabled ? 'enabled' : 'disabled'} successfully!`);
      },
      error: (err) => {
        console.error('Failed to toggle module:', err);
        alert('❌ Failed to update module status');
      }
    });
  }

  /**
   * Check if a module is enabled
   */
  isModuleEnabled(moduleName: string): boolean {
    const module = this.modules().find(m => m.module_name === moduleName);
    return module?.is_enabled || false;
  }
}
