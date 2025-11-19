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

// SocketService removed: WebSocket functionality is disabled for this deployment.
