import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Entrega } from './cancion'; 
import { EntregasService } from './canciones.service'; 
import { Observable } from 'rxjs';

@Component({
  selector: 'app-entregas',
  templateUrl: './canciones.component.html',
  styleUrls: ['./canciones.component.css'],
  standalone: false
})

export class EntregasComponent implements OnInit {
  entregas$: Observable<Entrega[]>;

  constructor(private entregasService: EntregasService) {}
  
  ngOnInit() {
    this.entregas$ = this.entregasService.getEntregas();
  }
  
}
