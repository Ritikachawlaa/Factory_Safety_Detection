import { useEffect, useState, useCallback } from "react";
import { Car, Truck, TruckIcon, Clock, LogIn, LogOut, Camera, Shield } from "lucide-react";
import ModulePageLayout from "@/components/ModulePageLayout";
import WebcamFeed from "@/components/WebcamFeed";
import StatsCard from "@/components/StatsCard";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { useFactorySafetyAPI } from "@/hooks/useFactorySafetyAPI";

const VehicleManagementModule = () => {
  const { getVehicleLogs, getDiagnostics, loading, error } = useFactorySafetyAPI();
  const [vehicleData, setVehicleData] = useState<any[]>([]);
  const [detectionResult, setDetectionResult] = useState<any>(null);
  const [diagnostics, setDiagnostics] = useState<any>(null);

  useEffect(() => {
    loadVehicleData();
    const interval = setInterval(loadVehicleData, 5000);
    return () => clearInterval(interval);
  }, [getVehicleLogs, getDiagnostics]);

  const loadVehicleData = async () => {
    const [logs, diag] = await Promise.all([
      getVehicleLogs(50),
      getDiagnostics()
    ]);
    
    if (logs) {
      const formattedData = logs.map((log: any, idx: number) => ({
        id: idx + 1,
        plate: log.license_plate || "UNKNOWN",
        type: log.vehicle_type || "Unknown",
        time: new Date(log.timestamp).toLocaleTimeString(),
        direction: "Detected",
        confidence: (log.confidence * 100).toFixed(0),
        status: log.license_plate ? "recognized" : "unread"
      }));
      setVehicleData(formattedData);
    }
    
    if (diag) setDiagnostics(diag);
  };

  const handleDetectionResult = useCallback((result: any) => {
    setDetectionResult(result);
    if (result?.vehicle_count > 0) {
      loadVehicleData();
    }
  }, []);

  const columns = [
    { key: "plate", label: "License Plate" },
    { 
      key: "type", 
      label: "Vehicle Type",
      render: (value: string) => (
        <div className="flex items-center gap-2">
          {value === "Truck" || value === "truck" ? <Truck className="w-4 h-4" /> : <Car className="w-4 h-4" />}
          {value}
        </div>
      )
    },
    { 
      key: "confidence", 
      label: "Confidence",
      render: (value: string) => `${value}%`
    },
    { key: "time", label: "Detected At" },
    { 
      key: "status", 
      label: "Status",
      render: (value: string) => (
        <Badge variant={value === "recognized" ? "default" : "secondary"}>
          {value === "recognized" ? "✓ Read" : "⚠ Unread"}
        </Badge>
      )
    },
  ];

  const vehicleMetrics = diagnostics?.modules?.module_2;
  return (
    <ModulePageLayout
      icon={Car}
      title="Vehicle & Gate Management System"
      description="Monitor vehicle movement, identity, and access at entry/exit points with advanced ANPR and vehicle classification."
    >
      <div className="container mx-auto px-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard icon={Car} label="Vehicles Detected" value={detectionResult?.vehicle_count || vehicleMetrics?.vehicles_detected || 0} />
          <StatsCard icon={LogIn} label="Plates Read" value={vehicleMetrics?.plates_read || 0} />
          <StatsCard icon={Clock} label="Processing Time" value={detectionResult?.processing_time_ms ? `${detectionResult.processing_time_ms}ms` : "~20ms"} />
          <StatsCard icon={TruckIcon} label="Module Status" value={vehicleMetrics?.status === "operational" ? "✓ Active" : "● Offline"} />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Entry Gate Camera */}
          <div className="lg:col-span-2">
            <WebcamFeed 
              title="Vehicle Detection Camera"
              autoStart={true}
              intervalMs={500}
              enabledFeatures={{
                human: false,
                helmet: false,
                vehicle: true,
                loitering: false,
                crowd: false,
                box_count: false,
                line_crossing: true,
                tracking: true,
                motion: false,
                face_detection: false,
                face_recognition: false,
              }}
              onDetectionResult={handleDetectionResult}
              showDetections={true}
            />
          </div>

          {/* Module Status */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Module Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-sm">Vehicle Detection</span>
                <Badge variant={vehicleMetrics?.status === "operational" ? "default" : "secondary"}>
                  {vehicleMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground">
                <p>• Real-time vehicle detection</p>
                <p>• ANPR/LPR enabled</p>
                <p>• Line crossing tracking</p>
                <p>• Vehicle classification</p>
              </div>

              {/* Latest Detection */}
              {detectionResult && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg text-sm">
                  <p className="font-semibold text-blue-700 dark:text-blue-300 mb-2">Latest Detection</p>
                  <div className="space-y-1 text-xs">
                    <p><strong>Vehicles:</strong> {detectionResult.vehicle_count || 0}</p>
                    <p><strong>Time:</strong> {detectionResult.processing_time_ms || 0}ms</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Vehicle Type Breakdown */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {[
            { type: "Cars", count: 78, icon: Car, color: "bg-blue-500" },
            { type: "Trucks", count: 23, icon: Truck, color: "bg-orange-500" },
            { type: "Bikes", count: 42, icon: Car, color: "bg-green-500" },
            { type: "Others", count: 13, icon: Car, color: "bg-purple-500" },
          ].map((item) => (
            <div key={item.type} className="bg-card border border-border rounded-xl p-5 text-center">
              <div className={`w-12 h-12 rounded-full ${item.color}/10 flex items-center justify-center mx-auto mb-3`}>
                <item.icon className={`w-6 h-6 ${item.color.replace('bg-', 'text-')}`} />
              </div>
              <p className="text-2xl font-bold text-foreground">{item.count}</p>
              <p className="text-sm text-muted-foreground">{item.type}</p>
            </div>
          ))}
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
                "Vehicle detection & classification",
                "Number plate recognition (ANPR)",
                "Entry/exit time logging",
                "Vehicle type breakup analytics",
                "Unauthorized vehicle alerts",
                "Integration with boom barriers"
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
              AI Features
            </h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {["Vehicle Detection", "Vehicle Classification", "ANPR/LPR", "Color Recognition", "Make/Model Detection"].map((feature) => (
                <Badge key={feature} variant="secondary" className="px-3 py-1">
                  {feature}
                </Badge>
              ))}
            </div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Use Cases</h4>
            <div className="flex flex-wrap gap-2">
              {["Factory Gates", "Parking Areas", "Logistics Tracking", "Toll Plazas", "Residential Complexes"].map((useCase) => (
                <Badge key={useCase} variant="outline" className="px-3 py-1 border-primary/30 text-primary">
                  {useCase}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Vehicle Log */}
        <DataTable
          title="Recent Vehicle Activity"
          columns={columns}
          data={vehicleData}
        />
      </div>
    </ModulePageLayout>
  );
};

export default VehicleManagementModule;
