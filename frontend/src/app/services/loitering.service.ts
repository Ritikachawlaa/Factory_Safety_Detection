import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface LoiteringStatus {
  id?: number;
  timestamp?: string;
  activeGroups: number;
  alertTriggered?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class LoiteringService {
  private apiUrl = `${environment.apiUrl}/live/loitering/`;
  private statsUrl = `${environment.apiUrl}/stats/loitering/`;

  constructor(private http: HttpClient) {}

  // Send webcam frame for live detection
  detectFromFrame(frameData: string): Observable<LoiteringStatus> {
    return this.http.post<LoiteringStatus>(this.apiUrl, { frame: frameData });
  }

  // Get statistics
  getLoiteringStats(): Observable<any> {
    return this.http.get<any>(this.statsUrl);
  }

  // Get historical records
  getLoiteringRecords(limit: number = 10): Observable<LoiteringStatus[]> {
    return this.http.get<LoiteringStatus[]>(`${environment.apiUrl}/loitering-detection/?limit=${limit}`);
  }
}
