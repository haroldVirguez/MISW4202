import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CancionesComponent } from './canciones/canciones.component';

const routes: Routes = [
  { path: '', redirectTo: '/canciones', pathMatch: 'full' },
  { path: 'canciones', component: CancionesComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
