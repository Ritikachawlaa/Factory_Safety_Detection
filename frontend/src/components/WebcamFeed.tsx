import React, { useEffect, useRef, useCallback } from 'react';
import { Play, Pause, Maximize2, Settings, Circle, AlertCircle, Loader } from 'lucide-react';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { useWebcam } from '@/hooks/useWebcam';
import { useDetectionFrameProcessor } from '@/hooks/useDetectionFrameProcessor';

interface WebcamFeedProps {
  title?: string;
  autoStart?: boolean;
  intervalMs?: number;
  enabledFeatures?: {
    [key: string]: boolean;
  };
  onDetectionResult?: (result: any) => void;
  showDetections?: boolean;
  width?: number;
  height?: number;
}

const WebcamFeed: React.FC<WebcamFeedProps> = ({
  title = 'Camera Feed',
  autoStart = true,
  intervalMs = 3000,  // OPTIMIZED: 3 seconds (was 500ms) - 6x less processing
  enabledFeatures,
  onDetectionResult,
  showDetections = true,
  width = 1280,
  height = 720,
}) => {
  const { videoRef, canvasRef, isActive, startWebcam, stopWebcam, captureFrame, error: webcamError } = useWebcam({
    width,
    height,
  });

  const { result, isProcessing, error: processingError, startProcessing, stopProcessing } = useDetectionFrameProcessor({
    captureFrame,
    isActive,
    intervalMs,
    enabledFeatures,
  });

  const lastResultRef = useRef<any>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const videoContainerRef = useRef<HTMLDivElement>(null);
  const faceBoxesRef = useRef<Map<number, any>>(new Map()); // Cache for smooth animation

  // Draw bounding boxes on overlay canvas (animation loop at 60 FPS)
  useEffect(() => {
    const canvas = overlayCanvasRef.current;
    const container = videoContainerRef.current;
    
    if (!canvas || !container) return;

    // Set canvas size to match container (fullscreen)
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;

    const animationLoop = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw each cached face box (smooth animation)
      faceBoxesRef.current.forEach((face: any) => {
        const { x, y, w, h } = face.bbox;
        
        // CRITICAL FIX: Backend returns bbox in 640×360 space
        // Must scale to ACTUAL display size (not the original 1280×720)
        const BACKEND_WIDTH = 640;  // Backend processes at this resolution
        const BACKEND_HEIGHT = 360;
        
        const scaleX = canvas.width / BACKEND_WIDTH;
        const scaleY = canvas.height / BACKEND_HEIGHT;
        
        const scaledX = x * scaleX;
        const scaledY = y * scaleY;
        const scaledW = w * scaleX;
        const scaledH = h * scaleY;

        // Draw bounding box
        const color = face.is_known ? '#00ff00' : '#ff0000';
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.shadowColor = color;
        ctx.shadowBlur = 10;
        ctx.strokeRect(scaledX, scaledY, scaledW, scaledH);
        ctx.shadowColor = 'transparent';

        // Draw label
        const labelText = `Track ID: ${face.track_id} | ${face.name}`;
        ctx.font = 'bold 16px Arial';
        const textMetrics = ctx.measureText(labelText);
        const labelHeight = 28;
        const labelWidth = textMetrics.width + 12;

        ctx.fillStyle = color;
        ctx.globalAlpha = 0.8;
        ctx.fillRect(scaledX, scaledY - labelHeight, labelWidth, labelHeight);
        ctx.globalAlpha = 1.0;

        ctx.fillStyle = '#000000';
        ctx.textBaseline = 'middle';
        ctx.fillText(labelText, scaledX + 6, scaledY - labelHeight / 2);

        // Confidence
        if (face.confidence) {
          const confidenceText = `Confidence: ${(face.confidence * 100).toFixed(1)}%`;
          ctx.font = '13px Arial';
          ctx.fillStyle = color;
          ctx.fillText(confidenceText, scaledX + 4, scaledY + scaledH + 20);
        }

        // Status
        const statusText = face.is_known ? '✓ KNOWN' : '? UNKNOWN';
        ctx.font = 'bold 13px Arial';
        ctx.fillStyle = face.is_known ? '#00ff00' : '#ff0000';
        ctx.fillText(statusText, scaledX + 4, scaledY + scaledH + 40);
      });

      requestAnimationFrame(animationLoop);
    };

    animationLoop();
  }, []);

  // Update face boxes when new detection result comes (once every 2 seconds)
  useEffect(() => {
    if (!result?.detected_faces) return;

    // Update cached faces (this happens only every 2 seconds)
    const newFaces = new Map<number, any>();
    result.detected_faces.forEach((face: any) => {
      newFaces.set(face.track_id, face);
    });
    faceBoxesRef.current = newFaces;

    console.log(`📍 Updated ${result.detected_faces.length} face(s) at resolution: backend 640×360 → display ${overlayCanvasRef.current?.width}×${overlayCanvasRef.current?.height}`);
  }, [result]);

  useEffect(() => {
    if (autoStart) {
      startWebcam();
    }

    return () => {
      stopWebcam();
    };
  }, [autoStart, startWebcam, stopWebcam]);

  useEffect(() => {
    if (result && onDetectionResult && result !== lastResultRef.current) {
      lastResultRef.current = result;
      onDetectionResult(result);
    }
  }, [result, onDetectionResult]);

  const handlePlayPause = () => {
    if (isActive) {
      stopWebcam();
      stopProcessing();
    } else {
      startWebcam();
    }
  };

  const displayError = webcamError || processingError;

  return (
    <div className="bg-card border border-border rounded-2xl overflow-hidden">
      {/* Camera Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-secondary/30">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Circle 
              className={`w-3 h-3 fill-destructive text-destructive ${isActive ? 'animate-pulse' : ''}`} 
            />
            <span className="text-sm font-medium text-foreground">
              {isActive ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <span className="text-sm text-muted-foreground">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handlePlayPause}
          >
            {isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
          {isProcessing && (
            <div className="flex items-center gap-1 px-2">
              <Loader className="w-4 h-4 animate-spin text-primary" />
              <span className="text-xs text-primary">Processing...</span>
            </div>
          )}
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Settings className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {displayError && (
        <div className="px-4 py-3 border-b border-border bg-destructive/10">
          <Alert variant="destructive" className="border-0">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {displayError}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Camera View */}
      <div className="relative aspect-video bg-background overflow-hidden" ref={videoContainerRef}>
        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Video element */}
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          playsInline
        />

        {/* Overlay canvas for bounding boxes */}
        <canvas
          ref={overlayCanvasRef}
          className="absolute inset-0 w-full h-full"
        />

        {/* Overlay content */}
        <div className="absolute inset-0 flex flex-col justify-between p-4">
          {/* Timestamp */}
          <div className="flex justify-between items-start">
            <div className="bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded-lg">
              <span className="text-xs font-mono text-primary">
                {new Date().toLocaleString()}
              </span>
            </div>

            {/* Processing Info */}
            {result && showDetections && (
              <div className="bg-background/80 backdrop-blur-sm px-3 py-2 rounded-lg max-w-xs">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {result.people_count !== undefined && (
                    <div>
                      <span className="text-muted-foreground">People:</span>
                      <span className="ml-1 font-semibold text-primary">{result.people_count}</span>
                    </div>
                  )}
                  {result.helmet_violations !== undefined && (
                    <div>
                      <span className="text-muted-foreground">Violations:</span>
                      <span className="ml-1 font-semibold text-destructive">{result.helmet_violations}</span>
                    </div>
                  )}
                  {result.vehicle_count !== undefined && (
                    <div>
                      <span className="text-muted-foreground">Vehicles:</span>
                      <span className="ml-1 font-semibold text-primary">{result.vehicle_count}</span>
                    </div>
                  )}
                  {result.faces_recognized !== undefined && (
                    <div>
                      <span className="text-muted-foreground">Faces:</span>
                      <span className="ml-1 font-semibold text-primary">{result.faces_recognized}</span>
                    </div>
                  )}
                  {result.processing_time_ms !== undefined && (
                    <div className="col-span-2">
                      <span className="text-muted-foreground">Process Time:</span>
                      <span className="ml-1 font-mono text-xs">{result.processing_time_ms}ms</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Bottom Status */}
          {isActive && (
            <div className="flex justify-between items-end">
              <div className="text-xs text-muted-foreground">
                <span className="inline-block px-2 py-1 bg-background/80 backdrop-blur-sm rounded">
                  {width}x{height} @ {Math.round(1000 / intervalMs)} FPS
                </span>
              </div>
              {isProcessing && (
                <div className="text-xs text-primary animate-pulse">
                  Processing Frame...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default WebcamFeed;
