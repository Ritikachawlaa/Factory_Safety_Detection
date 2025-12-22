import { useState, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = import.meta.env.VITE_API_BASE || '/api';

// Type definitions for all responses
export interface ProcessFrameResponse {
  success: boolean;
  frame_id: string;
  occupancy: number;
  entries: number;
  exits: number;
  faces_recognized: number;
  vehicles_detected: number;
  processing_time_ms: number;
  error?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  services: {
    inference_engine: string;
    database: string;
    video_service: string;
    scheduler: string;
  };
}

export interface DiagnosticResponse {
  modules: {
    module_1: { status: string; processed_frames: number; recognized_faces: number };
    module_2: { status: string; vehicles_detected: number; plates_read: number };
    module_3: { status: string; total_employees: number; today_attendance: number };
    module_4: { status: string; current_occupancy: number; total_entries: number };
  };
  system: {
    uptime_seconds: number;
    frames_processed: number;
    cache_size: number;
  };
}

export interface EnrollEmployeeResponse {
  success: boolean;
  employee_id: string;
  message: string;
  error?: string;
}

export interface ResetCountersResponse {
  success: boolean;
  message: string;
  counters: {
    entries: number;
    exits: number;
    faces_recognized: number;
  };
}

export interface VehicleLog {
  id: string;
  vehicle_type: string;
  license_plate: string;
  confidence: number;
  timestamp: string;
  image_path?: string;
}

export interface OccupancyLog {
  id: string;
  timestamp: string;
  occupancy: number;
  entries: number;
  exits: number;
  duration_seconds: number;
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  employee_name: string;
  timestamp: string;
  check_in_time: string;
  check_out_time?: string;
  status: string;
}

export const useFactorySafetyAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiCall = useCallback(
    async <T,>(
      endpoint: string,
      method: 'GET' | 'POST' = 'GET',
      body?: Record<string, unknown>
    ): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        const url = `${API_URL}${API_BASE}${endpoint}`;
        const options: RequestInit = {
          method,
          headers: {
            'Content-Type': 'application/json',
          },
        };

        if (body && method === 'POST') {
          options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
          throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data as T;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('API Error:', errorMessage);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Module 1 & 3: Process frame for face recognition and attendance
  const processFrame = useCallback(
    async (frameBase64: string): Promise<ProcessFrameResponse | null> => {
      return apiCall<ProcessFrameResponse>(
        '/process',
        'POST',
        { frame: frameBase64 }
      );
    },
    [apiCall]
  );

  // Module 1 & 3: Enroll employee for face recognition
  const enrollEmployee = useCallback(
    async (
      frameBase64: string,
      employeeId: string,
      employeeName: string
    ): Promise<EnrollEmployeeResponse | null> => {
      return apiCall<EnrollEmployeeResponse>(
        '/enroll-employee',
        'POST',
        {
          frame: frameBase64,
          employee_id: employeeId,
          employee_name: employeeName,
        }
      );
    },
    [apiCall]
  );

  // Health check endpoint
  const checkHealth = useCallback(
    async (): Promise<HealthResponse | null> => {
      return apiCall<HealthResponse>('/health', 'GET');
    },
    [apiCall]
  );

  // Diagnostic endpoint for system status
  const getDiagnostics = useCallback(
    async (): Promise<DiagnosticResponse | null> => {
      return apiCall<DiagnosticResponse>('/diagnostic', 'GET');
    },
    [apiCall]
  );

  // Reset daily counters
  const resetCounters = useCallback(
    async (): Promise<ResetCountersResponse | null> => {
      return apiCall<ResetCountersResponse>(
        '/inference/reset',
        'POST'
      );
    },
    [apiCall]
  );

  // Module 2: Get vehicle logs
  const getVehicleLogs = useCallback(
    async (limit: number = 100): Promise<VehicleLog[] | null> => {
      return apiCall<VehicleLog[]>(
        `/vehicle-logs?limit=${limit}`,
        'GET'
      );
    },
    [apiCall]
  );

  // Module 4: Get occupancy logs
  const getOccupancyLogs = useCallback(
    async (limit: number = 100): Promise<OccupancyLog[] | null> => {
      return apiCall<OccupancyLog[]>(
        `/occupancy-logs?limit=${limit}`,
        'GET'
      );
    },
    [apiCall]
  );

  // Module 3: Get attendance records
  const getAttendanceRecords = useCallback(
    async (employeeId?: string): Promise<AttendanceRecord[] | null> => {
      const query = employeeId ? `?employee_id=${employeeId}` : '';
      return apiCall<AttendanceRecord[]>(
        `/attendance-records${query}`,
        'GET'
      );
    },
    [apiCall]
  );

  // Unified detection endpoint - process frame with all features
  const processUnifiedFrame = useCallback(
    async (
      frameBase64: string,
      enabledFeatures?: {
        [key: string]: boolean;
      }
    ): Promise<any | null> => {
      return apiCall<any>(
        '/detect',
        'POST',
        {
          frame: frameBase64,
          enabled_features: enabledFeatures || {
            human: true,
            vehicle: false,
            helmet: true,
            loitering: false,
            crowd: false,
            box_count: false,
            line_crossing: false,
            tracking: false,
            motion: false,
            face_detection: false,
            face_recognition: false,
          },
        }
      );
    },
    [apiCall]
  );

  return {
    loading,
    error,
    processFrame,
    enrollEmployee,
    checkHealth,
    getDiagnostics,
    resetCounters,
    getVehicleLogs,
    getOccupancyLogs,
    getAttendanceRecords,
    processUnifiedFrame,
  };
};
