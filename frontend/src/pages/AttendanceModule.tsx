import { useEffect, useState, useCallback } from "react";
import { UserCheck, Clock, LogIn, LogOut, Calendar, AlertTriangle, Camera, Shield } from "lucide-react";
import ModulePageLayout from "@/components/ModulePageLayout";
import WebcamFeed from "@/components/WebcamFeed";
import StatsCard from "@/components/StatsCard";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { useFactorySafetyAPI } from "@/hooks/useFactorySafetyAPI";

const columns = [
  { key: "name", label: "Employee Name" },
  { key: "department", label: "Department" },
  { 
    key: "checkIn", 
    label: "Check In",
    render: (value: string) => (
      <div className="flex items-center gap-2">
        <LogIn className="w-4 h-4 text-green-500" />
        {value}
      </div>
    )
  },
  { 
    key: "checkOut", 
    label: "Check Out",
    render: (value: string) => (
      <div className="flex items-center gap-2">
        <LogOut className="w-4 h-4 text-orange-500" />
        {value}
      </div>
    )
  },
  { 
    key: "status", 
    label: "Status",
    render: (value: string) => {
      const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
        present: "default",
        late: "secondary",
        early_exit: "secondary",
        absent: "destructive"
      };
      const labels: Record<string, string> = {
        present: "Present",
        late: "Late Entry",
        early_exit: "Early Exit",
        absent: "Absent"
      };
      return <Badge variant={variants[value]}>{labels[value]}</Badge>;
    }
  },
];

const AttendanceModule = () => {
  const [attendanceRecords, setAttendanceRecords] = useState<any[]>([]);
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [detectionResult, setDetectionResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getAttendanceRecords, getDiagnostics } = useFactorySafetyAPI();

  useEffect(() => {
    loadAttendanceData();
    const interval = setInterval(loadAttendanceData, 5000);
    return () => clearInterval(interval);
  }, [getAttendanceRecords, getDiagnostics]);

  const loadAttendanceData = async () => {
    try {
      setLoading(true);
      const [records, diag] = await Promise.all([
        getAttendanceRecords(undefined),
        getDiagnostics()
      ]);

      if (records && Array.isArray(records)) {
        const transformed = records.map((record: any) => ({
          name: record.employee_name || record.name || "Unknown",
          department: record.department || "-",
          checkIn: record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString() : "-",
          checkOut: record.check_out_time ? new Date(record.check_out_time).toLocaleTimeString() : "-",
          status: record.status || "present"
        }));
        setAttendanceRecords(transformed);
      }

      if (diag) {
        setDiagnostics(diag);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load attendance records");
    } finally {
      setLoading(false);
    }
  };

  const attendanceMetrics = diagnostics?.modules?.module_3;
  const presentCount = attendanceRecords.filter((r: any) => r.status === "present").length;
  const lateCount = attendanceRecords.filter((r: any) => r.status === "late").length;
  const absentCount = attendanceRecords.filter((r: any) => r.status === "absent").length;

  const handleDetectionResult = useCallback((result: any) => {
    if (result) {
      setDetectionResult(result);
      if (result?.faces_recognized > 0) {
        loadAttendanceData();
      }
    }
  }, []);
  return (
    <ModulePageLayout
      icon={UserCheck}
      title="Attendance & Workforce Presence System"
      description="Automate attendance tracking without biometric devices using AI-powered face recognition for accurate workforce management."
    >
      <div className="container mx-auto px-6">
        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatsCard icon={UserCheck} label="Present Today" value={presentCount || attendanceMetrics?.present_count || 0} />
          <StatsCard icon={Clock} label="Late Arrivals" value={lateCount || attendanceMetrics?.late_count || 0} />
          <StatsCard icon={LogOut} label="Early Exits" value={attendanceMetrics?.early_exits || 0} />
          <StatsCard icon={AlertTriangle} label="Absent" value={absentCount || attendanceMetrics?.absent_count || 0} />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Entry Camera */}
          <div className="lg:col-span-2">
            <WebcamFeed 
              title="Attendance Camera"
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
                <span className="text-sm">Attendance Module</span>
                <Badge variant={attendanceMetrics?.status === "operational" ? "default" : "secondary"}>
                  {attendanceMetrics?.status || "Loading"}
                </Badge>
              </div>
              <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground">
                <p>• Auto face detection</p>
                <p>• Real-time attendance</p>
                <p>• Multi-person tracking</p>
                <p>• Historical logging</p>
              </div>

              {/* Latest Detection */}
              {detectionResult && (
                <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg text-sm">
                  <p className="font-semibold text-amber-700 dark:text-amber-300 mb-2">Latest Detection</p>
                  <div className="space-y-1 text-xs">
                    <p><strong>Faces Detected:</strong> {detectionResult.faces_recognized || 0}</p>
                    <p><strong>Time:</strong> {detectionResult.processing_time_ms || 0}ms</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Shift Summary */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {[
            { shift: "Morning Shift", time: "6:00 AM - 2:00 PM", present: 48, total: 50 },
            { shift: "General Shift", time: "9:00 AM - 6:00 PM", present: 87, total: 95 },
            { shift: "Night Shift", time: "10:00 PM - 6:00 AM", present: 7, total: 8 },
          ].map((shift) => (
            <div key={shift.shift} className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-foreground">{shift.shift}</h4>
                <Calendar className="w-4 h-4 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground mb-3">{shift.time}</p>
              <div className="flex items-end justify-between">
                <div>
                  <span className="text-2xl font-bold text-foreground">{shift.present}</span>
                  <span className="text-muted-foreground">/{shift.total}</span>
                </div>
                <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary rounded-full" 
                    style={{ width: `${(shift.present / shift.total) * 100}%` }}
                  />
                </div>
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
                "Face-based attendance marking",
                "Entry & exit-based presence tracking",
                "Shift-wise attendance reports",
                "Late entry / early exit detection",
                "Multi-location attendance sync",
                "Integration with HR systems"
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
              {["Face Recognition", "Human Detection", "Time Fencing", "Liveness Check", "Mask Detection"].map((feature) => (
                <Badge key={feature} variant="secondary" className="px-3 py-1">
                  {feature}
                </Badge>
              ))}
            </div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Use Cases</h4>
            <div className="flex flex-wrap gap-2">
              {["Workforce Management", "HR Automation", "Payroll Integration", "Compliance Tracking"].map((useCase) => (
                <Badge key={useCase} variant="outline" className="px-3 py-1 border-primary/30 text-primary">
                  {useCase}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Today's Attendance */}
        <DataTable
          title="Today's Attendance Log"
          columns={columns}
          data={attendanceRecords.length > 0 ? attendanceRecords : []}
        />
      </div>
    </ModulePageLayout>
  );
};

export default AttendanceModule;
