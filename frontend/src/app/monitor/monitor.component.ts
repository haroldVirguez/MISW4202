import { Component, OnInit, OnDestroy } from '@angular/core';
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

@Component({
  selector: 'app-monitor',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="monitor-container">
      <div class="monitor-header">
        <div class="container">
          <div class="row align-items-center">
            <div class="col-md-8">
              <h1 class="monitor-title">
                <i class="fas fa-heartbeat"></i>
                Health Monitor
              </h1>
              <p class="monitor-subtitle">Monitoreo en tiempo real del microservicio de Logística e Inventarios</p>
            </div>
            <div class="col-md-4 text-end">
              <div class="status-indicator" [ngClass]="getOverallStatusClass()">
                <div class="pulse-dot"></div>
                <span class="status-text">{{ getOverallStatusText() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="container mt-4">
        <div class="control-panel">
          <div class="row">
            <div class="col-md-8">
              <div class="btn-group" role="group">
                <button 
                  class="btn btn-ping" 
                  (click)="hacerPing()"
                  [disabled]="pingEnProgreso">
                  <i class="fas fa-satellite-dish"></i>
                  {{ pingEnProgreso ? 'Ping en progreso...' : 'Ping Manual' }}
                </button>
                <button 
                  class="btn btn-refresh" 
                  (click)="obtenerEstadoCompleto()"
                  [disabled]="estadoEnProgreso">
                  <i class="fas fa-sync-alt" [class.fa-spin]="estadoEnProgreso"></i>
                  {{ estadoEnProgreso ? 'Actualizando...' : 'Actualizar Estado' }}
                </button>
              </div>
            </div>
            <div class="col-md-4 text-end">
              <div class="last-update">
                <i class="fas fa-clock"></i>
                <span>Última actualización: {{ ultimaActualizacion | date:'short' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dashboard-grid">
          <div class="dashboard-card status-card">
            <div class="card-header">
              <h3><i class="fas fa-server"></i> Estado del Servicio</h3>
            </div>
            <div class="card-body">
              <div class="status-grid" *ngIf="estadoLogistica">
                <div class="status-item">
                  <div class="status-icon" [ngClass]="getStatusIconClass(estadoLogistica.ping_echo.status)">
                    <i class="fas" [ngClass]="getStatusIcon(estadoLogistica.ping_echo.status)"></i>
                  </div>
                  <div class="status-info">
                    <h4>{{ estadoLogistica.ping_echo.status | titlecase }}</h4>
                    <p>{{ estadoLogistica.ping_echo.message }}</p>
                  </div>
                </div>
                <div class="metrics-row">
                  <div class="metric">
                    <span class="metric-label">Tiempo de Respuesta</span>
                    <span class="metric-value" [ngClass]="getResponseTimeClass(estadoLogistica.ping_echo.response_time_ms)">
                      {{ estadoLogistica.ping_echo.response_time_ms || 'N/A' }}ms
                    </span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">HTTP Status</span>
                    <span class="metric-value">{{ estadoLogistica.ping_echo.http_status || 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="dashboard-card broker-card">
            <div class="card-header">
              <h3><i class="fas fa-database"></i> Broker Redis</h3>
            </div>
            <div class="card-body" *ngIf="estadoLogistica">
              <div class="broker-status">
                <div class="broker-item">
                  <div class="broker-icon" [ngClass]="estadoLogistica.broker_status.redis_connected ? 'connected' : 'disconnected'">
                    <i class="fas fa-circle"></i>
                  </div>
                  <div class="broker-info">
                    <h4>Redis</h4>
                    <p>{{ estadoLogistica.broker_status.redis_connected ? 'Conectado' : 'Desconectado' }}</p>
                  </div>
                </div>
                <div class="queues-info">
                  <h5>Colas Activas</h5>
                  <div class="queue-list">
                    <div class="queue-item" *ngFor="let queue of getQueueList()">
                      <span class="queue-name">{{ queue.name }}</span>
                      <span class="queue-count">{{ queue.count }} tareas</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="dashboard-card recommendations-card" *ngIf="estadoLogistica && estadoLogistica.recommendations.length > 0">
            <div class="card-header">
              <h3><i class="fas fa-lightbulb"></i> Recomendaciones</h3>
            </div>
            <div class="card-body">
              <div class="recommendations-list">
                <div class="recommendation-item" *ngFor="let rec of estadoLogistica.recommendations">
                  <i class="fas fa-arrow-right"></i>
                  <span>{{ rec }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="history-section">
          <div class="dashboard-card history-card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h3><i class="fas fa-history"></i> Historial en Tiempo Real</h3>
              <button class="btn btn-clear" (click)="limpiarHistorial()">
                <i class="fas fa-trash"></i> Limpiar
              </button>
            </div>
            <div class="card-body">
              <div class="history-timeline" *ngIf="historialPings.length > 0; else noHistory">
                <div class="timeline-item" *ngFor="let ping of historialPings; let i = index" 
                     [ngClass]="getTimelineItemClass(ping.status)">
                  <div class="timeline-marker">
                    <i class="fas" [ngClass]="getStatusIcon(ping.status)"></i>
                  </div>
                  <div class="timeline-content">
                    <div class="timeline-header">
                      <span class="timeline-time">{{ ping.timestamp | date:'short' }}</span>
                      <span class="timeline-status" [ngClass]="getStatusBadgeClass(ping.status)">
                        {{ ping.status | titlecase }}
                      </span>
                    </div>
                    <div class="timeline-details">
                      <span class="timeline-message">{{ ping.message }}</span>
                      <span class="timeline-metrics">
                        {{ ping.response_time_ms || 'N/A' }}ms | HTTP {{ ping.http_status || 'N/A' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <ng-template #noHistory>
                <div class="no-history">
                  <i class="fas fa-chart-line"></i>
                  <p>No hay historial de pings disponible</p>
                  <small>Haz clic en "Ping Manual" para comenzar</small>
                </div>
              </ng-template>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    
    .monitor-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .monitor-header {
      background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
      color: white;
      padding: 2rem 0;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .monitor-title {
      font-size: 2.5rem;
      font-weight: 700;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    
    .monitor-title i {
      color: #ff6b6b;
    }
    
    .monitor-subtitle {
      font-size: 1.1rem;
      opacity: 0.9;
      margin: 0.5rem 0 0 0;
    }
    
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      border-radius: 25px;
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
    }
    
    .pulse-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
    
    .pulse-dot.healthy { background: #4ade80; }
    .pulse-dot.degraded { background: #fbbf24; }
    .pulse-dot.critical { background: #ef4444; }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    .status-text {
      font-weight: 600;
      font-size: 0.9rem;
    }
    
    .control-panel {
      background: white;
      border-radius: 15px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      backdrop-filter: blur(10px);
    }
    
    .btn-group {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    
    .btn {
      border: none;
      border-radius: 10px;
      padding: 0.75rem 1.5rem;
      font-weight: 600;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .btn-ping {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    
    .btn-ping:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .btn-refresh {
      background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
      color: white;
    }
    
    .btn-refresh:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(74, 222, 128, 0.4);
    }
    
    
    .btn-clear {
      background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
      color: white;
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }
    
    .last-update {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #6b7280;
      font-size: 0.9rem;
    }
    
    
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    
    .dashboard-card {
      background: white;
      border-radius: 15px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      overflow: hidden;
      transition: transform 0.3s ease;
    }
    
    .dashboard-card:hover {
      transform: translateY(-5px);
    }
    
    .card-header {
      background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
      padding: 1.5rem;
      border-bottom: 1px solid #e2e8f0;
    }
    
    .card-header h3 {
      margin: 0;
      font-size: 1.3rem;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    
    .card-header h3 i {
      color: #667eea;
    }
    
    .card-body {
      padding: 1.5rem;
    }
    
    .status-grid {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    
    .status-item {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    
    .status-icon {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      color: white;
    }
    
    .status-icon.healthy { background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); }
    .status-icon.degraded { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); }
    .status-icon.critical { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    .status-icon.timeout { background: linear-gradient(135deg, #fb923c 0%, #ea580c 100%); }
    .status-icon.unreachable { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); }
    .status-icon.error { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    
    .status-info h4 {
      margin: 0 0 0.25rem 0;
      font-size: 1.2rem;
      font-weight: 700;
      color: #1e293b;
    }
    
    .status-info p {
      margin: 0;
      color: #64748b;
      font-size: 0.9rem;
    }
    
    .metrics-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    
    .metric {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    
    .metric-label {
      font-size: 0.8rem;
      color: #64748b;
      font-weight: 500;
    }
    
    .metric-value {
      font-size: 1.1rem;
      font-weight: 700;
      color: #1e293b;
    }
    
    .metric-value.fast { color: #22c55e; }
    .metric-value.slow { color: #f59e0b; }
    .metric-value.very-slow { color: #ef4444; }
    
    .broker-status {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    
    .broker-item {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    
    .broker-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .broker-icon.connected {
      background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
      color: white;
    }
    
    .broker-icon.disconnected {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
    }
    
    .broker-info h4 {
      margin: 0 0 0.25rem 0;
      font-size: 1.1rem;
      font-weight: 700;
      color: #1e293b;
    }
    
    .broker-info p {
      margin: 0;
      color: #64748b;
      font-size: 0.9rem;
    }
    
    .queues-info h5 {
      margin: 0 0 1rem 0;
      font-size: 1rem;
      font-weight: 600;
      color: #374151;
    }
    
    .queue-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .queue-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem;
      background: #f8fafc;
      border-radius: 8px;
      border-left: 4px solid #667eea;
    }
    
    .queue-name {
      font-weight: 600;
      color: #1e293b;
    }
    
    .queue-count {
      font-size: 0.8rem;
      color: #64748b;
    }
    
    .recommendations-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    
    .recommendation-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem;
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      border-radius: 10px;
      border-left: 4px solid #f59e0b;
    }
    
    .recommendation-item i {
      color: #f59e0b;
      font-size: 0.9rem;
    }
    
    .recommendation-item span {
      color: #92400e;
      font-weight: 500;
    }
    
    .history-section {
      margin-top: 2rem;
    }
    
    .history-timeline {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-height: 400px;
      overflow-y: auto;
    }
    
    .timeline-item {
      display: flex;
      gap: 1rem;
      padding: 1rem;
      border-radius: 10px;
      transition: all 0.3s ease;
    }
    
    .timeline-item:hover {
      background: #f8fafc;
    }
    
    .timeline-item.healthy {
      border-left: 4px solid #22c55e;
      background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }
    
    .timeline-item.degraded {
      border-left: 4px solid #f59e0b;
      background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    }
    
    .timeline-item.critical {
      border-left: 4px solid #ef4444;
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    }
    
    .timeline-marker {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1rem;
      flex-shrink: 0;
    }
    
    .timeline-marker.healthy { background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); }
    .timeline-marker.degraded { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); }
    .timeline-marker.critical { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    
    .timeline-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .timeline-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .timeline-time {
      font-size: 0.8rem;
      color: #64748b;
      font-weight: 500;
    }
    
    .timeline-status {
      padding: 0.25rem 0.75rem;
      border-radius: 15px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    
    .timeline-details {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    
    .timeline-message {
      color: #374151;
      font-weight: 500;
    }
    
    .timeline-metrics {
      font-size: 0.8rem;
      color: #64748b;
    }
    
    .no-history {
      text-align: center;
      padding: 3rem 1rem;
      color: #64748b;
    }
    
    .no-history i {
      font-size: 3rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }
    
    .no-history p {
      font-size: 1.1rem;
      margin-bottom: 0.5rem;
    }
    
    .no-history small {
      font-size: 0.9rem;
    }
    
    .badge {
      font-size: 0.8em;
      padding: 0.4rem 0.8rem;
      border-radius: 15px;
      font-weight: 600;
    }
    
    .badge.healthy { background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); color: white; }
    .badge.degraded { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: white; }
    .badge.critical { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
    .badge.timeout { background: linear-gradient(135deg, #fb923c 0%, #ea580c 100%); color: white; }
    .badge.unreachable { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; }
    .badge.error { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
    
    @media (max-width: 768px) {
      .monitor-title {
        font-size: 2rem;
      }
      
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
      
      .btn-group {
        flex-direction: column;
      }
      
      .metrics-row {
        grid-template-columns: 1fr;
      }
      
      .timeline-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }
    }
  `]
})
export class MonitorComponent implements OnInit, OnDestroy {
  estadoLogistica: LogisticaStatus | null = null;
  historialPings: PingResult[] = [];
  pingEnProgreso = false;
  estadoEnProgreso = false;
  monitoreoAutomatico = false;
  ultimaActualizacion: Date = new Date();
  private monitoreoSubscription?: Subscription;

  constructor(private http: HttpClient) {}

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
    this.http.get<PingResult>('http://localhost:8080/monitor/ping-logistica')
      .subscribe({
        next: (result) => {
          this.historialPings.unshift(result);
          if (this.historialPings.length > 20) {
            this.historialPings = this.historialPings.slice(0, 20);
          }
          this.ultimaActualizacion = new Date();
          this.pingEnProgreso = false;
        },
        error: (error) => {
          console.error('Error en ping:', error);
          this.pingEnProgreso = false;
        }
      });
  }

  obtenerEstadoCompleto() {
    this.estadoEnProgreso = true;
    this.http.get<LogisticaStatus>('http://localhost:8080/monitor/logistica-status')
      .subscribe({
        next: (estado) => {
          this.estadoLogistica = estado;
          this.ultimaActualizacion = new Date();
          this.estadoEnProgreso = false;
        },
        error: (error) => {
          console.error('Error obteniendo estado:', error);
          this.estadoEnProgreso = false;
        }
      });
  }

  iniciarMonitoreoAutomatico() {
    this.monitoreoAutomatico = true;
    this.monitoreoSubscription = interval(500).subscribe(() => {
      this.hacerPing();
      this.obtenerEstadoCompleto();
    });
  }

  limpiarHistorial() {
    this.historialPings = [];
  }

  getStatusBadgeClass(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'badge healthy';
      case 'degraded':
        return 'badge degraded';
      case 'critical':
        return 'badge critical';
      case 'timeout':
        return 'badge timeout';
      case 'unreachable':
        return 'badge unreachable';
      case 'error':
        return 'badge error';
      default:
        return 'badge bg-secondary';
    }
  }

  getQueueCount(): number {
    if (!this.estadoLogistica?.broker_status?.queues) {
      return 0;
    }
    return Object.keys(this.estadoLogistica.broker_status.queues).length;
  }

  getOverallStatusClass(): string {
    if (!this.estadoLogistica) return 'unknown';
    return this.estadoLogistica.overall_status;
  }

  getOverallStatusText(): string {
    if (!this.estadoLogistica) return 'Desconocido';
    switch (this.estadoLogistica.overall_status) {
      case 'healthy': return 'Saludable';
      case 'degraded': return 'Degradado';
      case 'critical': return 'Crítico';
      default: return 'Desconocido';
    }
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
      case 'error': return 'fa-exclamation-circle';
      default: return 'fa-question-circle';
    }
  }

  getResponseTimeClass(responseTime: number): string {
    if (!responseTime) return '';
    if (responseTime < 100) return 'fast';
    if (responseTime < 500) return 'slow';
    return 'very-slow';
  }

  getQueueList(): Array<{name: string, count: number}> {
    if (!this.estadoLogistica?.broker_status?.queues) {
      return [];
    }
    return Object.entries(this.estadoLogistica.broker_status.queues).map(([name, info]: [string, any]) => ({
      name,
      count: info.length || 0
    }));
  }

  getTimelineItemClass(status: string): string {
    return status.toLowerCase();
  }
}
