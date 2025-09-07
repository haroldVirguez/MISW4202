"""
Tareas de monitoreo que serán auto-descubiertas por el worker
"""
import time
import redis
import os
from datetime import datetime

# Solo importar cuando estamos en el contexto del worker
try:
    from celery_app.worker import worker_celery
    celery_instance = worker_celery
    print("✓ Usando worker_celery para tareas de monitor")
except ImportError:
    
    print("⚠️ worker_celery no disponible")
    celery_instance = None

def _register_task(func, name):
    """Helper para registrar tareas de forma segura"""
    if celery_instance:
        return celery_instance.task(name=name)(func)
    else:
        return func

def health_check_impl():
    """Verifica la salud general del sistema"""
    print("🏥 [MONITOR] Ejecutando health check del sistema")
    
    # Verificar Redis
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=6379,
            decode_responses=True
        )
        redis_status = redis_client.ping()
    except Exception as e:
        print(f"❌ [MONITOR] Error conectando a Redis: {e}")
        redis_status = False
    
    time.sleep(1)
    
    result = {
        'system_status': 'healthy' if redis_status else 'degraded',
        'redis_status': redis_status,
        'timestamp': datetime.now().isoformat(),
        'worker': 'monitor_worker',
        'checks_performed': ['redis_connectivity']
    }
    
    print(f"✅ [MONITOR] Health check completado - Status: {result['system_status']}")
    return result

def log_activity_impl(activity_data):
    """Registra actividad del sistema"""
    print(f"📝 [MONITOR] Registrando actividad: {activity_data}")
    time.sleep(0.5)
    
    # Simular escritura a log
    log_entry = {
        'activity_id': f"ACT_{int(time.time())}",
        'activity_data': activity_data,
        'timestamp': datetime.now().isoformat(),
        'worker': 'monitor_worker',
        'logged': True
    }
    
    print(f"✅ [MONITOR] Actividad registrada: {log_entry['activity_id']}")
    return log_entry

def generate_metrics_impl():
    """Genera métricas del sistema"""
    print("📊 [MONITOR] Generando métricas del sistema")
    time.sleep(2)
    
    # Simular recolección de métricas
    result = {
        'metrics_id': f"MET_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'worker': 'monitor_worker',
        'metrics': {
            'cpu_usage': '25%',
            'memory_usage': '60%',
            'disk_usage': '45%',
            'requests_per_minute': 120,
            'response_time_avg': '180ms',
            'active_tasks': 3
        }
    }
    
    print(f"✅ [MONITOR] Métricas generadas: {result['metrics_id']}")
    return result

def ping_logistica_async_impl():
    """Ping echo asíncrono al microservicio de Logística e Inventarios"""
    print("🏥 [MONITOR] Ejecutando ping echo a Logística e Inventarios")
    
    try:
        import requests
        
        start_time = time.time()
        logistica_url = "http://m-logistica-inventario:5002/health"
        response = requests.get(logistica_url, timeout=2)
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)
        
        if response.status_code == 200:
            status = "healthy"
            message = "Ping exitoso"
            ping_successful = True
        else:
            status = "degraded"
            message = f"Respuesta inesperada: {response.status_code}"
            ping_successful = False
            
        result = {
            'ping_id': f"PING_{int(time.time())}",
            'target_service': 'logistica_inventario',
            'status': status,
            'message': message,
            'response_time_ms': response_time,
            'http_status': response.status_code,
            'timestamp': datetime.now().isoformat(),
            'ping_successful': ping_successful,
            'worker': 'monitor_worker'
        }
        
        print(f"✅ [MONITOR] Ping completado - Status: {status}, Tiempo: {response_time}ms")
        return result
        
    except requests.exceptions.Timeout:
        result = {
            'ping_id': f"PING_{int(time.time())}",
            'target_service': 'logistica_inventario',
            'status': 'timeout',
            'message': 'Timeout: El servicio no respondió en 2 segundos',
            'response_time_ms': 2000,
            'http_status': None,
            'timestamp': datetime.now().isoformat(),
            'ping_successful': False,
            'worker': 'monitor_worker'
        }
        print("❌ [MONITOR] Ping timeout - Servicio no respondió")
        return result
        
    except requests.exceptions.ConnectionError:
        result = {
            'ping_id': f"PING_{int(time.time())}",
            'target_service': 'logistica_inventario',
            'status': 'unreachable',
            'message': 'Error de conexión: El servicio no está disponible',
            'response_time_ms': None,
            'http_status': None,
            'timestamp': datetime.now().isoformat(),
            'ping_successful': False,
            'worker': 'monitor_worker'
        }
        print("❌ [MONITOR] Ping fallido - Servicio no disponible")
        return result
        
    except Exception as e:
        result = {
            'ping_id': f"PING_{int(time.time())}",
            'target_service': 'logistica_inventario',
            'status': 'error',
            'message': f'Error inesperado: {str(e)}',
            'response_time_ms': None,
            'http_status': None,
            'timestamp': datetime.now().isoformat(),
            'ping_successful': False,
            'worker': 'monitor_worker'
        }
        print(f"❌ [MONITOR] Ping error: {str(e)}")
        return result

# Registrar tareas con nombres específicos
health_check = _register_task(health_check_impl, 'monitor.health_check')
log_activity = _register_task(log_activity_impl, 'monitor.log_activity')
generate_metrics = _register_task(generate_metrics_impl, 'monitor.generate_metrics')
ping_logistica_async = _register_task(ping_logistica_async_impl, 'monitor.ping_logistica')

print("✓ Tareas de monitor registradas")
