import { useRef, useCallback, useState } from 'react';

interface DetectedFace {
  track_id: number;
  name: string;
  confidence: number;
  bbox?: { x: number; y: number; w: number; h: number };
  is_known: boolean;
}

interface DetectionResult {
  detected_faces?: DetectedFace[];
  [key: string]: any;
}

interface SmartDetectionState {
  hasChanged: boolean;
  newFaces: DetectedFace[];
  removedFaces: DetectedFace[];
  persistentFaces: DetectedFace[];
}

export const useSmartFaceDetection = () => {
  const previousFacesRef = useRef<Map<number, DetectedFace>>(new Map());
  const [detectionState, setDetectionState] = useState<SmartDetectionState>({
    hasChanged: false,
    newFaces: [],
    removedFaces: [],
    persistentFaces: [],
  });

  const processFaceDetection = useCallback((result: DetectionResult): SmartDetectionState => {
    const currentFaces = result.detected_faces || [];
    const currentFacesMap = new Map(currentFaces.map(f => [f.track_id, f]));
    const previousFaces = previousFacesRef.current;

    // Find new faces (track_id in current but not in previous)
    const newFaces = currentFaces.filter(f => !previousFaces.has(f.track_id));

    // Find removed faces (track_id in previous but not in current)
    const removedFaces = Array.from(previousFaces.values()).filter(
      f => !currentFacesMap.has(f.track_id)
    );

    // Determine if state has changed
    const hasChanged = newFaces.length > 0 || removedFaces.length > 0;

    // Update persistent faces map
    previousFacesRef.current = currentFacesMap;

    const state: SmartDetectionState = {
      hasChanged,
      newFaces,
      removedFaces,
      persistentFaces: currentFaces,
    };

    setDetectionState(state);
    return state;
  }, []);

  const reset = useCallback(() => {
    previousFacesRef.current.clear();
    setDetectionState({
      hasChanged: false,
      newFaces: [],
      removedFaces: [],
      persistentFaces: [],
    });
  }, []);

  return {
    processFaceDetection,
    detectionState,
    reset,
  };
};
