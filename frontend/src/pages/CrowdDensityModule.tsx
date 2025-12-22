import { useEffect, useState, useCallback } from "react";
import { AlertTriangle, Activity, Eye, Bell, TrendingUp, Camera, Shield, Map } from "lucide-react";
import ModulePageLayout from "@/components/ModulePageLayout";
import WebcamFeed from "@/components/WebcamFeed";
import StatsCard from "@/components/StatsCard";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { useFactorySafetyAPI } from "@/hooks/useFactorySafetyAPI";

const columns = [
  { key: "zone", label: "Zone" },
  { 
    key: "level", 
    label: "Density Level",
    render: (value: string) => {
      const colors: Record<string, string> = {
        critical: "bg-red-500",
        high: "bg-orange-500",
        medium: "bg-yellow-500",
        low: "bg-green-500"
      };
      return (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${colors[value]}`} />
          <span className="capitalize">{value}</span>
        </div>
      );
    }
  },
  { key: "density", label: "Density %" },
  { key: "time", label: "Last Updated" },
  { 
    key: "action", 
    label: "Action",
    render: (value: string) => (
      <Badge variant={value === "Alert Sent" ? "destructive" : value === "Monitoring" ? "secondary" : "default"}>
        {value}
      </Badge>
    )
  },
];

const CrowdDensityModule = () => {
  const [densityData, setDensityData] = useState<any[]>([]);
  const [diagnostics, setDiagnostics] = useState<any>(null);  const [detectionResult, setDetectionResult] = useState<any>(null);  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getOccupancyLogs, getDiagnostics } = useFactorySafetyAPI();

  useEffect(() => {
    loadDensityData();
    const interval = setInterval(loadDensityData, 5000);
    return () => clearInterval(interval);
  }, [getOccupancyLogs, getDiagnostics]);

  const loadDensityData = async () => {
    try {
      setLoading(true);
      const [logs, diag] = await Promise.all([
        getOccupancyLogs(50),
        getDiagnostics()
      ]);

      if (logs && Array.isArray(logs)) {
        const transformed = logs.map((log: any) => {
          const density = log.capacity ? Math.round((log.current_occupancy / log.capacity) * 100) : 0;
          let level = "low";
          if (density > 85) level = "critical";
          else if (density > 70) level = "high";
          else if (density > 50) level = "medium";
          
          return {
            zone: log.zone || "Main Area",
            level: level,
            density: density + "%",
            time: new Date().toLocaleTimeString(),
            action: level === "critical" ? "Alert Sent" : level === "high" ? "Monitoring" : "Normal"
          };
        });
        setDensityData(transformed);
      }

      if (diag) {
        setDiagnostics(diag);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load crowd density data");
    } finally {
      setLoading(false);
    }
  };

  const densityMetrics = diagnostics?.modules?.module_4;
  const criticalZones = densityData.filter((d: any) => d.level === "critical").length;
  const highDensityZones = densityData.filter((d: any) => d.level === "high").length;

  const handleDetectionResult = useCallback((result: any) => {
    if (result) {
      setDetectionResult(result);
    }
  }, []);

  return (
    <ModulePageLayout
      icon={AlertTriangle}
      title="Crowd Density & Overcrowding Detection"
      description="Prevent overcrowding and safety risks with real-time crowd density estimation, heat maps, and intelligent alert systems."
    >
      <div className="container mx-auto px-6">
        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard icon={Activity} label="Critical Zones" value={criticalZones} />
          <StatsCard icon={AlertTriangle} label="High Density" value={highDensityZones} />
          <StatsCard icon={Eye} label="Zones Monitored" value={densityData.length} />
          <StatsCard icon={Bell} label="Module Status" value={densityMetrics?.status === "operational" ? "✓ Active" : "● Offline"} />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Main Camera with Heatmap */}
          <div className="lg:col-span-2">
            <WebcamFeed 
              title="Crowd Density Camera"
              autoStart={true}
              intervalMs={500}
              enabledFeatures={{
                human: true,
                helmet: false,
                vehicle: false,
                loitering: false,
                crowd: true,
                box_count: false,
                line_crossing: false,
                tracking: true,
                motion: false,
                face_detection: false,
                face_recognition: false,
              }}
              onDetectionResult={handleDetectionResult}
              showDetections={true}
            />
          </div>

          {/* Stats Panel */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Module Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-sm">Crowd Density</span>
                <Badge variant={densityMetrics?.status === "operational" ? "default" : "secondary"}>
                  {densityMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground">
                <p>• Real-time density</p>
                <p>• Crowd detection</p>
                <p>• Heatmap generation</p>
                <p>• Alert automation</p>
              </div>

              {/* Latest Detection */}
              {detectionResult && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-sm">
                  <p className="font-semibold text-red-700 dark:text-red-300 mb-2">Current Frame</p>
                  <div className="space-y-1 text-xs">
                    <p><strong>People:</strong> {detectionResult.people_count || 0}</p>
                    <p><strong>Crowd Detected:</strong> {detectionResult.crowd_detected ? "Yes" : "No"}</p>
                    <p><strong>Density:</strong> {detectionResult.crowd_density || "N/A"}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Density Level Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {[
            { level: "Critical", range: ">85%", count: 1, color: "red" },
            { level: "High", range: "70-85%", count: 2, color: "orange" },
            { level: "Medium", range: "50-70%", count: 4, color: "yellow" },
            { level: "Low", range: "<50%", count: 5, color: "green" },
          ].map((item) => (
            <div key={item.level} className={`bg-card border border-${item.color}-500/30 rounded-xl p-5`}>
              <div className={`w-3 h-3 rounded-full bg-${item.color}-500 mb-3`} />
              <h4 className="font-semibold text-foreground">{item.level}</h4>
              <p className="text-sm text-muted-foreground mb-2">{item.range}</p>
              <p className="text-2xl font-bold text-foreground">{item.count} <span className="text-sm font-normal text-muted-foreground">zones</span></p>
            </div>
          ))}
        </div>

        {/* Heat Map Visualization */}
        <div className="bg-card border border-border rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Map className="w-5 h-5 text-primary" />
              Zone Heat Map Overview
            </h3>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-6">
                {[
                  { label: "Low", color: "bg-green-500" },
                  { label: "Medium", color: "bg-yellow-500" },
                  { label: "High", color: "bg-orange-500" },
                  { label: "Critical", color: "bg-red-500" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${item.color}`} />
                    <span className="text-xs text-muted-foreground">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Simulated floor plan with heat zones */}
          <div className="relative h-64 bg-secondary/30 rounded-xl border border-border overflow-hidden">
            <div className="absolute inset-4 grid grid-cols-4 grid-rows-3 gap-2">
              {[
                { name: "Gate A", density: "low" },
                { name: "Main Plaza", density: "critical" },
                { name: "Food Court", density: "high" },
                { name: "Gate B", density: "low" },
                { name: "Hall 1", density: "medium" },
                { name: "Hall 2", density: "medium" },
                { name: "Hall 3", density: "low" },
                { name: "VIP Area", density: "low" },
                { name: "Parking A", density: "low" },
                { name: "Exit 1", density: "medium" },
                { name: "Exit 2", density: "low" },
                { name: "Parking B", density: "low" },
              ].map((zone) => {
                const colors: Record<string, string> = {
                  critical: "bg-red-500/40 border-red-500",
                  high: "bg-orange-500/40 border-orange-500",
                  medium: "bg-yellow-500/40 border-yellow-500",
                  low: "bg-green-500/40 border-green-500"
                };
                return (
                  <div 
                    key={zone.name}
                    className={`${colors[zone.density]} border rounded-lg flex items-center justify-center text-xs font-medium text-foreground`}
                  >
                    {zone.name}
                  </div>
                );
              })}
            </div>
          </div>
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
                "Crowd density estimation",
                "Density level classification",
                "Alert triggers for overcrowding",
                "Heat map visualization",
                "Threshold-based notifications",
                "Historical pattern analysis"
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
              {["Crowd Analysis", "Density Estimation", "Alert System", "Heat Mapping", "Anomaly Detection"].map((feature) => (
                <Badge key={feature} variant="secondary" className="px-3 py-1">
                  {feature}
                </Badge>
              ))}
            </div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Use Cases</h4>
            <div className="flex flex-wrap gap-2">
              {["Event Safety", "Retail Analytics", "Public Spaces", "Transportation Hubs", "Stadium Management"].map((useCase) => (
                <Badge key={useCase} variant="outline" className="px-3 py-1 border-primary/30 text-primary">
                  {useCase}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Alert History */}
        <DataTable
          title="Recent Density Alerts"
          columns={columns}
          data={densityData.length > 0 ? densityData : []}
        />
      </div>
    </ModulePageLayout>
  );
};

export default CrowdDensityModule;
