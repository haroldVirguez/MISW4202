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
  procesando: boolean = false;
  mensaje: string = '';

  constructor(private entregasService: EntregasService) {}
  
  ngOnInit() {
    this.entregas$ = this.entregasService.getEntregas();
  }
  
  procesarPedido() {
    this.procesando = true;
    this.mensaje = 'Enviando petición de procesamiento...';
    
    const entregaId = Math.floor(Math.random() * 1000) + 1;
    
    this.entregasService.procesarEntrega(entregaId).subscribe({
      next: (response) => {
        this.procesando = false;
        this.mensaje = `✅ Pedido ${entregaId} enviado para procesamiento. Task ID: ${response.task_id}`;
        console.log('Respuesta del servidor:', response);
      },
      error: (error) => {
        this.procesando = false;
        this.mensaje = `❌ Error al procesar pedido: ${error.message || 'Error desconocido'}`;
        console.error('Error:', error);
      }
    });
  }
}
