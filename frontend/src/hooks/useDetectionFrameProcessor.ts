import { useEffect, useRef, useState, useCallback } from 'react';
import { useFactorySafetyAPI } from './useFactorySafetyAPI';

export interface DetectionResult {
  success: boolean;
  frame_id: string;
  timestamp?: string;
  people_count?: number;
  vehicle_count?: number;
  helmet_violations?: number;
  helmet_compliant?: number;
  ppe_compliance_rate?: number;
  loitering_detected?: boolean;
  loitering_count?: number;
  crowd_detected?: boolean;
  crowd_density?: string;
  box_count?: number;
  faces_recognized?: number;
  processing_time_ms?: number;
  error?: string;
  [key: string]: any;
}

interface UseDetectionFrameProcessorOptions {
  captureFrame: () => string | null;
  isActive: boolean;
  intervalMs?: number;
  enabledFeatures?: {
    [key: string]: boolean;
  };
}

interface UseDetectionFrameProcessorReturn {
  result: DetectionResult | null;
  isProcessing: boolean;
  error: string | null;
  startProcessing: () => void;
  stopProcessing: () => void;
  processFrameOnce: () => Promise<void>;
}

export const useDetectionFrameProcessor = ({
  captureFrame,
  isActive,
  intervalMs = 3000,  // OPTIMIZED: 3 seconds (was 500ms) - reduces AWS calls 6x!
  enabledFeatures = {
    human: true,
    vehicle: false,
    helmet: true,
    loitering: false,
    crowd: false,
    box_count: false,
    line_crossing: false,
    tracking: false,
    motion: false,
    face_detection: true,
    face_recognition: true,  // Keep face detection on
  },
}: UseDetectionFrameProcessorOptions): UseDetectionFrameProcessorReturn => {
  const { processUnifiedFrame } = useFactorySafetyAPI();
  
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const processingRef = useRef(false);
  const intervalRef = useRef<number | null>(null);

  const processFrameOnce = useCallback(async () => {
    if (isProcessing || processingRef.current) {
      return;
    }

    const frameData = captureFrame();
    if (!frameData) {
      return;
    }

    processingRef.current = true;
    setIsProcessing(true);
    setError(null);

    try {
      const detectionResult = await processUnifiedFrame(frameData, enabledFeatures);
      if (detectionResult) {
        setResult(detectionResult);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Detection failed';
      setError(errorMsg);
      console.error('Frame processing error:', err);
    } finally {
      processingRef.current = false;
      setIsProcessing(false);
    }
  }, [captureFrame, enabledFeatures, isProcessing, processUnifiedFrame]);

  const startProcessing = useCallback(() => {
    if (intervalRef.current !== null) {
      return; // Already processing
    }

    intervalRef.current = window.setInterval(() => {
      if (isActive) {
        processFrameOnce();
      }
    }, intervalMs);
  }, [isActive, intervalMs, processFrameOnce]);

  const stopProcessing = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Auto-start/stop based on isActive
  useEffect(() => {
    if (isActive) {
      startProcessing();
    } else {
      stopProcessing();
    }

    return () => {
      stopProcessing();
    };
  }, [isActive, startProcessing, stopProcessing]);

  return {
    result,
    isProcessing,
    error,
    startProcessing,
    stopProcessing,
    processFrameOnce,
  };
};
