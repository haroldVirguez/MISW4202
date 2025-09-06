import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask_restful import Api
from flask_jwt_extended import JWTManager

# Importar configuración compartida
from shared import create_app, make_celery, add_health_check, setup_cors

# Importar modelos y vistas locales
from .modelos import db
from .vistas import VistaEntregas, VistaEntrega, VistaSignIn, VistaLogIn

# Crear la aplicación usando la configuración compartida
app = create_app(service_name='logistica_inventario')

# Configurar CORS
setup_cors(app)

# Inicializar base de datos
with app.app_context():
    db.init_app(app)
    db.create_all()

# Configurar API REST
api = Api(app)
api.add_resource(VistaEntregas, '/entregas')
api.add_resource(VistaEntrega, '/entrega/<int:id_entrega>')
api.add_resource(VistaSignIn, '/signin', '/signin/<int:id_usuario>')
api.add_resource(VistaLogIn, '/login')

# Configurar JWT
jwt = JWTManager(app)

# Agregar health check
add_health_check(app, 'logistica_inventario')

# Nota: La instancia de Celery se crea en celery_config.py
# Si necesitas usar Celery en este microservicio, importa desde celery_config:
# from celery_config import celery