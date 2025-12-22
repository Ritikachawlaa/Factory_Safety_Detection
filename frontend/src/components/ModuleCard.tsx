import { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

interface ModuleCardProps {
  icon: LucideIcon;
  title: string;
  purpose: string;
  capabilities: string[];
  aiFeatures: string[];
  useCases: string[];
  index: number;
  slug: string;
}

const ModuleCard = ({
  icon: Icon,
  title,
  purpose,
  capabilities,
  aiFeatures,
  useCases,
  index,
  slug,
}: ModuleCardProps) => {
  return (
    <Link
      to={`/modules/${slug}`}
      className="group relative bg-gradient-card border border-border rounded-2xl p-6 hover:border-primary/50 transition-all duration-500 hover:shadow-glow animate-slide-up block"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-2xl bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative z-10">
        {/* Icon */}
        <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center mb-4 shadow-glow group-hover:scale-110 transition-transform duration-300">
          <Icon className="w-6 h-6 text-primary-foreground" />
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-foreground mb-2">{title}</h3>

        {/* Purpose */}
        <p className="text-sm text-muted-foreground mb-4">{purpose}</p>

        {/* Capabilities */}
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">
            Capabilities
          </h4>
          <ul className="space-y-1">
            {capabilities.slice(0, 4).map((cap, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="w-1 h-1 rounded-full bg-primary mt-2 shrink-0" />
                {cap}
              </li>
            ))}
          </ul>
        </div>

        {/* AI Features */}
        <div className="flex flex-wrap gap-2 mb-4">
          {aiFeatures.map((feature, i) => (
            <span
              key={i}
              className="px-2 py-1 text-xs font-medium rounded-md bg-secondary text-muted-foreground"
            >
              {feature}
            </span>
          ))}
        </div>

        {/* Use Cases */}
        <div className="pt-4 border-t border-border">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Use Cases
          </h4>
          <div className="flex flex-wrap gap-2">
            {useCases.map((uc, i) => (
              <span
                key={i}
                className="px-3 py-1 text-xs font-medium rounded-full border border-primary/30 text-primary"
              >
                {uc}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ModuleCard;
