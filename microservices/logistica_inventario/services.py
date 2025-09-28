from datetime import datetime
import os
import random
from celery_app.dispatcher import LogisticaTasks
from microservices.callers.m_callers import call_ms
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_procesar_entrega(entrega_id, retry_count=0, confirmacion_info=None):
    """
    Procesa la entrega de manera síncrona.
    """
    if not entrega_id:
        return {"error": "entrega_id es requerido"}, 400

    if not confirmacion_info:
        return {"error": "confirmacion_info es requerido"}, 400

    if not confirmacion_info.get("usuario_id"):
        return {"error": "usuario_id es requerido en confirmacion_info"}, 400
    
    if not confirmacion_info.get("direccion"):
        return {"error": "direccion es requerido en confirmacion_info"}, 400
    if not confirmacion_info.get("nombre_recibe"):
        return {"error": "nombre_recibe es requerido en confirmacion_info"}, 400
    if not confirmacion_info.get("firma_recibe"):
        return {"error": "firma_recibe es requerido en confirmacion_info"}, 400
    if not confirmacion_info.get("firma_payload"):
        return {"error": "firma_payload es requerido en confirmacion_info"}, 400
    if not confirmacion_info.get("pedido_id"):
        return {"error": "pedido_id es requerido en confirmacion_info"}, 400
    if not confirmacion_info.get("entrega_id"):
        return {"error": "entrega_id es requerido en confirmacion_info"}, 400

    (response, status_code) = call_ms(
        "autorizador",
        "/validate-signature",
        method="post",
        data={
            "payload": {
                "direccion": confirmacion_info.get("direccion"),
                "nombre_recibe": confirmacion_info.get("nombre_recibe"),
                "firma_recibe": confirmacion_info.get("firma_recibe"),
                "pedido_id": confirmacion_info.get("pedido_id"),
                "usuario_id": confirmacion_info.get("usuario_id"),
                "entrega_id": confirmacion_info.get("entrega_id"),
            },
            "firma": confirmacion_info.get("firma_payload"),
        },
        headers={"Content-Type": "application/json", "i-api-key": os.getenv("API_KEY")},
    )
    
    is_valid = response.get("data", {}).get("firma_valida") if status_code == 200 else False
    
    if not is_valid:
        return {"error": "Firma no válida"}, 403
    
    try:

        # Para tareas nuevas, aplicar la lógica de falla aleatoria
        if random.random() < 0.5:
            raise Exception("Sistema temporalmente no disponible")

        task_result = LogisticaTasks.procesar_entrega(
            entrega_id, "ENTREGADA", retry_count, confirmacion_info
        )

        return {
            "message": "Tarea enviada",
            "entrega_id": entrega_id,
            "estado": "exitoso",
            "timestamp": datetime.utcnow().isoformat(),
            **task_result,
        }, 200

    except Exception as e:
        task_result = LogisticaTasks.procesar_entrega(
            entrega_id, "PENDING_SYSTEM_CONFIRMATION", retry_count, confirmacion_info
        )
        return {
            "message": "Tarea enviada",
            "entrega_id": entrega_id,
            "estado": "Pendiente Confirmacion Sistema",
            "timestamp": datetime.utcnow().isoformat(),
            **task_result,
        }, 200
