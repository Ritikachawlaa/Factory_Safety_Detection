import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import PersonIdentityModule from "./pages/PersonIdentityModule";
import VehicleManagementModule from "./pages/VehicleManagementModule";
import AttendanceModule from "./pages/AttendanceModule";
import PeopleCountingModule from "./pages/PeopleCountingModule";
import CrowdDensityModule from "./pages/CrowdDensityModule";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/modules/person-identity" element={<PersonIdentityModule />} />
          <Route path="/modules/vehicle-management" element={<VehicleManagementModule />} />
          <Route path="/modules/attendance" element={<AttendanceModule />} />
          <Route path="/modules/people-counting" element={<PeopleCountingModule />} />
          <Route path="/modules/crowd-density" element={<CrowdDensityModule />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
