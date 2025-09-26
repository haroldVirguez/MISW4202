import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask_jwt_extended import JWTManager

# Importar configuración compartida
from shared import create_app, add_health_check

# Crear la aplicación usando la configuración compartida
app = create_app(service_name='autorizador')

jwt = JWTManager(app)

# Agregar health check
add_health_check(app, 'autorizador')

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5003))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host=host, port=port, debug=debug)


