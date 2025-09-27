from datetime import datetime
import random
from celery_app.dispatcher import LogisticaTasks


def sync_procesar_entrega(entrega_id, retry_count=0):
    """
    Procesa la entrega de manera síncrona.
    """
    if not entrega_id:
        return {"error": "entrega_id es requerido"}, 400
    
    try:
        
        # Para tareas nuevas, aplicar la lógica de falla aleatoria
        if random.random() < 0.5:
            raise Exception("Sistema temporalmente no disponible")
        
        task_result = LogisticaTasks.procesar_entrega(entrega_id, 'ENTREGADA', retry_count)

        return {
            "message": "Tarea enviada",
            "entrega_id": entrega_id,
            "estado": "exitoso",
            "timestamp": datetime.utcnow().isoformat(),
            **task_result
        }, 200
        
    except Exception as e:
        task_result = LogisticaTasks.procesar_entrega(entrega_id, 'PENDING_SYSTEM_CONFIRMATION', retry_count)
        return {
            "message": "Tarea enviada",
            "entrega_id": entrega_id,
            "estado": "Pendiente Confirmacion Sistema",
            "timestamp": datetime.utcnow().isoformat(),
            **task_result
        }, 200