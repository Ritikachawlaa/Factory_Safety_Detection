#!/bin/bash
# Quick Module Creation Script
# Usage: ./create-module.sh vehicle "Vehicle Detection" "🚗" "vehicle" "Vehicles Detected" "vehicle_count"

MODULE_ID=$1
MODULE_NAME=$2
MODULE_ICON=$3
FEATURE_FLAG=$4
PRIMARY_LABEL=$5
VALUE_FIELD=$6

COMPONENT_NAME="module-$MODULE_ID"
BASE_PATH="src/app/components/modules"

echo "Creating $COMPONENT_NAME..."

# Create directory
mkdir -p "$BASE_PATH/$COMPONENT_NAME"

# Generate TypeScript component
cat > "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts" << 'EOF'
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { SharedWebcamService } from '../../../services/shared-webcam.service';
import { UnifiedDetectionService, EnabledFeatures, DetectionResult } from '../../../services/unified-detection.service';
import { interval, Subscription } from 'rxjs';

interface HistoryEntry {
  timestamp: Date;
  value: any;
  label: string;
}

@Component({
  selector: 'app-MODULE_COMPONENT_NAME',
  templateUrl: './MODULE_COMPONENT_NAME.component.html',
  styleUrls: ['./MODULE_COMPONENT_NAME.component.css']
})
export class MODULE_CLASS_NAMEComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  detectionResult: DetectionResult | null = null;
  private detectionSubscription?: Subscription;
  isDetecting = false;
  enabledFeatures: EnabledFeatures = {
    human: FEATURE_HUMAN,
    vehicle: FEATURE_VEHICLE,
    helmet: FEATURE_HELMET,
    loitering: FEATURE_LOITERING,
    crowd: FEATURE_CROWD,
    box_count: FEATURE_BOX,
    line_crossing: FEATURE_LINE,
    tracking: FEATURE_TRACK,
    motion: FEATURE_MOTION,
    face_detection: FEATURE_FACE_DET,
    face_recognition: FEATURE_FACE_REC
  };
  history: HistoryEntry[] = [];
  maxHistoryItems = 50;
  peakCount = 0;
  averageCount = 0;

  constructor(
    public webcamService: SharedWebcamService,
    private detectionService: UnifiedDetectionService
  ) {}

  ngOnInit(): void {
    setTimeout(() => {
      if (this.videoElement && this.webcamService.isActive()) {
        this.webcamService.attachVideoElement(this.videoElement.nativeElement);
      }
    }, 100);
    this.startDetection();
  }

  ngOnDestroy(): void {
    this.stopDetection();
  }

  startDetection(): void {
    this.isDetecting = true;
    this.detectionSubscription = interval(500).subscribe(() => this.processFrame());
  }

  stopDetection(): void {
    if (this.detectionSubscription) {
      this.detectionSubscription.unsubscribe();
      this.isDetecting = false;
    }
  }

  private processFrame(): void {
    const frameData = this.webcamService.captureFrame();
    if (!frameData) return;
    this.detectionService.detect(frameData, this.enabledFeatures).subscribe({
      next: (result: DetectionResult) => {
        this.detectionResult = result;
        this.updateHistory(result);
        this.updateStats(result);
      },
      error: (error: any) => console.error('Detection error:', error)
    });
  }

  private updateHistory(result: DetectionResult): void {
    const value = result.VALUE_FIELD;
    const label = `${value} MODULE_LABEL_LOWER`;
    this.history.unshift({ timestamp: new Date(), value, label });
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }
  }

  private updateStats(result: DetectionResult): void {
    const currentValue = result.VALUE_FIELD;
    if (typeof currentValue === 'number' && currentValue > this.peakCount) {
      this.peakCount = currentValue;
    }
    if (this.history.length > 0) {
      const sum = this.history.reduce((acc, e) => acc + (e.value || 0), 0);
      this.averageCount = Math.round(sum / this.history.length);
    }
  }

  get recentHistory(): HistoryEntry[] {
    return this.history.slice(0, 10);
  }

  formatTime(date: Date): string {
    return date.toLocaleTimeString();
  }
}
EOF

# Replace placeholders
sed -i "s/MODULE_COMPONENT_NAME/$COMPONENT_NAME/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"
sed -i "s/MODULE_CLASS_NAME/${COMPONENT_NAME^}/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"
sed -i "s/VALUE_FIELD/$VALUE_FIELD/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"
sed -i "s/MODULE_LABEL_LOWER/$(echo $PRIMARY_LABEL | tr '[:upper:]' '[:lower:]')/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"

# Set feature flags
for feature in human vehicle helmet loitering crowd box_count line_crossing tracking motion face_detection face_recognition; do
    if [ "$feature" == "$FEATURE_FLAG" ]; then
        sed -i "s/FEATURE_${feature^^}/true/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"
    else
        sed -i "s/FEATURE_${feature^^}/false/g" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.ts"
    fi
done

# Copy CSS
cp "$BASE_PATH/module-human/module-human.component.css" "$BASE_PATH/$COMPONENT_NAME/$COMPONENT_NAME.component.css"

echo "✅ Module $COMPONENT_NAME created!"
echo "   Next: Add to app.module.ts and app-routing.module.ts"
