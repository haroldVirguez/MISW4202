import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Cancion } from './cancion'; 
import { CancionesService } from './canciones.service'; 
import { Observable } from 'rxjs';

@Component({
  selector: 'app-canciones',
  templateUrl: './canciones.component.html',
  styleUrls: ['./canciones.component.css'],
  standalone: false
})

export class CancionesComponent implements OnInit {
  canciones$: Observable<Cancion[]>;

  constructor(private cancionesService: CancionesService) {}
  
  ngOnInit() {
    this.canciones$ = this.cancionesService.getCanciones();
  }
  
}
