import { Component, Input, OnInit } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

// ============================================================================
// TYPES
// ============================================================================

export interface ActivityEvent {
  id: string;
  timestamp: Date;
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
  category: 'occupancy' | 'vehicle' | 'attendance' | 'identity' | 'system';
  metadata?: {
    cameraId?: string;
    cameraName?: string;
    personName?: string;
    personId?: string;
    vehiclePlate?: string;
    count?: number;
    location?: string;
    thumbnail?: string; // base64 or image url
  };
  read: boolean;
}

// ============================================================================
// ACTIVITY FEED COMPONENT
// ============================================================================

@Component({
  selector: 'app-activity-feed',
  template: `
    <div class="flex flex-col h-full bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      
      <!-- Header -->
      <div class="border-b border-slate-700 p-4 flex items-center justify-between sticky top-0 bg-slate-800 z-10">
        <div>
          <h3 class="text-sm font-bold text-white">Activity Feed</h3>
          <p class="text-xs text-slate-400 mt-1">Real-time events from all modules</p>
        </div>
        <div class="flex gap-2">
          <button 
            (click)="filterBySeverity('critical')"
            [class.text-rose-500]="selectedSeverity === 'critical'"
            class="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors">
            Critical
          </button>
          <button 
            (click)="filterBySeverity(null)"
            [class.text-cyan-500]="selectedSeverity === null"
            class="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors">
            All
          </button>
        </div>
      </div>

      <!-- Events List -->
      <div class="flex-1 overflow-y-auto">
        <div *ngIf="(filteredEvents$ | async) as events; else noEvents" class="divide-y divide-slate-700">
          
          <div 
            *ngFor="let event of events"
            [class.bg-slate-700 bg-opacity-50]="!event.read"
            class="p-3 hover:bg-slate-700 hover:bg-opacity-30 transition-colors cursor-pointer border-l-4 border-transparent"
            [ngClass]="getSeverityClass(event.severity)"
            (click)="markAsRead(event.id)">
            
            <!-- Timestamp -->
            <div class="text-xs text-slate-400 font-mono mb-1">
              {{ formatTime(event.timestamp) }}
            </div>

            <!-- Main Content (flex with thumbnail) -->
            <div class="flex gap-3">
              
              <!-- Thumbnail -->
              <div *ngIf="event.metadata?.thumbnail" class="flex-shrink-0 w-12 h-12 rounded overflow-hidden bg-slate-900 border border-slate-600">
                <img 
                  [src]="event.metadata.thumbnail"
                  alt="Event thumbnail"
                  class="w-full h-full object-cover">
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                
                <!-- Title -->
                <div class="text-sm font-semibold text-white flex items-center gap-2">
                  <svg 
                    *ngIf="!event.read"
                    class="w-2 h-2 bg-cyan-500 rounded-full flex-shrink-0"
                    viewBox="0 0 2 2">
                    <circle cx="1" cy="1" r="1" fill="currentColor" />
                  </svg>
                  {{ event.title }}
                  <span [class]="getSeverityBadgeClass(event.severity)" class="text-xs px-2 py-0.5 rounded font-mono flex-shrink-0">
                    {{ event.severity.toUpperCase() }}
                  </span>
                </div>

                <!-- Description -->
                <p class="text-xs text-slate-300 mt-1 line-clamp-2">
                  {{ event.description }}
                </p>

                <!-- Metadata -->
                <div *ngIf="event.metadata" class="text-xs text-slate-400 mt-2 grid grid-cols-2 gap-2">
                  <span *ngIf="event.metadata.cameraName">
                    <span class="text-slate-500">Camera:</span> {{ event.metadata.cameraName }}
                  </span>
                  <span *ngIf="event.metadata.personName">
                    <span class="text-slate-500">Person:</span> {{ event.metadata.personName }}
                  </span>
                  <span *ngIf="event.metadata.vehiclePlate">
                    <span class="text-slate-500">Plate:</span> {{ event.metadata.vehiclePlate }}
                  </span>
                  <span *ngIf="event.metadata.count !== undefined">
                    <span class="text-slate-500">Count:</span> {{ event.metadata.count }}
                  </span>
                </div>
              </div>

              <!-- Close/Actions -->
              <div class="flex-shrink-0 flex gap-1">
                <button 
                  (click)="dismissEvent($event, event.id)"
                  class="p-1 hover:bg-slate-600 rounded transition-colors text-slate-400 hover:text-slate-200">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                </button>
              </div>
            </div>
          </div>

        </div>

        <!-- No Events State -->
        <ng-template #noEvents>
          <div class="flex flex-col items-center justify-center h-full text-slate-400 p-4">
            <svg class="w-12 h-12 mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20"><path d="M5 13a3 3 0 105.119-1H7A1 1 0 005.5 11h3A3 3 0 005 13z" /></svg>
            <p class="text-sm">No activity yet</p>
            <p class="text-xs mt-1">Events will appear here as they occur</p>
          </div>
        </ng-template>
      </div>

      <!-- Footer Stats -->
      <div class="border-t border-slate-700 p-3 bg-slate-900 grid grid-cols-3 gap-3 text-xs">
        <div class="text-center">
          <div class="text-rose-400 font-bold">{{ criticalCount }}</div>
          <div class="text-slate-400">Critical</div>
        </div>
        <div class="text-center">
          <div class="text-amber-400 font-bold">{{ warningCount }}</div>
          <div class="text-slate-400">Warnings</div>
        </div>
        <div class="text-center">
          <div class="text-cyan-400 font-bold">{{ unreadCount }}</div>
          <div class="text-slate-400">Unread</div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
      width: 6px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: rgba(100, 116, 139, 0.5);
      border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: rgba(100, 116, 139, 0.7);
    }
  `]
})
export class ActivityFeedComponent implements OnInit {
  @Input() events$: Observable<ActivityEvent[]> = new BehaviorSubject<ActivityEvent[]>([]);

