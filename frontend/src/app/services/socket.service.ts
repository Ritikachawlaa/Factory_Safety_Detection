import { Injectable, signal, computed, effect } from '@angular/core';
import { environment } from '../../environments/environment';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface HelmetData {
  totalPeople: number;
  compliantCount: number;
  violationCount: number;
  detections: Detection[];
  timestamp?: string;
}

export interface Detection {
  class: 'helmet' | 'head' | 'person';
  confidence: number;
  bbox: [number, number, number, number]; // [x, y, width, height]
  trackingId?: number;
}

export interface LoiteringData {
  activeGroups: number;
  groupDetails: LoiteringGroup[];
  alerts: LoiteringAlert[];
  timestamp?: string;
}

export interface LoiteringGroup {
  groupId: number;
  personCount: number;
  duration: number;
  locations: Array<{ x: number; y: number }>;
}

export interface LoiteringAlert {
  groupId: number;
  message: string;
  timestamp: string;
  severity: 'warning' | 'critical';
}

export interface ProductionData {
  itemCount: number;
  hourlyData: HourlyCount[];
  itemsPerMinute: number;
  timestamp?: string;
}

export interface HourlyCount {
  hour: string;
  count: number;
}

export interface AttendanceData {
  verifiedCount: number;
  lastPersonSeen: string;
  verifiedLog: AttendanceEntry[];
  unknownLog: UnknownEntry[];
  timestamp?: string;
}

export interface AttendanceEntry {
  name: string;
  time: string;
  thumbnail?: string;
  confidence?: number;
}

export interface UnknownEntry {
  id: string;
  snapshot: string;
  time: string;
}

