import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Entrega } from './entrega'; 
import { EntregasService } from './entregas.service'; 
import { Observable } from 'rxjs';

@Component({
  selector: 'app-entregas',
  templateUrl: './entregas.component.html',
  styleUrls: ['./entregas.component.css'],
  standalone: false
})

export class EntregasComponent implements OnInit {
  entregas$: Observable<Entrega[]>;

  constructor(private entregasService: EntregasService) {}
  
  ngOnInit() {
    this.entregas$ = this.entregasService.getEntregas();
  }
  
}
