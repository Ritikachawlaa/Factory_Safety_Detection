import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

// ============================================================================
// TYPES
// ============================================================================

export interface Toast {
  id: string;
  message: string;
  title?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number; // in ms, 0 = manual dismiss
  action?: {
    label: string;
    callback: () => void;
  };
}

// ============================================================================
// TOAST NOTIFICATION SERVICE
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class ToastNotificationService {
  
  private toasts$ = new BehaviorSubject<Toast[]>([]);
  private toastIdCounter = 0;

  /**
   * Get observable of all active toasts
   */
  getToasts(): Observable<Toast[]> {
    return this.toasts$.asObservable();
  }

  /**
   * Show a success toast
   */
  success(message: string, title?: string, duration: number = 3000): string {
    return this.show('success', message, title, duration);
  }

  /**
   * Show an error toast
   */
  error(message: string, title?: string, duration: number = 5000): string {
    return this.show('error', message, title, duration);
  }

  /**
   * Show a warning toast
   */
  warning(message: string, title?: string, duration: number = 4000): string {
    return this.show('warning', message, title, duration);
  }

  /**
   * Show an info toast
   */
  info(message: string, title?: string, duration: number = 3000): string {
    return this.show('info', message, title, duration);
  }

  /**
   * Show a critical alert (persistent)
   */
  critical(message: string, title?: string, action?: { label: string; callback: () => void }): string {
    return this.show('error', message, title || 'Critical Alert', 0, action);
  }

  /**
   * Show a custom toast
   */
  show(
    type: 'success' | 'error' | 'warning' | 'info',
    message: string,
    title?: string,
    duration?: number,
    action?: { label: string; callback: () => void }
  ): string {
    const id = `toast-${++this.toastIdCounter}`;

    const toast: Toast = {
      id,
      type,
      message,
      title,
      duration: duration ?? this.getDefaultDuration(type),
      action
    };

    // Add toast
    const toasts = this.toasts$.value;
    this.toasts$.next([...toasts, toast]);

    // Auto-dismiss if duration is set
    if (toast.duration && toast.duration > 0) {
      setTimeout(() => {
        this.dismiss(id);
      }, toast.duration);
    }

    return id;
  }

  /**
   * Dismiss a specific toast
   */
  dismiss(id: string): void {
    const toasts = this.toasts$.value.filter(t => t.id !== id);
    this.toasts$.next(toasts);
  }

  /**
   * Dismiss all toasts
   */
  dismissAll(): void {
    this.toasts$.next([]);
  }

  /**
   * Execute toast action and dismiss
   */
  executeAction(id: string): void {
    const toast = this.toasts$.value.find(t => t.id === id);
    if (toast?.action) {
      toast.action.callback();
    }
    this.dismiss(id);
  }

  private getDefaultDuration(type: string): number {
    switch (type) {
      case 'error':
        return 5000;
      case 'warning':
        return 4000;
      case 'info':
        return 3000;
      case 'success':
        return 3000;
      default:
        return 3000;
    }
  }
}

// ============================================================================
// TOAST NOTIFICATION COMPONENT
// ============================================================================

import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-toast-notification',
  template: `
    <div 
      [@toastAnimation]
      [class]="getToastClass()"
      class="flex gap-4 items-start p-4 rounded-lg border shadow-lg backdrop-blur-sm pointer-events-auto">
      
      <!-- Icon -->
      <div class="flex-shrink-0 mt-0.5">
        <svg 
          *ngIf="toast.type === 'success'"
          class="w-5 h-5 text-emerald-400"
          fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>

        <svg 
          *ngIf="toast.type === 'error'"
          class="w-5 h-5 text-rose-400"
          fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>

        <svg 
          *ngIf="toast.type === 'warning'"
          class="w-5 h-5 text-amber-400"
          fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>

        <svg 
          *ngIf="toast.type === 'info'"
          class="w-5 h-5 text-cyan-400"
          fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
      </div>

      <!-- Content -->
      <div class="flex-1">
        <div *ngIf="toast.title" class="font-semibold text-sm text-white">
          {{ toast.title }}
        </div>
        <div [class.text-slate-300]="toast.title" [class.text-white]="!toast.title" class="text-sm mt-0.5">
          {{ toast.message }}
        </div>
      </div>

      <!-- Action Button -->
      <div *ngIf="toast.action" class="flex-shrink-0">
        <button 
          (click)="onAction()"
          class="px-3 py-1 text-xs font-semibold rounded transition-colors"
          [ngClass]="getActionButtonClass()">
          {{ toast.action.label }}
        </button>
      </div>

      <!-- Close Button -->
      <button 
        (click)="onDismiss()"
        class="flex-shrink-0 text-slate-400 hover:text-slate-200 transition-colors">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class ToastNotificationComponent implements OnInit {
  @Input() toast!: Toast;

  constructor(private toastService: ToastNotificationService) {}

  ngOnInit(): void {
    // Lifecycle managed by service
  }

  getToastClass(): string {
    const base = 'border bg-slate-900 bg-opacity-95';
    
    const typeClasses: { [key: string]: string } = {
      success: 'border-emerald-500 bg-emerald-900 bg-opacity-20',
      error: 'border-rose-500 bg-rose-900 bg-opacity-20',
      warning: 'border-amber-500 bg-amber-900 bg-opacity-20',
      info: 'border-cyan-500 bg-cyan-900 bg-opacity-20'
    };

    return typeClasses[this.toast.type] || base;
  }

  getActionButtonClass(): string {
    const typeClasses: { [key: string]: string } = {
      success: 'bg-emerald-600 hover:bg-emerald-500 text-white',
      error: 'bg-rose-600 hover:bg-rose-500 text-white',
      warning: 'bg-amber-600 hover:bg-amber-500 text-white',
      info: 'bg-cyan-600 hover:bg-cyan-500 text-white'
    };

    return typeClasses[this.toast.type] || typeClasses.info;
  }

  onDismiss(): void {
    this.toastService.dismiss(this.toast.id);
  }

  onAction(): void {
    this.toastService.executeAction(this.toast.id);
  }
}

// ============================================================================
// TOAST CONTAINER (displays all toasts)
// ============================================================================

@Component({
  selector: 'app-toast-container',
  template: `
    <div class="fixed bottom-4 right-4 z-50 pointer-events-none space-y-3">
      <app-toast-notification 
        *ngFor="let toast of toasts$ | async"
        [toast]="toast">
      </app-toast-notification>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class ToastContainerComponent implements OnInit {
  toasts$: Observable<Toast[]>;

  constructor(private toastService: ToastNotificationService) {
    this.toasts$ = this.toastService.getToasts();
  }

  ngOnInit(): void {
    // Component setup
  }
}
