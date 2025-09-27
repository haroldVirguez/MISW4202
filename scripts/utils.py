from functools import wraps
import os
from urllib import request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
import bcrypt
from flask import current_app, g, request
import hmac
import hashlib
import json   

def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def compare_password(stored_password: str, provided_password: str) -> bool:
    """Compare a stored hashed password with a provided password."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def sign_data(secret_key: str, data: dict) -> str:
    """Sign data using a shared secret key (HMAC)."""
    data_str = json.dumps(data, sort_keys=True)
    signature = hmac.new(secret_key.encode('utf-8'), data_str.encode('utf-8'), hashlib.sha512).hexdigest()
    return signature

def validate_signature(secret_key: str, data: dict, signature: str) -> bool:
    """Validate the signature of the data using the shared secret key (HMAC)."""
    data_str = json.dumps(data, sort_keys=True)
    expected_signature = hmac.new(secret_key.encode('utf-8'), data_str.encode('utf-8'), hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def with_app_context(app):
    """
    Decorador para ejecutar una función dentro del contexto de la aplicación Flask.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_api_protect_validation_result():
    """ 
    Verifica si la solicitud fue autenticada mediante API key válida.
    """
    return {
        'is_api_key_validated': getattr(g, 'is_api_key_validated_var', False),
        'is_jwt_validated': getattr(g, 'is_jwt_validated_var', False),
        'jwt_info': get_jwt() if getattr(g, 'is_jwt_validated_var', False) else None
    }

def api_protect(options):
    """
    Decorador para proteger endpoints con autenticación API key o JWT.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_jwt_required = options.get('jwt_required', False)
            is_api_key_required = options.get('api_key_required', False)
            
            jwt_header = request.headers.get("Authorization", None)
            api_key = request.headers.get("i-api-key", None)
            
            if is_jwt_required and not jwt_header:
                return {"error": "JWT requerido"}, 401
            
            if is_api_key_required and not api_key:
                return {"error": "API key requerida"}, 401
            
            if not jwt_header and not api_key:
                return {"error": "Se requiere autenticación (JWT o API key)"}, 401
            
            g.is_api_key_validated_var = False
            g.is_jwt_validated_var = False
            
            if api_key:
                
                loaded_key = options.get('key') or os.getenv("API_KEY")
                if not loaded_key and is_api_key_required:
                    return {"error": "API key no configurada en el servidor"}, 500
                
                if api_key != loaded_key:
                    return {"error": "API key no válida"}, 403
                g.is_api_key_validated_var = True

            if jwt_header:
                try:
                    verify_jwt_in_request()
                except Exception as e:
                    return {"error": "JWT no válido"}, 403
                
                jwt_info = get_jwt().get("sub", {})
                roles = jwt_info.get("roles", "").split(",")
                roles_required = options.get('roles_required', [])
                if len(roles_required) and not set(roles_required).intersection(set(roles)):
                    return {"error": "No tiene permisos para realizar esta acción"}, 403
                g.is_jwt_validated_var = True

            return current_app.ensure_sync(func)(*args, **kwargs)
        
        return wrapper
    return decorator