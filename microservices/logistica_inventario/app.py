import sys
import os
# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask_restful import Api
from flask_jwt_extended import JWTManager

# Importar configuración compartida
from shared import create_app, add_health_check
# Removed setup_cors - CORS is handled by nginx API Gateway

# Importar modelos y vistas locales
from .modelos import db
from .vistas import VistaEntregas, VistaEntrega, VistaTareas, VistaTareaDetail,  VistaConfirmarEntrega

# Crear la aplicación usando la configuración compartida
app = create_app(service_name='logistica_inventario')

# CORS is handled by nginx API Gateway - no need to setup here

# Inicializar base de datos
with app.app_context():
    db.init_app(app)
    db.create_all()

# Configurar API REST
api = Api(app)
api.add_resource(VistaEntregas, '/entregas')
api.add_resource(VistaEntrega, '/entrega/<int:id_entrega>')
api.add_resource(VistaConfirmarEntrega, '/entrega/<int:id_entrega>/confirmar')
api.add_resource(VistaTareaDetail, '/tarea', '/tarea/<string:task_id>')
api.add_resource(VistaTareas, '/tareas')

# Configurar JWT
jwt = JWTManager(app)

# Agregar health check
add_health_check(app, 'logistica_inventario')

# Nota: Este microservicio usa el task_dispatcher para enviar tareas
# NO importa directamente las definiciones de tareas para evitar dependencias circulares