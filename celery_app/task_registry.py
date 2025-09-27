"""
Registro central de tareas disponibles
NO importa código, solo define metadatos
"""

TASK_REGISTRY = {
    # Tareas de Logística
    'logistica.procesar_entrega': {
        'description': 'Procesa una entrega específica',
        'params': ['entrega_id', 'status', '_retry_count', 'confirmacion_info'],
        'queue': 'logistica',
        'timeout': 300,
        'module': 'microservices.logistica_inventario.tasks'
    },
    'logistica.validar_inventario': {
        'description': 'Valida disponibilidad en inventario',
        'params': ['producto_id', 'cantidad'],
        'queue': 'logistica',
        'timeout': 60,
        'module': 'microservices.logistica_inventario.tasks'
    },
    'logistica.generar_reporte': {
        'description': 'Genera reporte de entregas',
        'params': ['fecha_inicio', 'fecha_fin'],
        'queue': 'logistica',
        'timeout': 600,
        'module': 'microservices.logistica_inventario.tasks'
    },
    
    # Tareas de Monitor
    'monitor.health_check': {
        'description': 'Verifica salud de servicios',
        'params': [],
        'queue': 'monitor',
        'timeout': 30,
        'module': 'microservices.monitor.tasks'
    },
    'monitor.log_activity': {
        'description': 'Registra actividad del sistema',
        'params': ['activity_data'],
        'queue': 'monitor',
        'timeout': 60,
        'module': 'microservices.monitor.tasks'
    },
    'monitor.generate_metrics': {
        'description': 'Genera métricas del sistema',
        'params': [],
        'queue': 'monitor',
        'timeout': 120,
        'module': 'microservices.monitor.tasks'
    },
    'monitor.ping_logistica': {
        'description': 'Ping echo al microservicio de Logística e Inventarios',
        'params': [],
        'queue': 'monitor',
        'timeout': 5,
        'module': 'microservices.monitor.tasks'
    }
}

def get_task_info(task_name):
    """Obtiene información de una tarea sin importar código"""
    return TASK_REGISTRY.get(task_name)

def list_available_tasks():
    """Lista todas las tareas disponibles"""
    return list(TASK_REGISTRY.keys())

def get_tasks_by_queue(queue_name):
    """Obtiene tareas por cola"""
    return [
        task_name for task_name, info in TASK_REGISTRY.items()
        if info.get('queue') == queue_name
    ]

def validate_task_params(task_name, params):
    """Valida que los parámetros sean correctos para una tarea"""
    task_info = get_task_info(task_name)
    if not task_info:
        return False, f"Tarea '{task_name}' no encontrada"
    
    expected_params = task_info.get('params', [])
    if len(params) != len(expected_params):
        return False, f"Se esperan {len(expected_params)} parámetros, recibidos {len(params)}"
    
    return True, "Parámetros válidos"
