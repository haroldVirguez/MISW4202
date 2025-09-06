import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { CancionesComponent } from './canciones.component';

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule
  ],
  declarations: [CancionesComponent],
  exports: [CancionesComponent]
})
export class CancionesModule { }
