import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule, DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { LoginComponent } from './components/login/login.component';
import { AppRoutingModule } from './app-routing.module';

// Old components (keeping for backward compatibility)
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { HelmetDetectionComponent } from './components/helmet-detection/helmet-detection.component';
import { LoiteringDetectionComponent } from './components/loitering-detection/loitering-detection.component';
import { ProductionCounterComponent } from './components/production-counter/production-counter.component';
import { AttendanceSystemComponent } from './components/attendance-system/attendance-system.component';
import { UnifiedDetectionComponent } from './components/unified-detection/unified-detection.component';

// New Dashboard System
import { SidebarComponent } from './components/shared/sidebar/sidebar.component';
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

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    
    // Old components
    DashboardComponent,
    HelmetDetectionComponent,
    LoiteringDetectionComponent,
    ProductionCounterComponent,
    AttendanceSystemComponent,
    UnifiedDetectionComponent,
    
    // New dashboard system
    SidebarComponent,
    DashboardMainComponent,
    
    // Module components
    ModuleHumanComponent,
    ModuleVehicleComponent,
    ModuleHelmetComponent,
    ModuleLoiteringComponent,
    ModuleLabourCountComponent,
    ModuleCrowdComponent,
    ModuleBoxCountComponent,
    ModuleLineCrossingComponent,
    ModuleTrackingComponent,
    ModuleMotionComponent,
    ModuleFaceDetectionComponent,
    ModuleFaceRecognitionComponent
  ],
  imports: [
    BrowserModule,
    CommonModule,
    HttpClientModule,
    FormsModule,
    AppRoutingModule
  ],
  providers: [DatePipe],
  bootstrap: [AppComponent]
})
export class AppModule { }
