import { LucideIcon, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import Navbar from "./Navbar";
import Footer from "./Footer";

interface ModulePageLayoutProps {
  icon: LucideIcon;
  title: string;
  description: string;
  children: React.ReactNode;
}

const ModulePageLayout = ({
  icon: Icon,
  title,
  description,
  children,
}: ModulePageLayoutProps) => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="pt-32 pb-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-dark" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/10 rounded-full blur-3xl" />
        
        <div className="container mx-auto px-6 relative z-10">
          <Link to="/#modules">
            <Button variant="ghost" className="mb-6 gap-2 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-4 h-4" />
              Back to Modules
            </Button>
          </Link>
          
          <div className="flex items-start gap-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow shrink-0">
              <Icon className="w-8 h-8 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
                {title}
              </h1>
              <p className="text-lg text-muted-foreground max-w-2xl">
                {description}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <main className="pb-24">
        {children}
      </main>

      <Footer />
    </div>
  );
};

export default ModulePageLayout;
