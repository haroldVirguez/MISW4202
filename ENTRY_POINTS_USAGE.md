# Entry Points Usage Summary

## Cómo se están usando los Entry Points en Docker Compose

### 🔧 Microservicios Flask (usan entry points personalizados):

1. **m-logistica-inventario**:
   ```yaml
   command: python entrypoint_logistica.py
   ```
   - Entry Point: `entrypoint_logistica.py`
   - Importa: `from microservices.logistica_inventario import app`
   - Puerto: 5002

2. **m-monitor**:
   ```yaml
   command: python entrypoint_monitor.py
   ```
   - Entry Point: `entrypoint_monitor.py`
   - Importa: `from microservices.monitor import app`
   - Puerto: 5001

### ⚙️ Servicios Celery (usan comandos directos):

3. **celery-worker**:
   ```yaml
   command: celery -A celery_config.celery worker --loglevel=info
   ```
   - No usa entry point custom, usa comando directo de Celery
   - Usa `celery_config.py` que importa desde `shared`

4. **celery-flower**:
   ```yaml
   command: celery -A celery_config.celery flower --port=5555
   ```
   - No usa entry point custom, usa comando directo de Celery
   - Puerto: 5555

### 🚀 Para agregar un nuevo microservicio:

1. Crear: `entrypoint_mi_servicio.py` (usar `entrypoint_template.py` como base)
2. Agregar en docker-compose.yml:
   ```yaml
   mi-servicio:
     build:
       context: .
       dockerfile: Dockerfile
     command: python entrypoint_mi_servicio.py
     ports:
       - "5002:5002"
   ```

### ✅ Ventajas de esta estructura:

- **Separación limpia**: Cada servicio tiene su propio entry point
- **Reutilización**: Todos usan la misma imagen Docker base
- **Flexibilidad**: Se puede cambiar el comportamiento por servicio
- **Escalabilidad**: Fácil agregar nuevos microservicios
