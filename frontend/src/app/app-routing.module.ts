import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { HelmetDetectionComponent } from './components/helmet-detection/helmet-detection.component';
import { LoiteringDetectionComponent } from './components/loitering-detection/loitering-detection.component';
import { ProductionCounterComponent } from './components/production-counter/production-counter.component';
import { AttendanceSystemComponent } from './components/attendance-system/attendance-system.component';
import { LoginComponent } from './components/login/login.component';
import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [AuthGuard] },
  { path: 'helmet-detection', component: HelmetDetectionComponent, canActivate: [AuthGuard] },
  { path: 'loitering-detection', component: LoiteringDetectionComponent, canActivate: [AuthGuard] },
  { path: 'production-counter', component: ProductionCounterComponent, canActivate: [AuthGuard] },
  { path: 'attendance-system', component: AttendanceSystemComponent, canActivate: [AuthGuard] }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
