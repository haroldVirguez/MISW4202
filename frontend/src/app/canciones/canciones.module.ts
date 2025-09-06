import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { EntregasComponent } from './canciones.component';

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule
  ],
  declarations: [EntregasComponent],
  exports: [EntregasComponent]
})
export class EntregasModule { }
