import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EntregasComponent } from './canciones/canciones.component';

const routes: Routes = [
  { path: '', redirectTo: '/entregas', pathMatch: 'full' },
  { path: 'entregas', component: EntregasComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