export interface CriticalAlert {
  id: string;
  module: 'helmet' | 'loitering' | 'production' | 'attendance';
  message: string;
  severity: 'warning' | 'critical';
  timestamp: string;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting' | 'error';

interface WebSocketMessage {
  type: 'helmet' | 'loitering' | 'production' | 'attendance' | 'alert' | 'ping';
  data: any;
}

// ============================================================================
// SOCKET SERVICE
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class SocketService {
  private ws?: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start at 1 second
  private heartbeatInterval?: any;
  private readonly wsUrl = 'ws://localhost:8000/ws/factory/';

  // ============================================================================
  // SIGNAL-BASED STATE STORES (The Heart of Real-Time Updates)
  // ============================================================================

  /** Connection status - drives UI indicators */
  connectionStatus = signal<ConnectionStatus>('disconnected');

  /** Helmet detection data */
  helmetData = signal<HelmetData>({
    totalPeople: 0,
    compliantCount: 0,
    violationCount: 0,
    detections: []
  });

  /** Loitering detection data */
  loiteringData = signal<LoiteringData>({
    activeGroups: 0,
    groupDetails: [],
    alerts: []
  });

  /** Production counter data */
  productionData = signal<ProductionData>({
    itemCount: 0,
    hourlyData: [],
    itemsPerMinute: 0
  });

  /** Attendance tracking data */
  attendanceData = signal<AttendanceData>({
    verifiedCount: 0,
    lastPersonSeen: '---',
    verifiedLog: [],
    unknownLog: []
  });

  /** Critical alerts array (newest first) */
  criticalAlerts = signal<CriticalAlert[]>([]);

  // ============================================================================
  // COMPUTED SIGNALS (Derived State)
  // ============================================================================

  /** Is the system connected? */
  isConnected = computed(() => this.connectionStatus() === 'connected');

  /** Are there any active violations? */
  hasViolations = computed(() => 
    this.helmetData().violationCount > 0 || 
    this.loiteringData().activeGroups > 0
  );

  /** Latest critical alert (for dashboard banner) */
  latestAlert = computed(() => this.criticalAlerts()[0] || null);

  /** Total alert count */
  alertCount = computed(() => this.criticalAlerts().length);

  // ============================================================================
  // CONSTRUCTOR & LIFECYCLE
  // ============================================================================

  constructor() {
    console.log('🔌 SocketService initialized');
    
    // Auto-connect when service is created
    this.connect();

    // Optional: Log connection status changes
    effect(() => {
      console.log(`📡 Connection Status: ${this.connectionStatus()}`);
    });
  }

  // ============================================================================
  // CONNECTION MANAGEMENT
  // ============================================================================

  /**
   * Establish WebSocket connection with automatic reconnection
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected');
      return;
    }

    console.log(`🔄 Connecting to ${this.wsUrl}...`);
    this.connectionStatus.set('reconnecting');

    try {
      this.ws = new WebSocket(this.wsUrl);

      // Connection opened
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected!');
        this.connectionStatus.set('connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.startHeartbeat();
      };

      // Message received
      this.ws.onmessage = (event: MessageEvent) => {
        this.handleMessage(event);
      };

      // Connection closed
      this.ws.onclose = (event: CloseEvent) => {
        console.log('❌ WebSocket closed:', event.reason);
        this.connectionStatus.set('disconnected');
        this.stopHeartbeat();
        this.scheduleReconnect();
      };

      // Error occurred
      this.ws.onerror = (error: Event) => {
        console.error('🔥 WebSocket error:', error);
        this.connectionStatus.set('error');
      };

    } catch (error) {
      console.error('🔥 Failed to create WebSocket:', error);
      this.connectionStatus.set('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Gracefully disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      console.log('🔌 Disconnecting WebSocket...');
      this.ws.close(1000, 'Client disconnect');
      this.ws = undefined;
    }
    this.stopHeartbeat();
    this.connectionStatus.set('disconnected');
  }

  /**
   * Reconnect with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnect attempts reached');
      this.connectionStatus.set('error');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Send heartbeat ping to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', data: {} });
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = undefined;
    }
  }

  // ============================================================================
  // MESSAGE HANDLING
  // ============================================================================

  /**
   * Route incoming WebSocket messages to appropriate Signal stores
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'helmet':
          this.helmetData.set(message.data);
          this.checkHelmetViolations(message.data);
          break;

        case 'loitering':
          this.loiteringData.set(message.data);
          this.checkLoiteringAlerts(message.data);
          break;

        case 'production':
          this.productionData.set(message.data);
          break;

        case 'attendance':
          this.attendanceData.set(message.data);
          break;

        case 'alert':
          this.addCriticalAlert(message.data);
          break;

        case 'ping':
          // Heartbeat response - do nothing
          break;

        default:
          console.warn('⚠️ Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('🔥 Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Send message to WebSocket server
   */
  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ Cannot send message: WebSocket not connected');
    }
  }

  // ============================================================================
  // ALERT MANAGEMENT
  // ============================================================================

  /**
   * Check helmet data for violations and create alerts
   */
  private checkHelmetViolations(data: HelmetData): void {
    if (data.violationCount > 0) {
      this.addCriticalAlert({
        id: `helmet-${Date.now()}`,
        module: 'helmet',
        message: `${data.violationCount} Helmet Violation${data.violationCount > 1 ? 's' : ''} Detected!`,
        severity: 'critical',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Check loitering data for alerts
   */
  private checkLoiteringAlerts(data: LoiteringData): void {
    if (data.activeGroups > 0) {
      this.addCriticalAlert({
        id: `loitering-${Date.now()}`,
        module: 'loitering',
        message: `${data.activeGroups} Loitering Group${data.activeGroups > 1 ? 's' : ''} Detected!`,
        severity: 'warning',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Add critical alert to the top of the list
   */
  private addCriticalAlert(alert: CriticalAlert): void {
    const currentAlerts = this.criticalAlerts();
    
    // Check if alert already exists (avoid duplicates)
    if (currentAlerts.some(a => a.message === alert.message)) {
      return;
    }

    // Add to beginning, keep only last 50 alerts
    this.criticalAlerts.set([alert, ...currentAlerts].slice(0, 50));
  }

  /**
   * Clear a specific alert
   */
  clearAlert(alertId: string): void {
    this.criticalAlerts.update(alerts => 
      alerts.filter(a => a.id !== alertId)
    );
  }

  /**
   * Clear all alerts
   */
  clearAllAlerts(): void {
    this.criticalAlerts.set([]);
  }

  // ============================================================================
  // MANUAL DATA REQUESTS (Fallback for HTTP polling if WebSocket unavailable)
  // ============================================================================

  /**
   * Request fresh data from server (useful for manual refresh)
   */
  requestUpdate(module: 'helmet' | 'loitering' | 'production' | 'attendance'): void {
    this.send({
      type: module,
      data: { action: 'request_update' }
    });
  }

  /**
   * Request all module updates
   */
  requestAllUpdates(): void {
    ['helmet', 'loitering', 'production', 'attendance'].forEach(module => {
      this.requestUpdate(module as any);
    });
  }
}
