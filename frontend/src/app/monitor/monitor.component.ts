import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

interface PingResult {
  target_service: string;
  status: string;
  message: string;
  response_time_ms: number;
  http_status: number;
  timestamp: string;
  ping_successful: boolean;
}

interface LogisticaStatus {
  service: string;
  overall_status: string;
  ping_echo: PingResult;
  broker_status: {
    redis_connected: boolean;
    redis_ping: boolean;
    queues: any;
    timestamp: string;
  };
  last_check: string;
  recommendations: string[];
}

interface Entrega {
  id: number;
  titulo: string;
  estado: string;
  fecha_creacion: string;
  fecha_confirmacion?: string;
  task_id?: string;
}

interface EstadoEntrega {
  entrega_id: number;
  estado: string;
  mensaje: string;
  timestamp: string;
  procesado: boolean;
  minutos?: number;
  segundos?: number;
  enmascarado?: boolean;
}


@Component({
  selector: 'app-monitor',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './monitor.component.html',
  styleUrls: ['./monitor.component.css']
})
export class MonitorComponent implements OnInit, OnDestroy {
  estadoLogistica: LogisticaStatus | null = null;
  historialPings: PingResult[] = [];
  pingEnProgreso = false;
  estadoEnProgreso = false;
  monitoreoAutomatico = false;
  ultimaActualizacion: Date = new Date();
  private monitoreoSubscription?: Subscription;
  
