import { Component, computed, inject, signal, OnDestroy } from '@angular/core';

// Define the alert type expected by the template
type DashboardAlert = {
  id: string;
  module: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
};
import { ConfigurationService, ModuleConfig } from '../../services/configuration.service';
import { DashboardService } from '../../services/dashboard.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnDestroy {
  // Inject the centralized Socket Service
  private configService = inject(ConfigurationService);
  private dashboardService = inject(DashboardService);
  private pollingInterval: any;

  // Module configuration
  modules = signal<ModuleConfig[]>([]);
  showModuleSettings = signal(false);
  // Expose Object to template
  Object = Object;

  // --- Dummy data for dashboard (replace with HTTP polling if needed) ---
  helmetData = signal({ totalPeople: 0, compliantCount: 0, violationCount: 0 });
  loiteringData = signal({ activeGroups: 0 });
  productionData = signal({ itemCount: 0, itemsPerMinute: 0 });
  attendanceData = signal({ verifiedCount: 0, lastPersonSeen: '---' });
  // Provide a correct type for alerts
  criticalAlerts = signal<DashboardAlert[]>([]);
  latestAlert = computed(() => this.criticalAlerts()[0] || null);
  connectionStatus = signal('disconnected');
  isConnected = signal(false);

  // ============================================================================
  // COMPUTED SIGNALS (Derived data - auto-recalculates)
  // ============================================================================

  /**
   * Helmet compliance rate (0-100%)
   */
  helmetComplianceRate = computed(() => {
    const data = this.helmetData();
    if (!data.totalPeople) return 100;
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
    // No-op: WebSocket removed. Implement HTTP alert clearing if needed.
  }

  clearAllAlerts(): void {
    // No-op: WebSocket removed. Implement HTTP alert clearing if needed.
  }

  refreshData(): void {
    // No-op: WebSocket removed. Implement HTTP polling if needed.
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
    this.startPolling();
  }

  ngOnDestroy(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  }

  startPolling(): void {
    // Poll every 5 seconds
    this.fetchDashboardSummary();
    this.pollingInterval = setInterval(() => {
      this.fetchDashboardSummary();
    }, 5000);
  }

  fetchDashboardSummary(): void {
    this.dashboardService.getDashboardSummary().subscribe({
      next: (summary) => {
        // Update signals with summary data
        this.helmetData.set({
          totalPeople: summary.helmet_violations + summary.attendance.present, // Dummy logic for demo
          compliantCount: summary.attendance.present,
          violationCount: summary.helmet_violations
        });
        this.loiteringData.set({
          activeGroups: summary.loitering_alerts
        });
        this.productionData.set({
          itemCount: summary.production_count,
          itemsPerMinute: 0 // Not available in summary
        });
        this.attendanceData.set({
          verifiedCount: summary.attendance.present,
          lastPersonSeen: '---' // Not available in summary
        });
      },
      error: (err) => {
        console.error('Failed to fetch dashboard summary:', err);
      }
    });
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
