import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username: string = '';
  password: string = '';
  errorMessage: string = '';
  isLoading: boolean = false;

  constructor(private router: Router) {
    // Check if already logged in
    if (localStorage.getItem('isLoggedIn') === 'true') {
      this.router.navigate(['/dashboard']);
    }
  }

  onSubmit(): void {
    this.isLoading = true;
    this.errorMessage = '';

    // Simple authentication (replace with real auth in production)
    if (this.username === 'admin' && this.password === 'admin123') {
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('username', this.username);
      this.router.navigate(['/dashboard']);
    } else {
      this.errorMessage = 'Invalid username or password';
      this.isLoading = false;
    }
  }
}
