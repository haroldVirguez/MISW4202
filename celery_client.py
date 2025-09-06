"""
Configuración de Celery SOLO para envío de tareas desde Flask
NO auto-descubre, solo envía tareas por nombre
"""
import os
from celery import Celery

# Instancia de Celery para ENVÍO desde Flask
flask_celery = Celery(
    'misw4202_client',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Configuración más simple para cliente
flask_celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

print("✓ Flask Celery configurado para dispatch")

# NO auto-discover - solo envía tareas
