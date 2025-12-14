import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'AI Video Analytics System';

  constructor(private router: Router) {}

  /**
   * Check if current route is dashboard (new system)
   */
  isDashboardRoute(): boolean {
    const url = this.router.url;
    return url.startsWith('/dashboard') || url === '/';
  }
}
