import { useEffect, useRef, useState, useCallback } from "react";
import { User, UserCheck, UserX, Camera, Shield, Clock, Eye, Upload, AlertCircle } from "lucide-react";
import ModulePageLayout from "@/components/ModulePageLayout";
import WebcamFeed from "@/components/WebcamFeed";
import StatsCard from "@/components/StatsCard";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useFactorySafetyAPI } from "@/hooks/useFactorySafetyAPI";
import { useSmartFaceDetection } from "@/hooks/useSmartFaceDetection";

const PersonIdentityModule = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { 
    enrollEmployee, 
    getDiagnostics, 
    loading, 
    error 
  } = useFactorySafetyAPI();

  const { processFaceDetection, detectionState } = useSmartFaceDetection();

  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [detectionData, setDetectionData] = useState<any>(null);
  const [detectedFaces, setDetectedFaces] = useState<any[]>([]);
  const [personData, setPersonData] = useState<any[]>([]);
  const [enrollMode, setEnrollMode] = useState(false);
  const [employeeInfo, setEmployeeInfo] = useState({ id: "", name: "" });

  useEffect(() => {
    loadDiagnostics();
    const interval = setInterval(loadDiagnostics, 5000);
    return () => clearInterval(interval);
  }, [getDiagnostics]);

  const loadDiagnostics = async () => {
    const data = await getDiagnostics();
    if (data) {
      setDiagnostics(data);
    }
  };

  const fileToBase64 = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64String = reader.result?.toString().split(',')[1];
        resolve(base64String || '');
      };
      reader.onerror = reject;
    });
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const base64 = await fileToBase64(file);
      
      if (enrollMode && employeeInfo.id && employeeInfo.name) {
        const result = await enrollEmployee(base64, employeeInfo.id, employeeInfo.name);
        if (result?.success) {
          alert(`${employeeInfo.name} enrolled successfully!`);
          setEnrollMode(false);
          setEmployeeInfo({ id: "", name: "" });
        }
      }
    } catch (err) {
      console.error('Error processing image:', err);
    }
  };

  const addToPersonData = useCallback((result: any) => {
    if (result.detected_faces && result.detected_faces.length > 0) {
      // Create a record for each detected face
      result.detected_faces.forEach((face: any) => {
        const newRecord = {
          id: `${face.track_id}`,
          name: face.name,
          type: face.is_known ? "Employee" : "Unknown",
          confidence: `${(face.confidence * 100).toFixed(1)}%`,
          lastSeen: new Date().toLocaleTimeString(),
          status: face.is_known ? "authorized" : "unknown"
        };
        setPersonData(prev => [newRecord, ...prev].slice(0, 20));
      });
    }
  }, []);

  const handleDetectionResult = useCallback((result: any) => {
    if (result) {
      setDetectionData(result);
      
      // Process face detection using smart detection hook
      const faceState = processFaceDetection(result);
      
      // Only update person data if faces have changed
      if (faceState.hasChanged) {
        setDetectedFaces(faceState.persistentFaces);
        addToPersonData(result);
        
        // Log state changes for debugging
        if (faceState.newFaces.length > 0) {
          console.log('✅ New faces detected:', faceState.newFaces.map(f => `${f.name} (Track ID: ${f.track_id})`));
        }
        if (faceState.removedFaces.length > 0) {
          console.log('❌ Faces removed:', faceState.removedFaces.map(f => `${f.name} (Track ID: ${f.track_id})`));
        }
      }
    }
  }, [processFaceDetection, addToPersonData]);

  const columns = [
    { key: "id", label: "Track ID" },
    { key: "name", label: "Name" },
    { key: "type", label: "Type" },
    { key: "confidence", label: "Confidence" },
    { key: "lastSeen", label: "Last Seen" },
    { 
      key: "status", 
      label: "Status",
      render: (value: string) => (
        <Badge variant={value === "authorized" ? "default" : value === "unknown" ? "secondary" : "destructive"}>
          {value === "authorized" ? <><UserCheck className="w-3 h-3 mr-1" />Authorized</> : <><UserX className="w-3 h-3 mr-1" />Unknown</>}
        </Badge>
      )
    },
  ];

  const faceMetrics = diagnostics?.modules?.module_1;
  const attendanceMetrics = diagnostics?.modules?.module_3;

  return (
    <ModulePageLayout
      icon={User}
      title="Person Identity & Access Intelligence"
      description="Identify who is present and who is unauthorized within premises using advanced AI-powered facial recognition and human detection."
    >
      <div className="container mx-auto px-6">
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard 
            icon={Eye} 
            label="Persons Detected" 
            value={detectionData?.faces_recognized || faceMetrics?.recognized_faces || 0} 
            trend={{ value: "Real-time", isPositive: true }} 
          />
          <StatsCard 
            icon={UserCheck} 
            label="Today Attendance" 
            value={attendanceMetrics?.today_attendance || 0} 
          />
          <StatsCard 
            icon={UserX} 
            label="Processed Frames" 
            value={faceMetrics?.processed_frames || 0} 
          />
          <StatsCard 
            icon={Shield} 
            label="Module Status" 
            value={faceMetrics?.status === "operational" ? "✓ Active" : "● Offline"} 
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Webcam Feed */}
          <div className="lg:col-span-2">
            <WebcamFeed 
              title="Person Identity Camera"
              autoStart={true}
              intervalMs={500}
              enabledFeatures={{
                human: true,
                helmet: false,
                vehicle: false,
                loitering: false,
                crowd: false,
                box_count: false,
                line_crossing: false,
                tracking: true,
                motion: false,
                face_detection: true,
                face_recognition: true,
              }}
              onDetectionResult={handleDetectionResult}
              showDetections={true}
            />
          </div>

          {/* Stats Details */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Module Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-sm">Face Recognition</span>
                <Badge variant={faceMetrics?.status === "operational" ? "default" : "secondary"}>
                  {faceMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-sm">Attendance Module</span>
                <Badge variant={attendanceMetrics?.status === "operational" ? "default" : "secondary"}>
                  {attendanceMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground">
                <p>• Real-time face detection</p>
                <p>• Live recognition</p>
                <p>• Auto-attendance logging</p>
                <p>• Multi-face tracking</p>
              </div>

              {/* Latest Detection */}
              {detectionData && (
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg text-sm">
                  <p className="font-semibold text-green-700 dark:text-green-300 mb-2">Latest Detection</p>
                  <div className="space-y-1 text-xs">
                    <p><strong>Faces Recognized:</strong> {detectionData.faces_recognized || 0}</p>
                    <p><strong>People Detected:</strong> {detectionData.people_count || 0}</p>
                    <p><strong>Process Time:</strong> {detectionData.processing_time_ms || 0}ms</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Current Detected Faces */}
        {detectedFaces.length > 0 && (
          <div className="mb-8 bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-green-500" />
              Currently Detected Faces ({detectedFaces.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {detectedFaces.map((face: any) => (
                <div key={face.track_id} className={`p-4 rounded-lg border-2 ${face.is_known ? 'border-green-500 bg-green-50 dark:bg-green-950' : 'border-orange-500 bg-orange-50 dark:bg-orange-950'}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="font-semibold text-foreground">{face.name}</p>
                      <p className="text-xs text-muted-foreground">Track ID: {face.track_id}</p>
                    </div>
                    <Badge variant={face.is_known ? "default" : "secondary"}>
                      {face.is_known ? "Known" : "Unknown"}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Confidence: {(face.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detection Events */}
        {detectionState.newFaces.length > 0 && (
          <div className="mb-8">
            <Alert className="border-green-200 bg-green-50 dark:bg-green-950">
              <Eye className="h-4 w-4 text-green-600 dark:text-green-400" />
              <AlertDescription className="text-green-700 dark:text-green-300">
                ✅ <strong>{detectionState.newFaces.length}</strong> new face(s) detected: {detectionState.newFaces.map(f => `${f.name} (Track ID: ${f.track_id})`).join(", ")}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {detectionState.removedFaces.length > 0 && (
          <div className="mb-8">
            <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-950">
              <AlertCircle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
              <AlertDescription className="text-orange-700 dark:text-orange-300">
                ⚠️ <strong>{detectionState.removedFaces.length}</strong> face(s) left: {detectionState.removedFaces.map(f => `${f.name} (Track ID: ${f.track_id})`).join(", ")}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Detection History Table */}
        <div className="mb-8 bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            Detection History (Last {personData.length > 0 ? personData.length : 0} Events)
          </h3>
          {personData.length > 0 ? (
            <DataTable columns={columns} data={personData} />
          ) : (
            <p className="text-center text-muted-foreground py-8">No detections yet. Webcam feed will appear here.</p>
          )}
        </div>

        {/* Capabilities & AI Features */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Camera className="w-5 h-5 text-primary" />
              Core Capabilities
            </h3>
            <ul className="space-y-3">
              {[
                "Real-time face detection & recognition",
                "Employee face enrollment & matching",
                "Automatic attendance tracking",
                "Unknown person alerting",
                "Multi-face tracking in single frame",
                "Face confidence scoring"
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Performance
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Processing Speed</span>
                <span className="font-semibold">~40-200ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Detection Accuracy</span>
                <span className="font-semibold">95%+</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Cost Savings</span>
                <span className="font-semibold">90%</span>
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                {["Face Detection", "Face Recognition", "Age Est.", "Gender Detection"].map((feature) => (
                  <Badge key={feature} variant="secondary" className="text-xs px-2 py-0.5">
                    {feature}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ModulePageLayout>
  );
};

export default PersonIdentityModule;
