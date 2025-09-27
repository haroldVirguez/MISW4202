"""
Configuración compartida para microservicios Flask
Este módulo proporciona funciones reutilizables para configurar Flask
"""

from flask import Flask, request, jsonify
import logging
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
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(service_name)

    # Log incoming requests
    @app.before_request
    def log_request():
        logger.info(f"Incoming request: {request.method} {request.path}")
        content_type = request.content_type

        if content_type and "application/json" in content_type:  # Check if Content-Type is JSON
            try:
                logger.info(f"Payload: {request.get_json()}")
            except Exception as e:
                logger.warning(f"Failed to parse JSON payload: {e}")
        elif request.form:  # Handle form data
            logger.info(f"Form data: {request.form}")
        elif request.args:  # Handle query parameters
            logger.info(f"Query params: {request.args}")
        else:
            logger.info("No JSON payload or form data found in the request.")

    # Log outgoing responses
    @app.after_request
    def log_response(response):
        logger.info(f"Response status: {response.status}")
        try:
            if response.is_json:  # Check if the response is JSON
                logger.info(f"Response JSON: {response.get_json()}")
            else:
                logger.info("Response is not JSON.")
        except Exception as e:
            logger.warning(f"Failed to log response body: {e}")
        return response

    # Configuración de base de datos
    db_uri = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///misw4202.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Configuración JWT
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "frase-secreta")
    app.config["PROPAGATE_EXCEPTIONS"] = True

    # Configuración específica del servicio
    app.config["SERVICE_NAME"] = service_name

    # Aplicar configuraciones adicionales si se proporcionan
    if config_overrides:
        app.config.update(config_overrides)

    return app


def add_health_check(app, service_name=None):
    """
    Agregar endpoint de health check genérico

    Args:
        app (Flask): Instancia de Flask
        service_name (str): Nombre del servicio (opcional, usa SERVICE_NAME del config si no se proporciona)
    """
    if not service_name:
        service_name = app.config.get("SERVICE_NAME", "unknown")

    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": service_name, "version": "1.0.0"}


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
