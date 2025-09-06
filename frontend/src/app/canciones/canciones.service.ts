import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Cancion } from './cancion';

@Injectable({
  providedIn: 'root',
})
export class CancionesService {
  constructor(private http: HttpClient) {}

  getCanciones(): Observable<Cancion[]> {
    return this.http.get<Cancion[]>('http://localhost:5000/canciones');
  }
}
