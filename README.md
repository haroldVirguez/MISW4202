# MISW4202 - Microservicios con Docker

Este proyecto incluye una arquitectura de microservicios con Flask, Angular, Redis y Celery desplegados con Docker Compose.

## Arquitectura

La aplicación está dividida en microservicios independientes que comparten la misma imagen base pero tienen diferentes entry points:

- **Frontend**: Aplicación Angular servida con Nginx
- **Microservicio Logística/Inventario**: API Flask en puerto 5000 (`microservices/logistica_inventario/`)
- **Microservicio Monitor**: Servicio de monitoreo en puerto 5001 (`microservices/monitor/`)
- **Redis**: Broker de mensajería para Celery
- **Celery Worker**: Procesador de tareas asíncronas
- **Celery Flower**: Monitor web de Celery en puerto 5555
- **SQLite**: Base de datos como volumen compartido

## Estructura del Proyecto

```
MISW4202/
├── shared/                      # Configuración compartida y reutilizable
│   ├── __init__.py             # Funciones: create_app, make_celery, etc.
│   └── flask_config.py         # Importaciones simplificadas
├── microservices/
│   ├── logistica_inventario/    # Microservicio principal
│   │   ├── __init__.py         # Exporta app
│   │   ├── app.py              # Flask app usando shared config
│   │   ├── tasks.py            # Tareas asíncronas de Celery
│   │   ├── modelos/
│   │   └── vistas/
│   └── monitor/                 # Microservicio monitor
│       ├── __init__.py         # Exporta app
│       └── monitor_service.py  # Flask app usando shared config
├── entrypoint_logistica.py      # Entry point para logística
├── entrypoint_monitor.py        # Entry point para monitor
├── entrypoint_celery.py         # Entry point para celery
├── celery_config.py             # Configuración de Celery
├── frontend/                    # Aplicación Angular
├── docker-compose.yml
├── Dockerfile                   # Imagen compartida
└── requirements.txt
```

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

- **Frontend**: <http://localhost:4200>
- **API Logística/Inventario**: <http://localhost:5002>
- **API Monitor**: <http://localhost:5001>
- **Celery Flower**: <http://localhost:5555>
- **Redis**: localhost:6379

### Comandos Útiles

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs m-logistica-inventario

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reconstruir un servicio específico
docker-compose up --build m-logistica-inventario
```

### Endpoints de Monitoreo

- `GET /health` - Health check de cada servicio
- `GET /monitor/status` - Estado general de los servicios
- `GET /monitor/queue` - Información de las colas de Celery
- `GET /monitor/workers` - Información de los workers activos

## Microservicios

### Logística/Inventario (`m-logistica-inventario`)

- **Puerto**: 5002
- **Entry Point**: `entrypoint_logistica.py`
- **Comando**: `python entrypoint_logistica.py`
- **Funcionalidad**: Gestión de entregas, autenticación

### Monitor (`m-monitor`)

- **Puerto**: 5001
- **Entry Point**: `entrypoint_monitor.py`
- **Comando**: `python entrypoint_monitor.py`
- **Funcionalidad**: Monitoreo de Redis, Celery y estado de servicios

### Celery Worker (`celery-worker`)

- **Entry Point**: Comando directo de Celery
- **Comando**: `celery -A celery_config.celery worker --loglevel=info`
- **Funcionalidad**: Procesamiento de tareas asíncronas

### Celery Flower (`celery-flower`)

- **Puerto**: 5555
- **Entry Point**: Comando directo de Celery
- **Comando**: `celery -A celery_config.celery flower --port=5555`
- **Funcionalidad**: Monitor web de Celery

## Desarrollo Local (Alternativo)

Para activar el venv en desarrollo local:

```powershell
.\venv\Scripts\Activate.ps1
```

## Variables de Entorno

Ver `.env.example` para las variables de entorno disponibles.

## Configuración de Microservicios

### **📦 Configuración Compartida (`shared/`)**

El módulo `shared` proporciona funciones reutilizables que cualquier microservicio puede usar:

- **`create_app(service_name, config_overrides)`**: Crea una app Flask configurada
- **`make_celery(app)`**: Configura Celery con contexto Flask
- **`add_health_check(app, service_name)`**: Agrega endpoint `/health`
- **`setup_cors(app, origins)`**: Configura CORS

### **🔧 Cada Microservicio:**

- **Imagen Docker**: Un solo Dockerfile compartido
- **Configuración**: Usa `shared` para configuración base + configuración específica
- **Entry Points**: Cada servicio tiene su propio punto de entrada independiente
- **Base de datos**: SQLite compartida via volumen Docker
- **Redis**: Broker común para Celery y monitoreo

### **💡 Ventajas de esta Estructura:**

✅ **Reutilizable**: La configuración en `shared/` se puede usar en nuevos microservicios  
✅ **Mantenible**: Cambios de configuración se hacen en un solo lugar  
✅ **Flexible**: Cada microservicio puede agregar configuración específica  
✅ **Separado**: Cada microservicio mantiene su lógica de negocio independiente

### **🚀 Cómo agregar un nuevo microservicio:**

1. **Crear la carpeta**: `microservices/mi_nuevo_servicio/`
2. **Crear el app.py**:
   ```python
   from shared import create_app, setup_cors, add_health_check
   
   app = create_app('mi_nuevo_servicio')
   setup_cors(app)
   add_health_check(app)
   
   @app.route('/mi-endpoint')
   def mi_endpoint():
       return {'mensaje': 'Hola desde mi nuevo microservicio'}
   ```
3. **Si necesitas tareas asíncronas, crear tasks.py**:
   ```python
   from celery_config import celery
   
   @celery.task
   def mi_tarea_asincrona():
       return "Tarea completada"
   ```
4. **Crear entry point**: `entrypoint_mi_servicio.py`
5. **Agregar al docker-compose.yml** con su propio `command:`
6. **Agregar el microservicio a `celery_config.py`** para auto-descubrir tareas

### **📋 Configuración de Celery Simplificada:**

- **Una sola configuración**: `celery_config.py` usa `shared` para crear la app
- **Auto-descubrimiento**: Encuentra automáticamente tareas en todos los microservicios
- **Sin duplicación**: No necesitas crear Celery en cada microservicio
- **Tareas por microservicio**: Cada uno tiene su propio `tasks.py`


