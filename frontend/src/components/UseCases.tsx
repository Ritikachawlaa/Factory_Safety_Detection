import { Factory, Building2, Warehouse, ShoppingBag, GraduationCap, Hospital } from "lucide-react";

const useCases = [
  {
    icon: Factory,
    title: "Manufacturing & Factories",
    description: "Monitor entry gates, track workforce attendance, and ensure safety compliance across your production facilities.",
    modules: ["Vehicle Management", "Attendance", "Safety Monitoring"],
  },
  {
    icon: Building2,
    title: "Corporate Offices",
    description: "Streamline visitor management, automate attendance, and enhance building security with face recognition.",
    modules: ["Access Control", "Attendance", "Visitor Management"],
  },
  {
    icon: Warehouse,
    title: "Logistics & Warehouses",
    description: "Track vehicle movements, monitor loading docks, and optimize warehouse operations with real-time analytics.",
    modules: ["Vehicle Tracking", "People Counting", "Access Control"],
  },
  {
    icon: ShoppingBag,
    title: "Retail & Shopping Centers",
    description: "Understand customer flow, manage peak hours, and optimize store layouts with occupancy analytics.",
    modules: ["People Counting", "Crowd Density", "Heat Maps"],
  },
  {
    icon: GraduationCap,
    title: "Educational Institutions",
    description: "Ensure campus safety, automate attendance, and monitor restricted areas with intelligent surveillance.",
    modules: ["Attendance", "Access Control", "Safety Alerts"],
  },
  {
    icon: Hospital,
    title: "Healthcare Facilities",
    description: "Manage visitor access, monitor patient areas, and ensure compliance with healthcare regulations.",
    modules: ["Access Control", "Occupancy", "Safety Monitoring"],
  },
];

const UseCases = () => {
  return (
    <section id="use-cases" className="py-24 relative">
      <div className="absolute inset-0 bg-gradient-dark" />
      
      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-sm font-medium text-primary uppercase tracking-wider">
            Industry Solutions
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mt-4 mb-6">
            Designed for Your Industry
          </h2>
          <p className="text-muted-foreground">
            Our flexible platform adapts to diverse industry requirements with specialized configurations.
          </p>
        </div>

        {/* Use Cases Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {useCases.map((useCase, index) => (
            <div
              key={useCase.title}
              className="group relative p-8 rounded-2xl border border-border bg-card hover:border-primary/50 transition-all duration-500 animate-slide-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Icon */}
              <div className="w-14 h-14 rounded-2xl bg-gradient-primary flex items-center justify-center mb-6 shadow-glow group-hover:scale-110 transition-transform duration-300">
                <useCase.icon className="w-7 h-7 text-primary-foreground" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-foreground mb-3">
                {useCase.title}
              </h3>
              <p className="text-muted-foreground mb-6">
                {useCase.description}
              </p>

              {/* Modules Tags */}
              <div className="flex flex-wrap gap-2">
                {useCase.modules.map((module) => (
                  <span
                    key={module}
                    className="px-3 py-1 text-xs font-medium rounded-full bg-secondary text-muted-foreground"
                  >
                    {module}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default UseCases;
