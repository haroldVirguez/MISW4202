#!/usr/bin/env python3

import os
import sys

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

if __name__ == '__main__':
    from microservices.monitor import app
    
    # Configurar el host y puerto desde variables de entorno
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Monitor microservice on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
