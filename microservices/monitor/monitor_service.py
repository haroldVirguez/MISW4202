import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

from flask import jsonify
import redis
import requests
import time
from datetime import datetime

# Importar configuración compartida
from shared import create_app, add_health_check
# Removed setup_cors - CORS is handled by nginx API Gateway

# Crear la aplicación usando la configuración compartida
app = create_app(service_name='monitor')

# CORS is handled by nginx API Gateway - no need to setup here

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

@app.route('/monitor/ping-logistica', methods=['GET'])
def ping_logistica():
    """Ping echo al microservicio de Logística e Inventarios"""
    try:
        start_time = time.time()
        
        health_url = "http://m-logistica-inventario:5002/health"
        health_response = requests.get(health_url, timeout=1)
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        if health_response.status_code == 200:
            status = "healthy"
            message = "Servicio de logística funcionando correctamente"
        else:
            status = "degraded"
            message = f"Servicio de logística con problemas - código {health_response.status_code}"
            
        return jsonify({
            'target_service': 'logistica_inventario',
            'status': status,
            'message': message,
            'response_time_ms': response_time,
            'http_status': health_response.status_code,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'ping_successful': health_response.status_code == 200
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'target_service': 'logistica_inventario',
            'status': 'timeout',
            'message': 'Timeout en confirmación de entrega - sistema enmascarando falla y procesando asíncronamente en Broker de mensajería',
            'response_time_ms': 2000,
            'http_status': None,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'ping_successful': False
        }), 408
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            'target_service': 'logistica_inventario',
            'status': 'unreachable',
            'message': 'Error de conexión al microservicio de logística - sistema enmascarando falla y procesando asíncronamente en Broker de mensajería',
            'response_time_ms': None,
            'http_status': None,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'ping_successful': False
        }), 503
        
    except Exception as e:
        return jsonify({
            'target_service': 'logistica_inventario',
            'status': 'error',
            'message': f'Error inesperado: {str(e)}',
            'response_time_ms': None,
            'http_status': None,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'ping_successful': False
        }), 500

@app.route('/monitor/logistica-status', methods=['GET'])
def logistica_status():
    """Estado detallado del microservicio de Logística e Inventarios"""
    try:
        ping_result = ping_logistica()
        ping_data = ping_result.get_json()
        is_healthy = ping_data.get('ping_successful', False)
    
        broker_status = check_broker_connectivity()
        
        if is_healthy and broker_status['redis_connected']:
            overall_status = 'healthy'
        elif broker_status['redis_connected']:
            overall_status = 'degraded'
        else:
            overall_status = 'critical'
            
        return jsonify({
            'service': 'logistica_inventario',
            'overall_status': overall_status,
            'ping_echo': ping_data,
            'broker_status': broker_status,
            'last_check': datetime.now().isoformat(),
            'recommendations': get_recommendations(overall_status)
        })
        
    except Exception as e:
        return jsonify({
            'service': 'logistica_inventario',
            'overall_status': 'error',
            'error': str(e),
            'last_check': datetime.now().isoformat()
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

def check_broker_connectivity():
    """Verifica la conectividad del broker de mensajería (Redis)"""
    try:
        redis_ping = redis_client.ping()
        celery_queues = ['celery', 'logistica', 'monitor']
        queue_status = {}
        
        for queue in celery_queues:
            try:
                queue_length = redis_client.llen(queue)
                queue_status[queue] = {
                    'length': queue_length,
                    'accessible': True
                }
            except Exception:
                queue_status[queue] = {
                    'length': 0,
                    'accessible': False
                }
        
        return {
            'redis_connected': redis_ping,
            'redis_ping': redis_ping,
            'queues': queue_status,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'redis_connected': False,
            'redis_ping': False,
            'error': str(e),
            'queues': {},
            'timestamp': datetime.now().isoformat()
        }

def get_recommendations(status):
    """Genera recomendaciones basadas en el estado del servicio"""
    recommendations = []
    
    if status == 'healthy':
        recommendations.append("✅ Servicio funcionando correctamente")
        recommendations.append("🔄 Continuar monitoreo regular")
    elif status == 'degraded':
        recommendations.append("⚠️ Servicio con problemas de conectividad")
        recommendations.append("🔍 Verificar logs del microservicio de logística")
        recommendations.append("🔄 Reintentar operaciones fallidas")
    elif status == 'critical':
        recommendations.append("🚨 Servicio crítico - Acción inmediata requerida")
        recommendations.append("🔄 Reiniciar microservicio de logística")
        recommendations.append("📞 Notificar al equipo de operaciones")
        recommendations.append("💾 Verificar integridad de datos")
    else:
        recommendations.append("❓ Estado desconocido - Investigar")
        recommendations.append("🔍 Revisar logs del sistema")
    
    return recommendations

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
