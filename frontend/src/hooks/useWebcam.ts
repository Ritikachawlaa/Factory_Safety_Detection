import { useRef, useCallback, useEffect, useState } from 'react';

interface UseWebcamOptions {
  width?: number;
  height?: number;
  facingMode?: 'user' | 'environment';
}

interface UseWebcamReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  isActive: boolean;
  startWebcam: () => Promise<void>;
  stopWebcam: () => void;
  captureFrame: () => string | null;
  frameDataUrl: string | null;
  error: string | null;
}

export const useWebcam = (options: UseWebcamOptions = {}): UseWebcamReturn => {
  const {
    width = 1280,
    height = 720,
    facingMode = 'user',
  } = options;

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  const [isActive, setIsActive] = useState(false);
  const [frameDataUrl, setFrameDataUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startWebcam = useCallback(async () => {
    try {
      setError(null);

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('getUserMedia is not supported in this browser');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: width },
          height: { ideal: height },
          facingMode,
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(err => {
          console.warn('Could not auto-play video:', err);
        });
      }

      setIsActive(true);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start webcam';
      setError(errorMsg);
      console.error('Webcam error:', err);
    }
  }, [width, height, facingMode]);

  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    setFrameDataUrl(null);
  }, []);

  const captureFrame = useCallback((): string | null => {
    if (!videoRef.current || !canvasRef.current) {
      return null;
    }

    try {
      const context = canvasRef.current.getContext('2d');
      if (!context) return null;

      const videoWidth = videoRef.current.videoWidth;
      const videoHeight = videoRef.current.videoHeight;

      // OPTIMIZATION: Downsample to 640x360 for processing (reduces data 75%)
      const targetWidth = 640;
      const targetHeight = 360;
      
      canvasRef.current.width = targetWidth;
      canvasRef.current.height = targetHeight;

      // Scale video to smaller size before drawing
      context.drawImage(videoRef.current, 0, 0, targetWidth, targetHeight);

      // Use lower JPEG quality for even smaller payload (0.75 instead of 0.85)
      const frameData = canvasRef.current.toDataURL('image/jpeg', 0.75);
      setFrameDataUrl(frameData);

      // Return base64 without data URL prefix for API calls
      return frameData.split(',')[1] || null;
    } catch (err) {
      console.error('Error capturing frame:', err);
      return null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  return {
    videoRef,
    canvasRef,
    isActive,
    startWebcam,
    stopWebcam,
    captureFrame,
    frameDataUrl,
    error,
  };
};
