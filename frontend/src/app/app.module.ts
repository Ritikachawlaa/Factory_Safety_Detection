import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule, DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { HelmetDetectionComponent } from './components/helmet-detection/helmet-detection.component';
import { LoiteringDetectionComponent } from './components/loitering-detection/loitering-detection.component';
import { ProductionCounterComponent } from './components/production-counter/production-counter.component';
import { AttendanceSystemComponent } from './components/attendance-system/attendance-system.component';
import { LoginComponent } from './components/login/login.component';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    HelmetDetectionComponent,
    LoiteringDetectionComponent,
    ProductionCounterComponent,
    AttendanceSystemComponent,
    LoginComponent
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
