"""
Configuración compartida para microservicios Flask
Este módulo proporciona funciones reutilizables para configurar Flask y Celery
"""

from flask import Flask
from celery import Celery
import os

def create_app(service_name="microservice", config_overrides=None):
    """
    Crear una aplicación Flask genérica que puede ser usada por cualquier microservicio
    
    Args:
        service_name (str): Nombre del microservicio para logging/identificación
        config_overrides (dict): Configuraciones adicionales específicas del microservicio
    
    Returns:
        Flask: Instancia configurada de Flask
    """
    app = Flask(__name__)
    
    # Configuración de base de datos
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///misw4202.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuración JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'frase-secreta')
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Configuración de Celery
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    app.config['CELERY_BROKER_URL'] = broker_url
    app.config['CELERY_RESULT_BACKEND'] = result_backend
    
    # Configuración específica del servicio
    app.config['SERVICE_NAME'] = service_name
    
    # Aplicar configuraciones adicionales si se proporcionan
    if config_overrides:
        app.config.update(config_overrides)
    
    return app

def make_celery(app):
    """
    Crear una instancia de Celery configurada con el contexto de Flask
    
    Args:
        app (Flask): Instancia de Flask
    
    Returns:
        Celery: Instancia configurada de Celery
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

def add_health_check(app, service_name=None):
    """
    Agregar endpoint de health check genérico
    
    Args:
        app (Flask): Instancia de Flask
        service_name (str): Nombre del servicio (opcional, usa SERVICE_NAME del config si no se proporciona)
    """
    if not service_name:
        service_name = app.config.get('SERVICE_NAME', 'unknown')
    
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy', 
            'service': service_name,
            'version': '1.0.0'
        }

def setup_cors(app, origins=None):
    """
    Configurar CORS para el microservicio
    
    Args:
        app (Flask): Instancia de Flask
        origins (list): Lista de orígenes permitidos (opcional)
    """
    from flask_cors import CORS
    
    if origins:
        CORS(app, origins=origins)
    else:
        CORS(app)
    
    return app
