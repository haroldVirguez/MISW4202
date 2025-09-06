import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Entrega } from './entrega';

@Injectable({
  providedIn: 'root',
})
export class EntregasService {
  private apiUrl = 'http://localhost:8080/api/v1/logistica';

  constructor(private http: HttpClient) {}

  getEntregas(): Observable<Entrega[]> {
    return this.http.get<Entrega[]>(`${this.apiUrl}/entregas`);
  }

  procesarEntrega(entregaId: number): Observable<any> {
    const body = {
      tipo: 'procesar_entrega',
      entrega_id: entregaId
    };
    
    return this.http.post(`${this.apiUrl}/tareas`, body);
  }
}
