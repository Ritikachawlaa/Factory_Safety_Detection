import { Component, OnInit, OnDestroy, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';
import { LoiteringService, LoiteringStatus } from '../../services/loitering.service';
import { ViolationService, LoiteringViolation } from '../../services/violation.service';
import { FrameLimiter, RECOMMENDED_FPS } from '../../utils/frame-limiter';

@Component({
  selector: 'app-loitering-detection',
  templateUrl: './loitering-detection.component.html',
  styleUrls: ['./loitering-detection.component.css']
})


export class LoiteringDetectionComponent implements OnInit, OnDestroy {
  // Injected services
  private violationService = inject(ViolationService);

  // Signals for violation management
  violations = this.violationService.loiteringViolations;
  showResolveModal = signal(false);
  selectedViolation = signal<LoiteringViolation | null>(null);
  resolutionNotes = signal('');
  resolvedBy = signal('');

  // Computed signals
  activeViolations = computed(() => 
    this.violations().filter(v => v.status === 'active')
  );

  loiteringData: LoiteringStatus = { activeGroups: 0 };
  lastDetection: any = null;
  
  // Configuration properties
  timeThreshold: number = 10;  // Default 10 seconds
  distanceThreshold: number = 150;  // Default 150 pixels
  
  private subscription?: Subscription;

  constructor(private loiteringService: LoiteringService) {}

  ngOnInit(): void {
    // Load today's violations
    this.loadViolations();
    
    // Load current configuration
    this.loadLoiteringConfig();
    
    this.subscription = this.loiteringService.getLoiteringStats().subscribe(
      (data: any) => this.loiteringData = data,
      (error: any) => console.error('Error:', error)
    );
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  // ============================================================================
  // VIOLATION MANAGEMENT METHODS
  // ============================================================================

  /**
   * Load today's loitering violations
   */
  loadViolations(): void {
    const today = new Date().toISOString().split('T')[0];
    this.violationService.loadLoiteringViolations(today);
  }

  /**
   * Format date-time for display
   */
  formatDateTime(timestamp: string): string {
    return new Date(timestamp).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  /**
   * Open resolve modal for a violation
   */
  openResolveModal(violation: LoiteringViolation): void {
    this.selectedViolation.set(violation);
    this.resolutionNotes.set('');
    this.resolvedBy.set('');
    this.showResolveModal.set(true);
  }

  /**
   * Close resolve modal
   */
  closeResolveModal(): void {
    this.showResolveModal.set(false);
    this.selectedViolation.set(null);
    this.resolutionNotes.set('');
    this.resolvedBy.set('');
  }

  /**
   * Resolve the selected violation
   */
  resolveViolation(): void {
    const violation = this.selectedViolation();
    const notes = this.resolutionNotes();
    const by = this.resolvedBy();
    
    if (!violation || !notes || !by) return;
    
    this.violationService.resolveLoiteringViolation(violation.id, notes, by).subscribe({
      next: () => {
        alert('✅ Violation resolved successfully!');
        this.closeResolveModal();
      },
      error: (err) => {
        alert('❌ Failed to resolve violation: ' + err.message);
      }
    });
  }

  // ============================================================================
  // CONFIGURATION MANAGEMENT METHODS
  // ============================================================================

  /**
   * Load current loitering detection configuration
   */
  loadLoiteringConfig(): void {
    this.loiteringService.getLoiteringConfig().subscribe({
      next: (config: any) => {
        this.timeThreshold = config.time_threshold || 10;
        this.distanceThreshold = config.distance_threshold || 150;
      },
      error: (err) => {
        console.error('Failed to load loitering config:', err);
      }
    });
  }

  /**
   * Update loitering configuration (called on input change)
   */
  updateLoiteringConfig(): void {
    // Input validation
    if (this.timeThreshold < 1) this.timeThreshold = 1;
    if (this.timeThreshold > 60) this.timeThreshold = 60;
    if (this.distanceThreshold < 50) this.distanceThreshold = 50;
    if (this.distanceThreshold > 300) this.distanceThreshold = 300;
  }

  /**
   * Save loitering configuration to backend
   */
  saveLoiteringConfig(): void {
    this.loiteringService.updateLoiteringConfig(this.timeThreshold, this.distanceThreshold).subscribe({
      next: (response: any) => {
        alert('✅ Configuration saved successfully!');
        console.log('Config updated:', response);
      },
      error: (err) => {
        alert('❌ Failed to save configuration: ' + err.message);
        console.error('Config update error:', err);
      }
    });
  }
}
