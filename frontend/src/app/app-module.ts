import { NgModule, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { MonitorModule } from './monitor/monitor.module';
import { AuthComponent } from './auth/auth.component';
import { SecurityValidationComponent } from './security-validation/security-validation.component';
import { NavigationComponent } from './navigation/navigation.component';

@NgModule({
  declarations: [
    App
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    MonitorModule,
    AuthComponent,
    SecurityValidationComponent,
    NavigationComponent,
    HttpClientModule,
  ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection()
  ],
  bootstrap: [App]
})
export class AppModule { }
