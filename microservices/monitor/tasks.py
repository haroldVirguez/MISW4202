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
    # Si no está disponible, crear instancia fallback
    print("⚠️ worker_celery no disponible, creando instancia fallback")
    from celery import Celery
    celery_instance = Celery(
        'fallback',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    )

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

# Registrar tareas con nombres específicos
health_check = _register_task(health_check_impl, 'monitor.health_check')
log_activity = _register_task(log_activity_impl, 'monitor.log_activity')
generate_metrics = _register_task(generate_metrics_impl, 'monitor.generate_metrics')

print("✓ Tareas de monitor registradas")