  selectedSeverity: 'critical' | null = null;
  filteredEvents$: Observable<ActivityEvent[]>;
  
  criticalCount = 0;
  warningCount = 0;
  unreadCount = 0;

  ngOnInit(): void {
    // Create filtered events stream
    this.filteredEvents$ = new Observable(observer => {
      const subscription = this.events$.subscribe(events => {
        const filtered = this.selectedSeverity 
          ? events.filter(e => e.severity === this.selectedSeverity)
          : events;
        
        // Update stats
        this.criticalCount = events.filter(e => e.severity === 'critical').length;
        this.warningCount = events.filter(e => e.severity === 'warning').length;
        this.unreadCount = events.filter(e => !e.read).length;

        observer.next(filtered);
      });
      return () => subscription.unsubscribe();
    });
  }

  filterBySeverity(severity: 'critical' | null): void {
    this.selectedSeverity = severity;
    // Trigger re-evaluation of filteredEvents$
    this.ngOnInit();
  }

  markAsRead(eventId: string): void {
    // TODO: Implement marking event as read (backend sync)
    console.log('Mark event as read:', eventId);
  }

  dismissEvent(event: Event, eventId: string): void {
    event.stopPropagation();
    // TODO: Implement event dismissal/removal
    console.log('Dismiss event:', eventId);
  }

  formatTime(date: Date): string {
    const now = new Date();
    const diff = (now.getTime() - date.getTime()) / 1000;

    if (diff < 60) {
      return `${Math.floor(diff)}s ago`;
    } else if (diff < 3600) {
      return `${Math.floor(diff / 60)}m ago`;
    } else if (diff < 86400) {
      return `${Math.floor(diff / 3600)}h ago`;
    } else {
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  }

  getSeverityClass(severity: string): string {
    const classes: { [key: string]: string } = {
      critical: 'border-l-rose-500 bg-rose-900 bg-opacity-10',
      warning: 'border-l-amber-500 bg-amber-900 bg-opacity-10',
      info: 'border-l-cyan-500 bg-cyan-900 bg-opacity-10',
      success: 'border-l-emerald-500 bg-emerald-900 bg-opacity-10'
    };
    return classes[severity] || classes.info;
  }

  getSeverityBadgeClass(severity: string): string {
    const classes: { [key: string]: string } = {
      critical: 'bg-rose-900 text-rose-200',
      warning: 'bg-amber-900 text-amber-200',
      info: 'bg-cyan-900 text-cyan-200',
      success: 'bg-emerald-900 text-emerald-200'
    };
    return classes[severity] || classes.info;
  }
}
