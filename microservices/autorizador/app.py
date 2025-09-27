import sys
import os
from flask_restful import Api

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask_jwt_extended import JWTManager
# Importar configuración compartida
from shared import create_app, add_health_check
from .modelos import db
from .vistas import VistaSignUp, VistaLogIn



# Crear la aplicación usando la configuración compartida
app = create_app(service_name='autorizador')

# Inicializar base de datos
with app.app_context():
    db.init_app(app)
    db.create_all()

# Configurar API REST
api = Api(app)

api.add_resource(VistaSignUp, '/signup')
api.add_resource(VistaLogIn, '/login')

# Configurar JWT
jwt = JWTManager(app)
# Agregar health check
add_health_check(app, 'autorizador')

