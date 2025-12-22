import ModuleCard from "./ModuleCard";
import {
  User,
  Car,
  UserCheck,
  Users,
  AlertTriangle,
} from "lucide-react";

const modules = [
  {
    icon: User,
    title: "Person Identity & Access Intelligence",
    purpose: "Identify who is present and who is unauthorized within premises.",
    capabilities: [
      "Detects all persons in camera view",
      "Identifies known vs unknown individuals",
      "Stores snapshots of unknown persons",
      "Employee face enrollment via dashboard",
    ],
    aiFeatures: ["Human Detection", "Face Detection", "Face Recognition"],
    useCases: ["Access Control", "Security Monitoring", "Attendance"],
    slug: "person-identity",
  },
  {
    icon: Car,
    title: "Vehicle & Gate Management System",
    purpose: "Monitor vehicle movement, identity, and access at entry/exit points.",
    capabilities: [
      "Vehicle detection & classification",
      "Number plate recognition (ANPR)",
      "Entry/exit time logging",
      "Vehicle type breakup analytics",
    ],
    aiFeatures: ["Vehicle Detection", "Vehicle Classification", "ANPR"],
    useCases: ["Factory Gates", "Parking Areas", "Logistics Tracking"],
    slug: "vehicle-management",
  },
  {
    icon: UserCheck,
    title: "Attendance & Workforce Presence",
    purpose: "Automate attendance tracking without biometric devices.",
    capabilities: [
      "Face-based attendance marking",
      "Entry & exit-based presence tracking",
      "Shift-wise attendance reports",
      "Late entry / early exit detection",
    ],
    aiFeatures: ["Face Recognition", "Human Detection", "Time Fencing"],
    useCases: ["Workforce Management", "HR Automation"],
    slug: "attendance",
  },
  {
    icon: Users,
    title: "People Counting & Occupancy Analytics",
    purpose: "Measure real-time and historical occupancy.",
    capabilities: [
      "Entry camera counting",
      "Exit camera counting",
      "Direction-based movement analysis",
      "Live occupancy calculation",
    ],
    aiFeatures: ["People Counting", "Entry Counting", "Exit Counting", "Line Crossing"],
    useCases: ["Capacity Planning", "Safety Compliance"],
    slug: "people-counting",
  },
  {
    icon: AlertTriangle,
    title: "Crowd Density & Overcrowding Detection",
    purpose: "Prevent overcrowding and safety risks.",
    capabilities: [
      "Crowd density estimation",
      "Density level classification",
      "Alert triggers for overcrowding",
      "Heat map visualization",
    ],
    aiFeatures: ["Crowd Analysis", "Density Estimation", "Alert System"],
    useCases: ["Event Safety", "Retail Analytics", "Public Spaces"],
    slug: "crowd-density",
  },
];

const Modules = () => {
  return (
    <section id="modules" className="py-24 relative">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-dark" />
      
      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-sm font-medium text-primary uppercase tracking-wider">
            Modular Architecture
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mt-4 mb-6">
            Intelligent AI Modules
          </h2>
          <p className="text-muted-foreground">
            Our platform offers specialized modules that can be deployed independently or combined
            for comprehensive surveillance intelligence.
          </p>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module, index) => (
            <ModuleCard key={module.title} {...module} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Modules;
