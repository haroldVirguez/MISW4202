from flask import Flask
from celery import Celery
import os

def create_app(config_name):
    app = Flask(__name__)
    
    # Configuración de base de datos - usar variable de entorno o default
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///misw4202.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['JWT_SECRET_KEY'] = 'frase-secreta'
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Configuración de Celery - usar variables de entorno o defaults
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    app.config['CELERY_BROKER_URL'] = broker_url
    app.config['CELERY_RESULT_BACKEND'] = result_backend
    
    return app

def make_celery(app):
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