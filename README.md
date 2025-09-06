# MISW4202 - Microservicios con Docker

Este proyecto incluye una arquitectura de microservicios con Flask, Angular, Redis y Celery desplegados con Docker Compose.

## Arquitectura

- **Frontend**: Aplicación Angular servida con Nginx
- **Microservicio Principal**: API Flask en puerto 5000
- **Microservicio Monitor**: Servicio de monitoreo en puerto 5001
- **Redis**: Broker de mensajería para Celery
- **Celery Worker**: Procesador de tareas asíncronas
- **Celery Flower**: Monitor web de Celery en puerto 5555
- **SQLite**: Base de datos como volumen compartido

## Instalación y Ejecución

### Prerequisitos
- Docker
- Docker Compose

### Ejecutar la aplicación
```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d --build
```

### Servicios Disponibles

- **Frontend**: http://localhost:4200
- **API Principal**: http://localhost:5000
- **API Monitor**: http://localhost:5001
- **Celery Flower**: http://localhost:5555
- **Redis**: localhost:6379

### Comandos Útiles

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs microservice-main

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reconstruir un servicio específico
docker-compose up --build microservice-main
```

### Endpoints de Monitoreo

- `GET /monitor/status` - Estado general de los servicios
- `GET /monitor/queue` - Información de las colas de Celery
- `GET /monitor/workers` - Información de los workers activos
- `GET /health` - Health check del servicio monitor

## Desarrollo Local (Alternativo)

Para activar el venv en desarrollo local:

```powershell
.\venv\Scripts\Activate.ps1
```

## Variables de Entorno

Ver `.env.example` para las variables de entorno disponibles.


