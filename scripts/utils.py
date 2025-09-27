from functools import wraps
import os
from urllib import request
import bcrypt
from flask import current_app, g, request   

def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def compare_password(stored_password: str, provided_password: str) -> bool:
    """Compare a stored hashed password with a provided password."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))


def api_key_required(optional=False, key=None):
    """
    Decorador para verificar la presencia de un API key en las solicitudes.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get("api-key")
            if not optional and (not api_key or api_key != key):
                return {"error": "API key requerida"}, 401
            return current_app.ensure_sync(func)(*args, **kwargs)
        
        return wrapper
    return decorator

def api_require_some_auth():
    """
    Decorador para verificar que la solicitud tenga al menos un método de autenticación válido:
    - JWT válido
    - API key válida
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_header = request.headers.get("Authorization", None)
            api_key = request.headers.get("api-key", None)

            if not (jwt_header or api_key):
                return {"error": "Se requiere autenticación válida (JWT o API key)"}, 401

            return current_app.ensure_sync(func)(*args, **kwargs)
        
        return wrapper
    return decorator