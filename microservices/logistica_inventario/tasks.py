"""
Definición de tareas de logística que serán auto-descubiertas por el worker
"""

from functools import wraps
import os
import time
import random
import requests
from datetime import datetime
from microservices.logistica_inventario.modelos import db, Entrega
from microservices.logistica_inventario import app
from scripts.utils import encrypt, required_signed_celery_message, with_app_context

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


def _retry_task_via_api(
    entrega_id, current_retry=0, max_retries=3, confirmacion_info=None
):
    """
    Realiza un retry automático llamando a la API
    """
    if current_retry >= max_retries:
        print(
            f"❌ [LOGISTICA] Máximo de reintentos alcanzado para entrega {entrega_id}"
        )
        return {
            "entrega_id": entrega_id,
            "status": "FAILED_MAX_RETRIES",
            "timestamp": datetime.now().isoformat(),
            "retry_count": current_retry,
            "error": "Excedido máximo de reintentos",
        }

    try:
        # Esperar un poco antes del reintento
        time.sleep(random.uniform(0, 0.1) ** current_retry)  # Backoff exponencial

        print(
            f"🔄 [LOGISTICA] Reintentando entrega {entrega_id} (intento {current_retry + 1}/{max_retries})"
        )

        # Llamar a la API para reenviar la tarea
        api_url = "http://m-logistica-inventario:5002/tareas"
        payload = {
            "tipo": "procesar_entrega",
            "entrega_id": entrega_id,
            "_retry_count": current_retry + 1,
            "confirmacion_info": confirmacion_info,
        }

        response = requests.post(
            api_url,
            json=payload,
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "i-api-key": os.getenv("API_KEY", "secret"),
            },
        )

        if response.status_code in [200, 202]:
            result = response.json()
            print(f"✅ [LOGISTICA] Reintento enviado para entrega {entrega_id}")
            return {
                "entrega_id": entrega_id,
                "status": "RETRY_SUBMITTED",
                "timestamp": datetime.now().isoformat(),
                "retry_count": current_retry + 1,
                "task_id": result.get("task_id"),
                "original_response": result,
            }
        else:
            print(f"⚠️ [LOGISTICA] Error en reintento API: {response.status_code}")
            return _retry_task_via_api(
                entrega_id,
                current_retry + 1,
                max_retries,
                confirmacion_info=confirmacion_info,
            )

    except Exception as e:
        print(f"⚠️ [LOGISTICA] Error en reintento: {str(e)}")
        return _retry_task_via_api(
            entrega_id,
            current_retry + 1,
            max_retries,
            confirmacion_info=confirmacion_info,
        )


# Implementaciones de las tareas
@with_app_context(app)
def procesar_entrega_impl(
    entrega_id, status, _retry_count=0, confirmacion_info=None, **kwargs
):
    """Procesa una entrega específica con mecanismo de retry automático"""
    required_signed_celery_message(kwargs=kwargs)
    print(
        f"🚚 [LOGISTICA] Procesando entrega {entrega_id} con estado {status} (retry: {_retry_count})"
    )
    time.sleep(random.uniform(0, 1))  # Simular trabajo

    entrega = db.session.query(Entrega).get(entrega_id)

    if not entrega:
        print(f"❌ [LOGISTICA] Entrega {entrega_id} no encontrada")
        return {
            "error": "Entrega no encontrada",
            "entrega_id": entrega_id,
            "timestamp": datetime.now().isoformat(),
            "worker": "logistica_worker",
        }

    if not confirmacion_info:
        print(
            f"❌ [LOGISTICA] confirmacion_info es requerido para entrega {entrega_id}"
        )
        return {
            "error": "confirmacion_info es requerido",
            "entrega_id": entrega_id,
            "timestamp": datetime.now().isoformat(),
            "worker": "logistica_worker",
        }

    if status == "PENDING_SYSTEM_CONFIRMATION":
        print(f"⚠️ [LOGISTICA] Sistema no disponible para entrega {entrega_id}")

        entrega.estado = "PENDING_SYSTEM_CONFIRMATION"
        db.session.commit()

        result = {
            "entrega_id": entrega_id,
            "status": "PENDING_SYSTEM_CONFIRMATION",
            "timestamp": datetime.now().isoformat(),
            "worker": "logistica_worker",
            "retry_count": _retry_count,
            "message": "Sistema temporalmente no disponible, reintentando automáticamente...",
        }

        # Realizar retry automático en background
        retry_result = _retry_task_via_api(
            entrega_id, _retry_count, confirmacion_info=confirmacion_info
        )
        result["retry_info"] = retry_result
        # En reintentos, devolver error si sigue fallando
        return result

    # Procesamiento exitoso
    entrega.estado = "ENTREGADA"
    entrega.fecha_entrega = datetime.now()
    entrega.direccion = (
        encrypt(confirmacion_info.get("direccion", None))
        if confirmacion_info.get("direccion", None)
        else None
    )
    entrega.nombre_recibe = (
        encrypt(confirmacion_info.get("nombre_recibe", None))
        if confirmacion_info.get("nombre_recibe", None)
        else None
    )
    entrega.firma_recibe = (
        encrypt(confirmacion_info.get("firma_recibe", None))
        if confirmacion_info.get("firma_recibe", None)
        else None
    )
    entrega.integridad_firma = confirmacion_info.get("firma_payload", None)

    db.session.commit()
    result = {
        "entrega_id": entrega_id,
        "status": "ENTREGADA",
        "timestamp": datetime.now().isoformat(),
        "worker": "logistica_worker",
        "retry_count": _retry_count,
        "detalles": {
            "validado": True,
            "costo_calculado": 150.00,
            "tiempo_estimado": "2-3 días hábiles",
        },
    }

    print(f"✅ [LOGISTICA] Entrega {entrega_id} procesada exitosamente")
    return result


def validar_inventario_impl(producto_id, cantidad):
    """Valida disponibilidad en inventario"""
    print(
        f"📦 [LOGISTICA] Validando inventario: producto {producto_id}, cantidad {cantidad}"
    )
    time.sleep(1)

    # Simulación de validación
    stock_disponible = 100
    disponible = cantidad <= stock_disponible

    result = {
        "producto_id": producto_id,
        "cantidad_solicitada": cantidad,
        "stock_disponible": stock_disponible,
        "disponible": disponible,
        "timestamp": datetime.now().isoformat(),
        "worker": "logistica_worker",
    }

    print(f"✅ [LOGISTICA] Validación completada - Disponible: {disponible}")
    return result


def generar_reporte_impl(fecha_inicio=None, fecha_fin=None):
    """Genera reporte de entregas"""
    if not fecha_inicio:
        fecha_inicio = datetime.now().strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")

    print(f"📊 [LOGISTICA] Generando reporte: {fecha_inicio} - {fecha_fin}")
    time.sleep(5)

    result = {
        "reporte_id": f"RPT_{fecha_inicio}_{fecha_fin}",
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "entregas_procesadas": 42,
        "ingresos_total": 15750.50,
        "timestamp": datetime.now().isoformat(),
        "worker": "logistica_worker",
    }

    print(f"✅ [LOGISTICA] Reporte generado exitosamente: {result['reporte_id']}")
    return result


# Registrar tareas con nombres específicos
procesar_entrega = _register_task(procesar_entrega_impl, "logistica.procesar_entrega")
validar_inventario = _register_task(
    validar_inventario_impl, "logistica.validar_inventario"
)
generar_reporte = _register_task(generar_reporte_impl, "logistica.generar_reporte")

print("✓ Tareas de logística registradas")
