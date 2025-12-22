import {
  Cpu,
  Zap,
  Shield,
  BarChart3,
  Bell,
  Cloud,
  Lock,
  Smartphone,
} from "lucide-react";

const features = [
  {
    icon: Cpu,
    title: "Edge AI Processing",
    description: "Run AI inference directly on edge devices for real-time analysis with minimal latency.",
  },
  {
    icon: Zap,
    title: "Real-Time Alerts",
    description: "Instant notifications for security events, unauthorized access, and anomaly detection.",
  },
  {
    icon: Shield,
    title: "Privacy Compliant",
    description: "Built-in privacy features with face blurring, data retention policies, and GDPR compliance.",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Comprehensive dashboards with historical trends, heat maps, and custom reports.",
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description: "Customizable alert rules with escalation workflows and multi-channel delivery.",
  },
  {
    icon: Cloud,
    title: "Cloud Integration",
    description: "Seamless cloud connectivity for remote access, backup, and multi-site management.",
  },
  {
    icon: Lock,
    title: "Enterprise Security",
    description: "End-to-end encryption, role-based access control, and audit logging.",
  },
  {
    icon: Smartphone,
    title: "Mobile Access",
    description: "Monitor your premises on-the-go with our responsive mobile applications.",
  },
];

const Features = () => {
  return (
    <section id="features" className="py-24 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 grid-pattern opacity-20" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      
      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-sm font-medium text-primary uppercase tracking-wider">
            Platform Capabilities
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mt-4 mb-6">
            Enterprise-Grade Features
          </h2>
          <p className="text-muted-foreground">
            Built for scale, security, and seamless integration with your existing infrastructure.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="group p-6 rounded-2xl border border-border bg-card hover:border-primary/50 transition-all duration-300 hover:shadow-glow animate-slide-up"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors duration-300">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
