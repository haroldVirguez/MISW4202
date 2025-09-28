import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EntregasComponent } from './entregas/entregas.component';
import { MonitorComponent } from './monitor/monitor.component';
import { AuthComponent } from './auth/auth.component';
import { SecurityValidationComponent } from './security-validation/security-validation.component';

const routes: Routes = [
  { path: '', redirectTo: '/auth', pathMatch: 'full' },
  { path: 'monitor', component: MonitorComponent },
  { path: 'auth', component: AuthComponent },
  { path: 'security-validation', component: SecurityValidationComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
