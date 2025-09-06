import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Entrega } from './entrega';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class EntregasService {
  private apiUrl = environment.apiGatewayUrl;

  constructor(private http: HttpClient) {}

  getEntregas(): Observable<Entrega[]> {
    return this.http.get<Entrega[]>(`${this.apiUrl}/api/v1/logistica/entregas`);
  }

  procesarEntrega(entregaId: number): Observable<any> {
    const body = {
      tipo: 'procesar_entrega',
      entrega_id: entregaId
    };
    
    return this.http.post(`${this.apiUrl}/api/v1/logistica/tareas`, body);
  }
}
