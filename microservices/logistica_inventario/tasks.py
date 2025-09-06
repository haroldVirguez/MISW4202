"""
Definición de tareas de logística que serán auto-descubiertas por el worker
"""
import time
from datetime import datetime

# Solo importar cuando estamos en el contexto del worker
try:
    from celery_app.worker import worker_celery
    celery_instance = worker_celery
    print("✓ Usando worker_celery para tareas de logística")
except ImportError:
    print("⚠️ worker_celery no disponible")
    celery_instance = None

def _register_task(func, name):
    """Helper para registrar tareas de forma segura"""
    if celery_instance:
        return celery_instance.task(name=name)(func)
    else:
        # Si no hay celery, devolver la función original
        return func

# Implementaciones de las tareas
def procesar_entrega_impl(entrega_id):
    """Procesa una entrega específica"""
    print(f"🚚 [LOGISTICA] Procesando entrega {entrega_id}")
    time.sleep(2)  # Simular trabajo
    
    result = {
        'entrega_id': entrega_id,
        'status': 'procesada',
        'timestamp': datetime.now().isoformat(),
        'worker': 'logistica_worker',
        'detalles': {
            'validado': True,
            'costo_calculado': 150.00,
            'tiempo_estimado': '2-3 días hábiles'
        }
    }
    
    print(f"✅ [LOGISTICA] Entrega {entrega_id} procesada exitosamente")
    return result

def validar_inventario_impl(producto_id, cantidad):
    """Valida disponibilidad en inventario"""
    print(f"📦 [LOGISTICA] Validando inventario: producto {producto_id}, cantidad {cantidad}")
    time.sleep(1)
    
    # Simulación de validación
    stock_disponible = 100
    disponible = cantidad <= stock_disponible
    
    result = {
        'producto_id': producto_id,
        'cantidad_solicitada': cantidad,
        'stock_disponible': stock_disponible,
        'disponible': disponible,
        'timestamp': datetime.now().isoformat(),
        'worker': 'logistica_worker'
    }
    
    print(f"✅ [LOGISTICA] Validación completada - Disponible: {disponible}")
    return result

def generar_reporte_impl(fecha_inicio=None, fecha_fin=None):
    """Genera reporte de entregas"""
    if not fecha_inicio:
        fecha_inicio = datetime.now().strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
    print(f"📊 [LOGISTICA] Generando reporte: {fecha_inicio} - {fecha_fin}")
    time.sleep(5)
    
    result = {
        'reporte_id': f"RPT_{fecha_inicio}_{fecha_fin}",
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'entregas_procesadas': 42,
        'ingresos_total': 15750.50,
        'timestamp': datetime.now().isoformat(),
        'worker': 'logistica_worker'
    }
    
    print(f"✅ [LOGISTICA] Reporte generado exitosamente: {result['reporte_id']}")
    return result

# Registrar tareas con nombres específicos
procesar_entrega = _register_task(procesar_entrega_impl, 'logistica.procesar_entrega')
validar_inventario = _register_task(validar_inventario_impl, 'logistica.validar_inventario')
generar_reporte = _register_task(generar_reporte_impl, 'logistica.generar_reporte')

print("✓ Tareas de logística registradas")
