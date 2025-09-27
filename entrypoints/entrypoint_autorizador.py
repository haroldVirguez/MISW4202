#!/usr/bin/env python3
"""
Ejemplo de entry point para un nuevo microservicio

Para crear un nuevo microservicio, copia este archivo y:
1. Renómbralo: entrypoint_mi_servicio.py
2. Cambia las importaciones para apuntar a tu microservicio
3. Agrega el servicio al docker-compose.yml
"""

import os
import sys

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

if __name__ == '__main__':
    # Importar desde tu microservicio
    from microservices.autorizador import app
    
    # Configurar el host y puerto desde variables de entorno
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5003))  # Cambiar puerto por defecto
    debug = os.getenv('FLASK_ENV') == 'development'
    public_key_path = os.getenv('PUBLIC_KEY_PATH', './public_key.pem')
    private_key_path = os.getenv('PRIVATE_KEY_PATH', './private_key.pem')

    with open(public_key_path, 'r') as pub_file:
        app.config['PUBLIC_KEY'] = pub_file.read()

    with open(private_key_path, 'r') as priv_file:
        app.config['PRIVATE_KEY'] = priv_file.read()

    print(f"Starting Mi Nuevo Microservicio on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
