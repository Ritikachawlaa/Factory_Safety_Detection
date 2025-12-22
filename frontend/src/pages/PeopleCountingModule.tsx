import { useEffect, useState, useCallback } from "react";
import { Users, LogIn, LogOut, TrendingUp, Activity, Camera, Shield, BarChart3 } from "lucide-react";
import ModulePageLayout from "@/components/ModulePageLayout";
import WebcamFeed from "@/components/WebcamFeed";
import StatsCard from "@/components/StatsCard";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { useFactorySafetyAPI } from "@/hooks/useFactorySafetyAPI";

const columns = [
  { key: "zone", label: "Zone Name" },
  { 
    key: "current", 
    label: "Current Occupancy",
    render: (value: number, row: any) => (
      <div className="flex items-center gap-2">
        <span className="font-semibold">{value}</span>
        <span className="text-muted-foreground">/ {row.capacity}</span>
      </div>
    )
  },
  { 
    key: "entries", 
    label: "Entries",
    render: (value: number) => (
      <div className="flex items-center gap-2 text-green-500">
        <LogIn className="w-4 h-4" />
        {value}
      </div>
    )
  },
  { 
    key: "exits", 
    label: "Exits",
    render: (value: number) => (
      <div className="flex items-center gap-2 text-orange-500">
        <LogOut className="w-4 h-4" />
        {value}
      </div>
    )
  },
  { 
    key: "status", 
    label: "Status",
    render: (value: string) => {
      const variants: Record<string, "default" | "secondary" | "destructive"> = {
        normal: "default",
        high: "secondary",
        low: "secondary"
      };
      return <Badge variant={variants[value]}>{value}</Badge>;
    }
  },
];

