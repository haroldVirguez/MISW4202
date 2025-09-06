import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EntregasComponent } from './entregas/entregas.component';

const routes: Routes = [
  { path: '', redirectTo: '/entregas', pathMatch: 'full' },
  { path: 'entregas', component: EntregasComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
