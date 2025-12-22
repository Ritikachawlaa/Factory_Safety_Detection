import { useState } from "react";
import { Play, Pause, Maximize2, Settings, Circle } from "lucide-react";
import { Button } from "./ui/button";

interface CameraPreviewProps {
  title: string;
  detections?: {
    label: string;
    count: number;
    color: string;
  }[];
  overlayElements?: React.ReactNode;
}

const CameraPreview = ({ title, detections = [], overlayElements }: CameraPreviewProps) => {
  const [isPlaying, setIsPlaying] = useState(true);

  return (
    <div className="bg-card border border-border rounded-2xl overflow-hidden">
      {/* Camera Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-secondary/30">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Circle className="w-3 h-3 fill-destructive text-destructive animate-pulse" />
            <span className="text-sm font-medium text-foreground">LIVE</span>
          </div>
          <span className="text-sm text-muted-foreground">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Settings className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Camera View */}
      <div className="relative aspect-video bg-background">
        {/* Simulated camera feed with gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-secondary/20 via-background to-secondary/30">
          {/* Grid overlay for camera effect */}
          <div 
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `
                linear-gradient(to right, hsl(var(--primary) / 0.3) 1px, transparent 1px),
                linear-gradient(to bottom, hsl(var(--primary) / 0.3) 1px, transparent 1px)
              `,
              backgroundSize: '40px 40px'
            }}
          />
          
          {/* Timestamp */}
          <div className="absolute top-4 left-4 bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded-lg">
            <span className="text-xs font-mono text-primary">
              {new Date().toLocaleString()}
            </span>
          </div>

          {/* Custom overlay elements */}
          {overlayElements}

          {/* Detection boxes simulation */}
          <div className="absolute top-1/4 left-1/4 w-20 h-32 border-2 border-primary rounded-lg animate-pulse">
            <span className="absolute -top-6 left-0 text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">
              Person
            </span>
          </div>
        </div>
      </div>

      {/* Detection Stats */}
      {detections.length > 0 && (
        <div className="flex items-center gap-4 px-4 py-3 border-t border-border bg-secondary/20">
          {detections.map((detection, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${detection.color}`} />
              <span className="text-sm text-muted-foreground">{detection.label}:</span>
              <span className="text-sm font-semibold text-foreground">{detection.count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CameraPreview;
