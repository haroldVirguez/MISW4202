# Entry Points Usage Summary

### 🔧 Microservicios Flask (usan entry points personalizados):

1. **m-logistica-inventario**:
   ```yaml
   command: python entrypoint_logistica.py
   ```
   - Entry Point: `entrypoint_logistica.py`
   - Importa: `from microservices.logistica_inventario import app`
   - Puerto: 5002
   - Usa: `celery_client.py` para dispatch de tareas

2. **m-monitor**:
   ```yaml
   command: python entrypoint_monitor.py
   ```
   - Entry Point: `entrypoint_monitor.py`
   - Importa: `from microservices.monitor import app`
   - Puerto: 5001
   - Usa: `celery_client.py` para dispatch de tareas

### ⚙️ Servicios Celery :

3. **celery-worker**:
   ```yaml
   command: celery -A celery_worker.worker_celery worker --loglevel=info -Q celery,logistica,monitor
   ```
   - Usa: `celery_worker.py` (instancia worker_celery)
   - Auto-discovery de tareas de microservicios
   - Escucha múltiples colas: celery, logistica, monitor
   - Ejecuta tareas sin dependencias Flask

4. **celery-flower**:
   ```yaml
   command: celery -A celery_worker.worker_celery flower --port=5555
   ```
   - Usa: `celery_worker.py` para monitoreo
   - Puerto: 5555

### 🚀 Arquitectura de Tareas Asíncronas

#### Componentes Clave:

- **`celery_worker.py`**: Instancia worker_celery para ejecución
- **`celery_client.py`**: Instancia flask_celery para dispatch
- **`task_registry.py`**: Registry de metadatos sin código
- **`task_dispatcher.py`**: Interface limpia para envío
- **Tareas en microservicios**: Auto-discovery por worker

#### Para agregar un nuevo microservicio:

1. Crear: `entrypoint_mi_servicio.py` (usar `entrypoint_template.py` como base)
2. Crear tareas en: `microservices/mi_servicio/tasks.py`
3. Actualizar: `task_registry.py` con metadatos de nuevas tareas
4. Agregar en docker-compose.yml:

   ```yaml
   mi-servicio:
     build:
       context: .
       dockerfile: Dockerfile
     command: python entrypoint_mi_servicio.py
     ports:
       - "5003:5003"
   ```