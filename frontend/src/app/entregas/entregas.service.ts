import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Entrega } from './entrega';

@Injectable({
  providedIn: 'root',
})
export class EntregasService {
  constructor(private http: HttpClient) {}

  getEntregas(): Observable<Entrega[]> {
    return this.http.get<Entrega[]>('http://localhost:5000/entregas');
  }
}
