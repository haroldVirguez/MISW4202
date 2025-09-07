import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { MonitorComponent } from './monitor.component';

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    MonitorComponent
  ],
  exports: [MonitorComponent]
})
export class MonitorModule { }
