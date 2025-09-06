"""
Módulo Celery - Gestión de tareas asíncronas
Contiene worker, client, registry y dispatcher
"""

from .worker import worker_celery
from .client import flask_celery
from .dispatcher import TaskDispatcher

__all__ = ['worker_celery', 'flask_celery', 'TaskDispatcher']
