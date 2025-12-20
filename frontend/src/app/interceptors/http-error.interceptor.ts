import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';

/**
 * Global HTTP Interceptor for error handling and retries
 * Provides consistent error handling across all 4 modules
 */
@Injectable()
export class HttpErrorInterceptor implements HttpInterceptor {
  constructor() {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request).pipe(
      // Retry failed requests once (except for POST, PUT, DELETE)
      retry({
        count: request.method === 'GET' ? 1 : 0,
        delay: (error: any) => {
          if (error instanceof HttpErrorResponse && (error.status === 408 || error.status === 429)) {
            return throwError(() => error);
          }
          throw error;
        }
      }),
      catchError((error: HttpErrorResponse) => {
        const errorMessage = this.getErrorMessage(error);
        console.error('HTTP Error:', errorMessage);

        // Handle specific error scenarios
        switch (error.status) {
          case 0:
            // Network error
            console.error('Network error - check backend server');
            break;
          case 400:
            // Bad request
            console.error('Bad request:', error.error);
            break;
          case 401:
            // Unauthorized
            console.error('Unauthorized - login required');
            // You can redirect to login here if needed
            break;
          case 403:
            // Forbidden
            console.error('Forbidden - insufficient permissions');
            break;
          case 404:
            // Not found
            console.error('Resource not found:', error.url);
            break;
          case 408:
            // Request timeout
            console.error('Request timeout');
            break;
          case 429:
            // Too many requests
            console.error('Too many requests - rate limited');
            break;
          case 500:
            // Server error
            console.error('Server error - please try again later');
            break;
          case 503:
            // Service unavailable
            console.error('Service unavailable - backend may be down');
            break;
          default:
            console.error('Unexpected error:', error);
        }

        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Extract meaningful error message from HTTP error response
   */
  private getErrorMessage(error: HttpErrorResponse): string {
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      return `Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.error && typeof error.error === 'object') {
        if (error.error.detail) {
          return error.error.detail;
        } else if (error.error.message) {
          return error.error.message;
        }
      }
      return `Error Code: ${error.status}\nMessage: ${error.statusText}`;
    }
  }
}
