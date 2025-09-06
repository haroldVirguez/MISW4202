"""
Configuración Flask específica
"""

from . import create_app, add_health_check, setup_cors

__all__ = ['create_app', 'add_health_check', 'setup_cors']
