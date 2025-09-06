import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

# Importar la configuración compartida directamente
from shared import create_app, make_celery

# Crear una app Flask genérica para Celery
app = create_app(service_name='celery_worker')

# Crear la instancia de Celery
celery = make_celery(app)

# Auto-descubrir tareas de los microservicios
celery.autodiscover_tasks([
    'microservices.logistica_inventario',
    'microservices.monitor',
    # Agregar aquí nuevos microservicios que tengan tareas
])

if __name__ == '__main__':
    celery.start()
