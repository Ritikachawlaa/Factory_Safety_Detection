import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';

// Dashboard Components
import { DashboardMainComponent } from './components/dashboard/dashboard-main/dashboard-main.component';

// Module Components
import { ModuleHumanComponent } from './components/modules/module-human/module-human.component';
import { ModuleVehicleComponent } from './components/modules/module-vehicle/module-vehicle.component';
import { ModuleHelmetComponent } from './components/modules/module-helmet/module-helmet.component';
import { ModuleLoiteringComponent } from './components/modules/module-loitering/module-loitering.component';
import { ModuleLabourCountComponent } from './components/modules/module-labour-count/module-labour-count.component';
import { ModuleCrowdComponent } from './components/modules/module-crowd/module-crowd.component';
import { ModuleBoxCountComponent } from './components/modules/module-box-count/module-box-count.component';
import { ModuleLineCrossingComponent } from './components/modules/module-line-crossing/module-line-crossing.component';
import { ModuleTrackingComponent } from './components/modules/module-tracking/module-tracking.component';
import { ModuleMotionComponent } from './components/modules/module-motion/module-motion.component';
import { ModuleFaceDetectionComponent } from './components/modules/module-face-detection/module-face-detection.component';
import { ModuleFaceRecognitionComponent } from './components/modules/module-face-recognition/module-face-recognition.component';

const routes: Routes = [
  // Default route - redirect to dashboard
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  
  // Main dashboard (entry point with webcam initialization)
  { path: 'dashboard', component: DashboardMainComponent },
  
  // Module routes (per-feature pages)
  { path: 'dashboard/human', component: ModuleHumanComponent },
  { path: 'dashboard/vehicle', component: ModuleVehicleComponent },
  { path: 'dashboard/helmet', component: ModuleHelmetComponent },
  { path: 'dashboard/loitering', component: ModuleLoiteringComponent },
  { path: 'dashboard/labour-count', component: ModuleLabourCountComponent },
  { path: 'dashboard/crowd', component: ModuleCrowdComponent },
  { path: 'dashboard/box-count', component: ModuleBoxCountComponent },
  { path: 'dashboard/line-crossing', component: ModuleLineCrossingComponent },
  { path: 'dashboard/tracking', component: ModuleTrackingComponent },
  { path: 'dashboard/motion', component: ModuleMotionComponent },
  { path: 'dashboard/face-detection', component: ModuleFaceDetectionComponent },
  { path: 'dashboard/face-recognition', component: ModuleFaceRecognitionComponent },
  
  // Login (optional - currently no auth required)
  { path: 'login', component: LoginComponent },
  
  // Fallback
  { path: '**', redirectTo: '/dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
