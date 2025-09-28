from functools import wraps
import os
from flask import current_app, g, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
import bcrypt
import hashlib
import hmac
import json
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as crypto_padding
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Password Utilities ---
def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def compare_password(stored_password: str, provided_password: str) -> bool:
    """Compare a stored hashed password with a provided password."""
    return bcrypt.checkpw(
        provided_password.encode("utf-8"), stored_password.encode("utf-8")
    )


def sign_data(secret_key: str, data: dict) -> str:
    """Sign data using a shared secret key (HMAC)."""
    data_str = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        secret_key.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha512
    ).hexdigest()
    logger.info("🔏 Data signed with HMAC")
    return signature


def validate_signature(secret_key: str, data: dict, signature: str) -> bool:
    """Validate the signature of the data using the shared secret key (HMAC)."""
    data_str = json.dumps(data, sort_keys=True)
    expected_signature = hmac.new(
        secret_key.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha512
    ).hexdigest()
    logger.info("🔏 Data signature validating")
    return hmac.compare_digest(expected_signature, signature)


# --- Encryption Utilities ---
from typing import Union


def encrypt(obj: Union[dict, str], encryption_key: str = "default") -> str:
    """Encrypt text using AES-256."""
    text = json.dumps(obj) if isinstance(obj, dict) else obj

    if not text:
        return text

    loaded_key = current_app.config.get("PRIVATE_KEY", "default")

    key = hashlib.sha256(loaded_key.encode("utf-8")).digest()
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = crypto_padding.PKCS7(128).padder()
    padded_text = padder.update(text.encode("utf-8")) + padder.finalize()
    encrypted = encryptor.update(padded_text) + encryptor.finalize()
    logger.info("🔒 Data encrypted")
    return f"{iv.hex()}:{encrypted.hex()}"


def decrypt(encrypted_text: str, encryption_key: str = "default") -> Union[dict, str]:
    """Decrypt text using AES-256."""

    if not encrypted_text:
        return {}

    loaded_key = current_app.config.get("PRIVATE_KEY", "default")

    key = hashlib.sha256(loaded_key.encode("utf-8")).digest()
    iv_hex, encrypted_hex = encrypted_text.split(":")
    iv = bytes.fromhex(iv_hex)
    encrypted = bytes.fromhex(encrypted_hex)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    unpadder = crypto_padding.PKCS7(128).unpadder()
    decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    decoded_decrypted = decrypted.decode("utf-8")
    logger.info("🔓 Data decrypted")
    try:
        return json.loads(decoded_decrypted)
    except json.JSONDecodeError:
        return decoded_decrypted


# --- Flask Context Utilities ---
def with_app_context(app):
    """Decorator to run a function within the Flask app context."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)

        return wrapper

    return decorator


def required_signed_celery_message(kwargs):
    """Validate that the kwargs contain a valid signed_celery_message."""
    signed_message = kwargs.get("signed_celery_message", None)
    if not signed_message:
        raise ValueError("signed_celery_message is required in kwargs")

    is_valid = validate_signature(
        os.getenv("CELERY_SIGNING_KEY", ""),
        kwargs.get("info_internal", {}),
        signed_message,
    )

    if not is_valid:
        raise ValueError("Invalid signed_celery_message")

    logger.info("✅ Valid signed_celery_message")
    return True


# --- API Protection Utilities ---
def validate_api_key(api_key: str, required: bool) -> bool:
    """Validate the API key."""
    loaded_key = os.getenv("API_KEY")
    if required and not loaded_key:
        raise ValueError("API key not configured on the server")
    return api_key == loaded_key


def validate_jwt(roles_required: list) -> None:
    """Validate the JWT and check roles."""
    verify_jwt_in_request()
    jwt_info = get_jwt().get("sub", {})
    roles = jwt_info.get("roles", "").split(",")
    if roles_required and not set(roles_required).intersection(roles):
        raise PermissionError("Insufficient permissions")


def api_protect(options):
    """
    Decorator to protect endpoints with API key or JWT authentication.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_required = options.get("jwt_required", False)
            api_key_required = options.get("api_key_required", False)
            roles_required = options.get("roles_required", [])

            jwt_header = request.headers.get("Authorization")
            api_key = request.headers.get("i-api-key")

            if jwt_required and not jwt_header:
                return {"error": "JWT required"}, 401
            if api_key_required and not api_key:
                return {"error": "API key required"}, 401
            if not jwt_header and not api_key:
                return {"error": "Authentication required (JWT or API key)"}, 401

            g.is_api_key_validated_var = False
            g.is_jwt_validated_var = False

            try:
                if api_key and validate_api_key(api_key, api_key_required):
                    g.is_api_key_validated_var = True
                    logger.info("🔑 API key validated")
                if jwt_header:
                    validate_jwt(roles_required)
                    g.is_jwt_validated_var = True
                    logger.info("🛂 JWT validated")
            except ValueError as e:
                return {"error": str(e)}, 500
            except PermissionError as e:
                return {"error": str(e)}, 403

            return current_app.ensure_sync(func)(*args, **kwargs)

        return wrapper

    return decorator


def get_api_protect_validation_result():
    """Get the validation results for API key and JWT."""
    return {
        "is_api_key_validated": getattr(g, "is_api_key_validated_var", False),
        "is_jwt_validated": getattr(g, "is_jwt_validated_var", False),
        "jwt_info": get_jwt() if getattr(g, "is_jwt_validated_var", False) else None,
    }
