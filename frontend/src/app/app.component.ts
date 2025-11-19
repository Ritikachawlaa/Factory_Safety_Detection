import { Component, computed, inject } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { AuthService } from './services/auth.service';
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

  // WebSocket/SocketService removed. No global alert signals.

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

  // WebSocket/SocketService removed. No alert dismiss/clear methods.
}
