import { Component, Input, OnInit } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';

// ============================================================================
// TYPES
// ============================================================================

export interface MetricScorecard {
  id: string;
  title: string;
  value: number | string;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  trendPercent?: number;
  color: 'cyan' | 'emerald' | 'rose' | 'amber' | 'purple';
  category: 'occupancy' | 'ppeCompliance' | 'alerts' | 'systemHealth' | 'vehicle' | 'attendance';
  icon: string; // SVG icon name
  sparklineData?: number[];
  lastUpdated?: Date;
  warning?: boolean;
  critical?: boolean;
}

// ============================================================================
// METRIC SCORECARD COMPONENT
// ============================================================================

@Component({
  selector: 'app-metric-scorecard',
  template: `
    <div 
      [class]="getCardClass()"
      class="rounded-lg p-4 border backdrop-blur-sm transition-all duration-300 hover:shadow-lg">
      
      <!-- Header -->
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center gap-3 flex-1">
          <!-- Icon -->
          <div [class]="getIconBackgroundClass()" class="p-2 rounded-lg">
            <svg [class]="getIconColorClass()" class="w-5 h-5" [innerHTML]="getIcon()" (click)="$event.preventDefault()"></svg>
          </div>

          <!-- Title & Category -->
          <div>
            <h3 class="text-xs font-semibold text-slate-300">{{ metric.title }}</h3>
            <p class="text-xs text-slate-500 mt-0.5">{{ metric.category }}</p>
          </div>
        </div>

        <!-- Status Badge -->
        <div *ngIf="metric.critical" class="px-2 py-1 bg-rose-900 text-rose-200 text-xs rounded font-mono">
          CRIT
        </div>
        <div *ngIf="metric.warning && !metric.critical" class="px-2 py-1 bg-amber-900 text-amber-200 text-xs rounded font-mono">
          WARN
        </div>
      </div>

      <!-- Value -->
      <div class="mb-3">
        <div class="text-3xl font-bold" [class]="getValueColorClass()">
          {{ formatValue(metric.value) }}<span class="text-sm text-slate-400 ml-1">{{ metric.unit }}</span>
        </div>

        <!-- Trend -->
        <div *ngIf="metric.trend" class="flex items-center gap-2 mt-2">
          <svg 
            [class]="getTrendColorClass()"
            class="w-4 h-4"
            [class.rotate-180]="metric.trend === 'down'"
            fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M3 10a1 1 0 011-1h5V5a1 1 0 011-1 1 1 0 01.82.45l8 12A1 1 0 0115 20H4a1 1 0 01-.82-1.45l8-12z" clip-rule="evenodd" />
          </svg>
          <span [class]="getTrendColorClass()" class="text-sm font-mono">
            {{ metric.trendPercent ? (metric.trendPercent > 0 ? '+' : '') + metric.trendPercent + '%' : metric.trend.toUpperCase() }}
          </span>
        </div>
      </div>

      <!-- Sparkline Chart -->
      <div *ngIf="metric.sparklineData && metric.sparklineData.length > 0" class="mb-3">
        <div class="h-10 flex items-end gap-0.5">
          <canvas 
            #sparklineCanvas
            class="w-full h-full">
          </canvas>
        </div>
      </div>

      <!-- Time -->
      <div class="text-xs text-slate-500 border-t border-slate-700 pt-3">
        Updated {{ getTimeAgo(metric.lastUpdated) }}
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class MetricScorecardComponent implements OnInit {
  @Input() metric!: MetricScorecard;

  ngOnInit(): void {
    if (this.metric.sparklineData) {
      this.drawSparkline();
    }
  }

  getCardClass(): string {
    let base = 'bg-slate-800 border-slate-700';
    
    if (this.metric.critical) {
      base = 'bg-rose-900 bg-opacity-20 border-rose-700';
    } else if (this.metric.warning) {
      base = 'bg-amber-900 bg-opacity-20 border-amber-700';
    }

    return base;
  }

  getIconBackgroundClass(): string {
    const classes: { [key: string]: string } = {
      cyan: 'bg-cyan-900 bg-opacity-30',
      emerald: 'bg-emerald-900 bg-opacity-30',
      rose: 'bg-rose-900 bg-opacity-30',
      amber: 'bg-amber-900 bg-opacity-30',
      purple: 'bg-purple-900 bg-opacity-30'
    };
    return classes[this.metric.color] || classes['cyan'];
  }

  getIconColorClass(): string {
    const classes: { [key: string]: string } = {
      cyan: 'text-cyan-400',
      emerald: 'text-emerald-400',
      rose: 'text-rose-400',
      amber: 'text-amber-400',
      purple: 'text-purple-400'
    };
    return classes[this.metric.color] || classes['cyan'];
  }

  getValueColorClass(): string {
    const classes: { [key: string]: string } = {
      cyan: 'text-cyan-400',
      emerald: 'text-emerald-400',
      rose: 'text-rose-400',
      amber: 'text-amber-400',
      purple: 'text-purple-400'
    };
    return classes[this.metric.color] || classes['cyan'];
  }

  getTrendColorClass(): string {
    if (!this.metric.trend) return 'text-slate-400';
    
    if (this.metric.trend === 'up') {
      return this.metric.category === 'alerts' || this.metric.category === 'systemHealth' 
        ? 'text-rose-400' // up is bad for alerts/health
        : 'text-emerald-400'; // up is good
    } else if (this.metric.trend === 'down') {
      return this.metric.category === 'alerts' || this.metric.category === 'systemHealth'
        ? 'text-emerald-400' // down is good for alerts/health
        : 'text-rose-400'; // down is bad
    }
    
    return 'text-slate-400';
  }

  getIcon(): string {
    const icons: { [key: string]: string } = {
      occupancy: `<path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />`,
      ppeCompliance: `<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />`,
      alerts: `<path d="M13 10V3L4 14h7v7l9-11h-7z" />`,
      systemHealth: `<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`,
      vehicle: `<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`,
      attendance: `<path d="M9 12l2 2 4-4M7 20H5a2 2 0 01-2-2V9.414a1 1 0 00-.293-.707l-2-2A1 1 0 015 5h8a1 1 0 01.707.293l2 2A1 1 0 0116 9.414V18a2 2 0 01-2 2h-5m-3-5h6" />`
    };
    return icons[this.metric.category] || icons['occupancy'];
  }

  formatValue(value: number | string): string {
    if (typeof value === 'string') return value;
    if (value >= 1000) return (value / 1000).toFixed(1) + 'k';
    return Math.round(value).toString();
  }

  getTimeAgo(date?: Date): string {
    if (!date) return 'Just now';
    
    const now = new Date();
    const diff = (now.getTime() - date.getTime()) / 1000;

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  }

  private drawSparkline(): void {
    // This will be called from template via ViewChild
    // Implementation uses canvas for high-performance sparkline rendering
    setTimeout(() => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (!canvas || !this.metric.sparklineData) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;

      const data = this.metric.sparklineData;
      const min = Math.min(...data);
      const max = Math.max(...data);
      const range = max - min || 1;

      const width = canvas.width;
      const height = canvas.height;
      const padding = 4;

      // Draw background
      ctx.fillStyle = 'rgba(6, 182, 212, 0.1)';
      ctx.fillRect(0, 0, width, height);

      // Draw line
      ctx.strokeStyle = this.getSparklineColor();
      ctx.lineWidth = 2;
      ctx.beginPath();

      data.forEach((value, index) => {
        const x = (index / (data.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((value - min) / range) * (height - padding * 2);

        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();

      // Draw area
      ctx.fillStyle = this.getSparklineColor().replace(')', ', 0.2)').replace('rgb', 'rgba');
      ctx.lineTo(width - padding, height - padding);
      ctx.lineTo(padding, height - padding);
      ctx.closePath();
      ctx.fill();
    }, 0);
  }

  private getSparklineColor(): string {
    const colors: { [key: string]: string } = {
      cyan: 'rgb(6, 182, 212)',
      emerald: 'rgb(16, 185, 129)',
      rose: 'rgb(244, 63, 94)',
      amber: 'rgb(245, 158, 11)',
      purple: 'rgb(168, 85, 247)'
    };
    return colors[this.metric.color] || colors['cyan'];
  }
}

// ============================================================================
// METRIC CARD CONTAINER (displays multiple metrics)
// ============================================================================

@Component({
  selector: 'app-metrics-bar',
  template: `
    <div class="h-24 bg-slate-900 border-b border-slate-700 p-4 overflow-x-auto">
      <div class="flex gap-4 h-full">
        <app-metric-scorecard 
          *ngFor="let metric of metrics$ | async"
          [metric]="metric"
          class="flex-shrink-0 w-80">
        </app-metric-scorecard>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }

    /* Horizontal scrollbar */
    ::-webkit-scrollbar {
      height: 6px;
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
export class MetricsBarComponent {
  @Input() metrics$!: Observable<MetricScorecard[]>;
}
