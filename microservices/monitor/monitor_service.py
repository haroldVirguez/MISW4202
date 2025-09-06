import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask import jsonify
import redis
from datetime import datetime

# Importar configuración compartida
from shared import create_app, add_health_check, setup_cors

# Crear la aplicación usando la configuración compartida
app = create_app(service_name='monitor')

# Configurar CORS - DESACTIVADO porque el API Gateway maneja CORS
# setup_cors(app)

# Configuración de Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    decode_responses=True
)

# Agregar health check personalizado con timestamp
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud del servicio monitor"""
    return jsonify({
        'status': 'healthy',
        'service': 'monitor',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/monitor/status', methods=['GET'])
def monitor_status():
    """Monitorea el estado de los servicios"""
    try:
        # Verificar conexión a Redis
        redis_status = redis_client.ping()
        
        # Obtener información de Celery
        celery_info = get_celery_info()
        
        return jsonify({
            'redis': {
                'status': 'connected' if redis_status else 'disconnected',
                'ping': redis_status
            },
            'celery': celery_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/monitor/queue', methods=['GET'])
def queue_info():
    """Información sobre las colas de Celery"""
    try:
        # Obtener información de las colas de Redis
        queue_info = {}
        
        # Lista de colas conocidas de Celery
        celery_queues = ['celery']
        
        for queue in celery_queues:
            queue_length = redis_client.llen(queue)
            queue_info[queue] = {
                'length': queue_length,
                'status': 'active' if queue_length > 0 else 'idle'
            }
        
        return jsonify({
            'queues': queue_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/monitor/workers', methods=['GET'])
def workers_info():
    """Información sobre los workers de Celery"""
    try:
        # Obtener estadísticas de workers activos
        active_workers = get_active_workers()
        
        return jsonify({
            'workers': active_workers,
            'total_workers': len(active_workers),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def get_celery_info():
    """Obtiene información sobre Celery desde Redis"""
    try:
        # Buscar keys relacionadas con Celery
        celery_keys = redis_client.keys('celery*')
        
        return {
            'keys_count': len(celery_keys),
            'status': 'active' if celery_keys else 'inactive'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error'
        }

def get_active_workers():
    """Obtiene información sobre workers activos"""
    try:
        # Buscar workers activos en Redis
        worker_keys = redis_client.keys('_kombu.binding.celery*')
        
        workers = []
        for key in worker_keys:
            workers.append({
                'key': key,
                'status': 'active'
            })
        
        return workers
    except Exception as e:
        return []

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