const PeopleCountingModule = () => {
  const [occupancyData, setOccupancyData] = useState<any[]>([]);
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [detectionResult, setDetectionResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getOccupancyLogs, getDiagnostics } = useFactorySafetyAPI();

  useEffect(() => {
    loadOccupancyData();
    const interval = setInterval(loadOccupancyData, 5000);
    return () => clearInterval(interval);
  }, [getOccupancyLogs, getDiagnostics]);

  const loadOccupancyData = async () => {
    try {
      setLoading(true);
      const [logs, diag] = await Promise.all([
        getOccupancyLogs(50),
        getDiagnostics()
      ]);

      if (logs && Array.isArray(logs)) {
        const transformed = logs.map((log: any) => ({
          zone: log.zone || "Main Area",
          current: log.current_occupancy || 0,
          capacity: log.capacity || 500,
          entries: log.entries || 0,
          exits: log.exits || 0,
          status: log.current_occupancy > (log.capacity || 500) * 0.8 ? "high" : log.current_occupancy > 0 ? "normal" : "low"
        }));
        setOccupancyData(transformed);
      }

      if (diag) {
        setDiagnostics(diag);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load occupancy data");
    } finally {
      setLoading(false);
    }
  };

  const occupancyMetrics = diagnostics?.modules?.module_4;
  const totalEntries = occupancyData.reduce((sum: number, item: any) => sum + item.entries, 0);
  const totalExits = occupancyData.reduce((sum: number, item: any) => sum + item.exits, 0);
  const currentOccupancy = occupancyMetrics?.current_occupancy || occupancyData.reduce((sum: number, item: any) => sum + item.current, 0);

  const handleDetectionResult = useCallback((result: any) => {
    if (result) {
      setDetectionResult(result);
    }
  }, []);

  return (
    <ModulePageLayout
      icon={Users}
      title="People Counting & Occupancy Analytics"
      description="Measure real-time and historical occupancy with advanced people counting using entry/exit cameras and directional analysis."
    >
      <div className="container mx-auto px-6">
        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard icon={Users} label="Current Occupancy" value={currentOccupancy || 0} />
          <StatsCard icon={LogIn} label="Total Entries" value={totalEntries || 0} />
          <StatsCard icon={LogOut} label="Total Exits" value={totalExits || 0} />
          <StatsCard icon={Activity} label="Module Status" value={occupancyMetrics?.status === "operational" ? "✓ Active" : "● Offline"} />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Entry Camera */}
          <div className="lg:col-span-2">
            <WebcamFeed 
              title="People Counting Camera"
              autoStart={true}
              intervalMs={500}
              enabledFeatures={{
                human: true,
                helmet: false,
                vehicle: false,
                loitering: false,
                crowd: true,
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

          {/* Stats Panel */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Module Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-sm">Occupancy Module</span>
                <Badge variant={occupancyMetrics?.status === "operational" ? "default" : "secondary"}>
                  {occupancyMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground">
                <p>• Real-time counting</p>
                <p>• Line crossing detection</p>
                <p>• Directional tracking</p>
                <p>• Entry/exit logging</p>
              </div>

              {/* Latest Detection */}
              {detectionResult && (
                <div className="mt-4 p-3 bg-cyan-50 dark:bg-cyan-950 border border-cyan-200 dark:border-cyan-800 rounded-lg text-sm">
                  <p className="font-semibold text-cyan-700 dark:text-cyan-300 mb-2">Current Frame</p>
                  <div className="space-y-1 text-xs">
                    <p><strong>People:</strong> {detectionResult.people_count || 0}</p>
                    <p><strong>Time:</strong> {detectionResult.processing_time_ms || 0}ms</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Hourly Occupancy Chart */}
        <div className="bg-card border border-border rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              Hourly Occupancy Trend
            </h3>
            <Badge variant="outline">Today</Badge>
          </div>
          {/* Simple bar chart visualization */}
          <div className="flex items-end justify-between h-40 gap-2">
            {[45, 78, 120, 180, 250, 320, 380, 420, 450, 399, 350, 280].map((value, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <div 
                  className="w-full bg-primary/20 rounded-t relative overflow-hidden"
                  style={{ height: `${(value / 500) * 100}%` }}
                >
                  <div 
                    className="absolute bottom-0 left-0 right-0 bg-primary rounded-t transition-all"
                    style={{ height: '100%' }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{8 + i}h</span>
              </div>
            ))}
          </div>
        </div>

        {/* Zone Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {occupancyData.slice(0, 3).map((zone) => (
            <div key={zone.zone} className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-foreground">{zone.zone}</h4>
                <Badge variant={zone.status === "high" ? "destructive" : "default"}>
                  {zone.status === "high" ? "Near Capacity" : "Normal"}
                </Badge>
              </div>
              <div className="mb-4">
                <div className="flex items-end gap-1 mb-2">
                  <span className="text-3xl font-bold text-foreground">{zone.current}</span>
                  <span className="text-muted-foreground mb-1">/ {zone.capacity}</span>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      zone.current / zone.capacity > 0.9 ? 'bg-destructive' : 'bg-primary'
                    }`}
                    style={{ width: `${(zone.current / zone.capacity) * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1 text-green-500">
                  <LogIn className="w-4 h-4" /> {zone.entries}
                </span>
                <span className="flex items-center gap-1 text-orange-500">
                  <LogOut className="w-4 h-4" /> {zone.exits}
                </span>
              </div>
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
                "Entry camera counting",
                "Exit camera counting",
                "Direction-based movement analysis",
                "Live occupancy calculation",
                "Zone-wise occupancy tracking",
                "Historical trend analysis"
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
              {["People Counting", "Entry Counting", "Exit Counting", "Line Crossing", "Direction Detection"].map((feature) => (
                <Badge key={feature} variant="secondary" className="px-3 py-1">
                  {feature}
                </Badge>
              ))}
            </div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Use Cases</h4>
            <div className="flex flex-wrap gap-2">
              {["Capacity Planning", "Safety Compliance", "Retail Analytics", "Event Management"].map((useCase) => (
                <Badge key={useCase} variant="outline" className="px-3 py-1 border-primary/30 text-primary">
                  {useCase}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Zone Occupancy Table */}
        <DataTable
          title="Zone-wise Occupancy"
          columns={columns}
          data={occupancyData.length > 0 ? occupancyData : []}
        />
      </div>
    </ModulePageLayout>
  );
};

export default PeopleCountingModule;
