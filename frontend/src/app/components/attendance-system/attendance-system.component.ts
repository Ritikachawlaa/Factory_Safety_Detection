import { Component, OnInit, OnDestroy, ViewChild, ElementRef, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';
import { AttendanceService, AttendanceStatus } from '../../services/attendance.service';
import { ViolationService, AttendanceRecord } from '../../services/violation.service';
import { EmployeeService } from '../../services/employee.service';

@Component({
  selector: 'app-attendance-system',
  templateUrl: './attendance-system.component.html',
  styleUrls: ['./attendance-system.component.css']
})
export class AttendanceSystemComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  // Injected services
  private violationService = inject(ViolationService);
  public employeeService = inject(EmployeeService);

  // Signals for two-column logs
  attendanceRecords = this.violationService.attendanceRecords;
  unknownPersons = this.violationService.unknownPersons;

  showVerifyModal = signal(false);
  selectedUnknownRecord = signal<AttendanceRecord | null>(null);
  selectedEmployeeId = signal<string>('');

  // Computed signals for filtered logs
  verifiedLogs = computed(() =>
    this.attendanceRecords().filter(record => record.status === 'verified')
  );

  unknownLogs = computed(() =>
    this.attendanceRecords().filter(record => record.status === 'unknown')
  );

  attendanceData: AttendanceStatus = {
    verifiedCount: 0,
    lastPersonSeen: '---',
    attendanceLog: []
  };
  lastDetection: any = null;
  isWebcamActive = false;
  isRecognizing = false;
  private subscription?: Subscription;
  private stream?: MediaStream;

  constructor(private attendanceService: AttendanceService) { }

  ngOnInit(): void {
    // Load attendance records from violation service
    this.violationService.loadAttendanceRecords();

    this.subscription = this.attendanceService.getAttendanceStats().subscribe(
      (data: any) => {
        this.attendanceData = data;
        if (data.attendance_log) {
          this.attendanceData.attendanceLog = data.attendance_log;
        }
      },
      (error: any) => console.error('Error:', error)
    );
  }

  async toggleWebcam(): Promise<void> {
    if (this.isWebcamActive) {
      this.stopWebcam();
    } else {
      await this.startWebcam();
    }
  }

  async startWebcam(): Promise<void> {
    try {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
      }

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      });
      this.videoElement.nativeElement.srcObject = this.stream;
      this.isWebcamActive = true;
    } catch (error: any) {
      console.error('Error accessing webcam:', error);
      let errorMsg = 'Failed to access webcam.';
      if (error.name === 'NotReadableError') {
        errorMsg = 'Camera is being used by another application. Please close other apps using the camera and try again.';
      } else if (error.name === 'NotAllowedError') {
        errorMsg = 'Camera permission denied. Please allow camera access.';
      }
      alert(errorMsg);
      this.isWebcamActive = false;
    }
  }

  stopWebcam(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.videoElement.nativeElement.srcObject = null;
      this.isWebcamActive = false;
    }
  }

  recognizeFace(): void {
    if (!this.isWebcamActive) return;

    this.isRecognizing = true;
    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const context = canvas.getContext('2d');

    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    const frameData = canvas.toDataURL('image/jpeg').split(',')[1];

    this.attendanceService.detectFromFrame(frameData).subscribe({
      next: (result: any) => {
        console.log('Face recognition result:', result);
        this.lastDetection = {
          lastPersonSeen: result.recognized_person || 'Unknown',
          status: result.status || 'Not recognized',
          timestamp: result.timestamp || new Date()
        };

        if (result.recognized_person) {
          this.attendanceData.lastPersonSeen = result.recognized_person;
          this.attendanceData.verifiedCount = result.verified_count || this.attendanceData.verifiedCount + 1;
        }

        // Update logs with snapshots if available
        if (result.verified_log_details) {
          const newVerified = result.verified_log_details.map((log: any, index: number) => ({
            id: `live-v-${index}-${Date.now()}`,
            employeeId: 'EMP-00' + index,
            employeeName: log.name,
            timestamp: log.time, // Already formatted time string
            type: 'check-in',
            photoUrl: log.snapshot_url,
            confidence: 0.95,
            status: 'verified'
          }));

          const newUnknown = result.unknown_log_details ? result.unknown_log_details.map((log: any, index: number) => ({
            id: `live-u-${index}-${Date.now()}`,
            employeeId: 'unknown',
            employeeName: 'Unknown',
            timestamp: log.time,
            type: 'check-in',
            photoUrl: log.snapshot_url,
            confidence: 0.0,
            status: 'unknown'
          })) : [];

          // Update the violation service signals to reflect live data
          this.violationService.attendanceRecords.set([...newVerified, ...newUnknown]);
        }

        this.isRecognizing = false;
        // Removed alert to make it smoother
        // alert(`Face Recognition Complete!\nPerson: ${this.lastDetection.lastPersonSeen}\nStatus: ${this.lastDetection.status}`);
      },
      error: (error: any) => {
        console.error('Recognition error:', error);
        this.isRecognizing = false;
        // alert('Face recognition failed. Check console for details.');
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.stopWebcam();
  }

  // ============================================================================
  // TWO-COLUMN LOG METHODS
  // ============================================================================

  /**
   * Format timestamp for display (e.g., "07:02 AM")
   */
  formatTime(timestamp: string): string {
    // If it's already a time string like "09:30 AM", return it
    if (timestamp.includes('AM') || timestamp.includes('PM')) {
      return timestamp;
    }

    // Otherwise parse as date
    try {
      return new Date(timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return timestamp;
    }
  }

  /**
   * Open verify modal for unknown person
   */
  openVerifyModal(record: AttendanceRecord): void {
    this.selectedUnknownRecord.set(record);
    this.selectedEmployeeId.set('');
    this.showVerifyModal.set(true);
  }

  /**
   * Close verify modal
   */
  closeVerifyModal(): void {
    this.showVerifyModal.set(false);
    this.selectedUnknownRecord.set(null);
    this.selectedEmployeeId.set('');
  }

  /**
   * Verify unknown person and link to employee
   */
  verifyUnknownPerson(): void {
    const record = this.selectedUnknownRecord();
    const employeeId = this.selectedEmployeeId();

    if (!record || !employeeId) {
      alert('Please select an employee');
      return;
    }

    this.violationService.verifyUnknownPerson(record.id, employeeId).subscribe({
      next: () => {
        alert('✅ Person verified and linked to employee database!');
        this.closeVerifyModal();
      },
      error: (err) => {
        alert('❌ Failed to verify person: ' + err.message);
      }
    });
  }
}