  ultimaEntrega: Entrega | null = null;
  estadoEntrega: EstadoEntrega | null = null;
  creandoEntrega = false;
  obteniendoEstado = false;
  contadorEntrega = 1;
  mostrarDetallesEntrega = false;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.obtenerEstadoCompleto();
    this.iniciarMonitoreoAutomatico();
  }

  ngOnDestroy() {
    if (this.monitoreoSubscription) {
      this.monitoreoSubscription.unsubscribe();
    }
  }

  hacerPing() {
    this.pingEnProgreso = true;
    
    this.http.get('http://localhost:8080/api/v1/monitor/ping-logistica')
      .subscribe({
        next: (response: any) => {
          this.historialPings.unshift(response);
          if (this.historialPings.length > 50) {
            this.historialPings = this.historialPings.slice(0, 50);
          }
          this.pingEnProgreso = false;
          this.ultimaActualizacion = new Date();
          this.cdr.detectChanges();
        },
        error: (error) => {
          console.error('Error en ping automático:', error);
          this.pingEnProgreso = false;
        }
      });
  }

  obtenerEstadoCompleto() {
    this.estadoEnProgreso = true;
    
    this.http.get('http://localhost:8080/api/v1/monitor/logistica-status')
      .subscribe({
        next: (response: any) => {
          this.estadoLogistica = response;
          this.estadoEnProgreso = false;
          this.ultimaActualizacion = new Date();
        },
        error: (error) => {
          console.error('Error obteniendo estado:', error);
          this.estadoEnProgreso = false;
        }
      });
  }

  iniciarMonitoreoAutomatico() {
    this.monitoreoAutomatico = true;
    this.monitoreoSubscription = interval(1500).subscribe(() => {
      this.hacerPing();
      this.obtenerEstadoCompleto();
    });
  }

  limpiarHistorial() {
    this.historialPings = [];
  }

  getOverallStatusClass(): string {
    if (!this.estadoLogistica) return 'critical';
    return this.estadoLogistica.overall_status.toLowerCase();
  }

  getOverallStatusText(): string {
    if (!this.estadoLogistica) return 'Desconocido';
    return this.estadoLogistica.overall_status;
  }

  getStatusIconClass(status: string): string {
    return status.toLowerCase();
  }

  getStatusIcon(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'fa-check-circle';
      case 'degraded': return 'fa-exclamation-triangle';
      case 'critical': return 'fa-times-circle';
      case 'timeout': return 'fa-clock';
      case 'unreachable': return 'fa-unlink';
      default: return 'fa-question-circle';
    }
  }

  getResponseTimeClass(responseTime: number): string {
    if (responseTime < 100) return 'fast';
    if (responseTime < 500) return 'slow';
    return 'very-slow';
  }

  getQueueList(): Array<{name: string, count: number}> {
    if (!this.estadoLogistica?.broker_status?.queues) {
      return [];
    }
    
    const queues = this.estadoLogistica.broker_status.queues;
    return Object.keys(queues).map(name => ({
      name,
      count: queues[name]?.length || 0
    }));
  }

  getTimelineItemClass(status: string): string {
    return status.toLowerCase();
  }

  crearEntrega() {
    this.creandoEntrega = true;
    
    const nuevaEntrega = {
      titulo: `Entrega de Prueba ${this.contadorEntrega}`,
      minutos: Math.floor(Math.random() * 60),
      segundos: Math.floor(Math.random() * 60),
      interprete: `Interprete ${this.contadorEntrega}`
    };

    this.http.post('http://localhost:8080/api/v1/logistica/entregas', nuevaEntrega)
      .subscribe({
        next: (response: any) => {
          const tareaData = {
            tipo: 'procesar_entrega',
            entrega_id: response.id
          };
          
          this.http.post('http://localhost:8080/api/v1/logistica/tareas', tareaData)
            .subscribe({
              next: (taskResponse: any) => {
                this.ultimaEntrega = {
                  id: response.id,
                  titulo: response.titulo,
                  estado: taskResponse.estado || 'pendiente',
                  fecha_creacion: new Date().toISOString(),
                  task_id: taskResponse.task_id || `task_${Date.now()}`
                };
                this.contadorEntrega++;
                this.creandoEntrega = false;
                this.ultimaActualizacion = new Date();
                this.mostrarDetallesEntrega = false;
                this.estadoEntrega = null;
                console.log('Tarea enviada a Celery:', taskResponse);
                console.log('ultimaEntrega creada:', this.ultimaEntrega);
                this.cdr.detectChanges();
              },
              error: (taskError) => {
                console.error('Error enviando tarea a Celery:', taskError);
                this.ultimaEntrega = {
                  id: response.id,
                  titulo: response.titulo,
                  estado: 'Pendiente Confirmacion Sistema',
                  fecha_creacion: new Date().toISOString(),
                  task_id: `task_${Date.now()}`
                };
                this.contadorEntrega++;
                this.creandoEntrega = false;
                this.ultimaActualizacion = new Date();
                this.mostrarDetallesEntrega = false;
                this.estadoEntrega = null;
                console.log('ultimaEntrega creada (en error):', this.ultimaEntrega);
                this.cdr.detectChanges();
              }
            });
        },
        error: (error) => {
          console.error('Error creando entrega:', error);
          this.creandoEntrega = false;
          
          this.ultimaEntrega = {
            id: this.contadorEntrega++,
            titulo: nuevaEntrega.titulo,
            estado: 'pendiente',
            fecha_creacion: new Date().toISOString(),
            task_id: `task_${Date.now()}`
          };
          console.log('ultimaEntrega creada (error creación):', this.ultimaEntrega);
          this.cdr.detectChanges();
        }
      });
  }

  obtenerEstadoEntrega() {
    if (!this.ultimaEntrega) {
      return;
    }
    
    this.obteniendoEstado = true;
    this.http.get(`http://localhost:8080/api/v1/logistica/entrega/${this.ultimaEntrega.id}`)
      .subscribe({
        next: (response: any) => {
          if (response.error_oculto) {
            console.error('Mensaje enmascarado:', response.mensaje);
          } else {
            console.log('Mensaje:', response.mensaje);
          }
          
          this.estadoEntrega = {
            entrega_id: this.ultimaEntrega!.id,
            estado: response.estado || 'procesado',
            mensaje: response.mensaje || `Entrega ${response.titulo} obtenida correctamente`,
            timestamp: new Date().toISOString(),
            procesado: true,
            minutos: response.minutos,
            segundos: response.segundos
          };
          this.mostrarDetallesEntrega = true;
          this.obteniendoEstado = false;
          this.ultimaActualizacion = new Date();
        },
        error: (error) => {
          console.error('Error obteniendo estado de entrega:', error);
          this.estadoEntrega = {
            entrega_id: this.ultimaEntrega!.id,
            estado: 'procesando_asincronamente',
            mensaje: 'Confirmación de entrega en proceso. El sistema continúa funcionando normalmente.',
            timestamp: new Date().toISOString(),
            procesado: false,
            enmascarado: true
          };
          this.mostrarDetallesEntrega = true;
          this.obteniendoEstado = false;
          this.ultimaActualizacion = new Date();
        }
      });
  }

  reiniciarFlujo() {
    this.ultimaEntrega = null;
    this.estadoEntrega = null;
    this.creandoEntrega = false;
    this.obteniendoEstado = false;
    this.ultimaActualizacion = new Date();
  }

  formatearEstado(estado: string): string {
    if (estado.toLowerCase().includes('confirmando')) {
      return 'Pendiente Confirmación Sistema';
    }
    if (estado.toLowerCase().includes('exitoso')) {
      return 'Exitoso';
    }
    return estado;
  }

}
