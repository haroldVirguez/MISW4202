"""
Archivo de definiciones de tareas simplificado

Este archivo ahora solo contiene referencias a las tareas reales
que están definidas en los módulos de tareas de cada microservicio.
Las tareas reales están en:
- microservices/logistica_inventario/tasks.py
- microservices/monitor/tasks.py

Para el registro de metadatos, ver task_registry.py
Para el dispatcher, ver shared/task_dispatcher.py
Para el worker, ver celery_worker.py
Para el cliente Flask, ver celery_client.py
"""

# Este archivo ya no es necesario con la nueva arquitectura
# Las tareas se registran automáticamente en sus respectivos módulos
# usando el worker_celery para auto-discovery

print("ℹ️  task_definitions.py cargado - usando nueva arquitectura desacoplada")

# Para compatibilidad, podemos importar las funciones de conveniencia
try:
    from shared.task_dispatcher import LogisticaTasks, MonitorTasks, task_dispatcher
    
    # Aliases para mantener compatibilidad con código existente
    procesar_entrega = LogisticaTasks.procesar_entrega
    validar_inventario = LogisticaTasks.validar_inventario
    generar_reporte_entregas = LogisticaTasks.generar_reporte
    
    print("✓ Task dispatcher cargado exitosamente")
    
except ImportError as e:
    print(f"⚠️ Error importando task dispatcher: {e}")
    
    # Funciones stub para evitar errores
    def procesar_entrega(*args, **kwargs):
        return {"error": "Task dispatcher no disponible"}
    
    def validar_inventario(*args, **kwargs):
        return {"error": "Task dispatcher no disponible"}
    
    def generar_reporte_entregas(*args, **kwargs):
        return {"error": "Task dispatcher no disponible"}

