import { Component, computed, inject } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { AuthService } from './services/auth.service';
import { SocketService } from './services/socket.service';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Factory Safety Dashboard';
  showSidebar = false;
  isSidebarCollapsed = false;

  // Inject SocketService for global alert monitoring
  private socketService = inject(SocketService);
  
  // Global alert signals
  latestAlert = this.socketService.latestAlert;
  hasViolations = this.socketService.hasViolations;
  alertCount = this.socketService.alertCount;

  constructor(
    public authService: AuthService,
    private router: Router
  ) {
    // Check if we should show sidebar based on route
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.showSidebar = this.authService.isLoggedIn() && !this.router.url.includes('/login');
    });
  }

  toggleSidebar(): void {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }

  logout(): void {
    this.authService.logout();
  }

  /**
   * Dismiss the current global alert
   */
  dismissAlert(): void {
    if (this.latestAlert()) {
      this.socketService.clearAlert(this.latestAlert()!.id);
    }
  }

  /**
   * Clear all alerts
   */
  clearAllAlerts(): void {
    this.socketService.clearAllAlerts();
  }
}
