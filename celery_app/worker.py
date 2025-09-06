"""
Configuración de Celery SOLO para el Worker
Auto-descubre y ejecuta las tareas
"""
import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from celery import Celery

# Instancia de Celery para el WORKER
worker_celery = Celery(
    'misw4202_worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Configuración del worker
worker_celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_routes={
        'logistica.*': {'queue': 'logistica'},
        'monitor.*': {'queue': 'monitor'},
    }
)

# Auto-descubrir tareas de los microservicios
worker_celery.autodiscover_tasks([
    'microservices.logistica_inventario.tasks',
    'microservices.monitor.tasks',
])

print("✓ Worker Celery configurado con auto-discovery")

if __name__ == '__main__':
    print("🚀 Iniciando worker de Celery...")
    worker_celery.start()
