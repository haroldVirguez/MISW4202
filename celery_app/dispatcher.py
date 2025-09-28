"""
Task Dispatcher - Desacoplamiento para el envío de tareas asíncronas

Este módulo proporciona una interfaz uniforme para enviar tareas sin
tener dependencias directas del código de las tareas.
Usa la instancia de Celery específica para Flask.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from celery.result import AsyncResult

from scripts.utils import sign_data
from .client import flask_celery
from .task_registry import list_available_tasks, get_task_info, validate_task_params
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskDispatcher:
    """
    Dispatcher para enviar tareas asíncronas sin acoplamiento directo
    Usa la instancia de Celery específica para Flask
    """

    def __init__(self):
        self.celery = flask_celery
        logger.info("✓ TaskDispatcher configurado con flask_celery")

    def dispatch_task(self, task_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Envía una tarea usando la instancia de Flask Celery

        Args:
            task_name: Nombre completo de la tarea (ej: 'logistica.procesar_entrega')
            *args: Argumentos posicionales para la tarea
            **kwargs: Argumentos nombrados para la tarea

        Returns:
            Dict con información de la tarea enviada
        """
        if not self.celery:
            return {
                "error": "Celery no disponible",
                "task_name": task_name,
                "status": "FAILED",
            }

        task_info = get_task_info(task_name)
        if not task_info:
            return {
                "error": f"Tarea '{task_name}' no encontrada en el registro",
                "task_name": task_name,
                "status": "FAILED",
            }

        # Validar parámetros
        is_valid, validation_msg = validate_task_params(task_name, args)
        if not is_valid:
            return {
                "error": f"Parámetros inválidos: {validation_msg}",
                "task_name": task_name,
                "status": "FAILED",
            }
        kwargs = {
            **(kwargs or {}),
            "signed_celery_message": sign_data(
                os.getenv("CELERY_SIGNING_KEY", ""),
                {"task_name": task_name, "args": args},
            ),
            "info_internal": {"task_name": task_name, "args": args},
        }
        try:
            # Enviar tarea usando Celery (por nombre)
            result = self.celery.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                queue=task_info.get("queue", "celery"),
            )

            return {
                "task_id": result.id,
                "task_name": task_name,
                "status": "PENDING",
                "queue": task_info.get("queue", "celery"),
                "timestamp": datetime.now().isoformat(),
                "args": args,
                "kwargs": kwargs,
            }

        except Exception as e:
            return {"error": str(e), "task_name": task_name, "status": "FAILED"}

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el resultado completo de una tarea"""
        if not self.celery:
            return {"error": "Celery no disponible", "task_id": task_id}

        try:
            result = AsyncResult(task_id, app=self.celery)

            response = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "timestamp": datetime.now().isoformat(),
            }

            if result.ready():
                if result.successful():
                    response["result"] = result.result
                else:
                    response["error"] = str(result.result)
            else:
                # Para tareas en progreso
                if isinstance(result.info, dict):
                    response.update(result.info)

            return response

        except Exception as e:
            return {"task_id": task_id, "status": "ERROR", "error": str(e)}

    def get_task_status(self, task_id: str) -> str:
        """Obtiene solo el estado de una tarea"""
        if not self.celery:
            return "ERROR"

        try:
            result = AsyncResult(task_id, app=self.celery)
            return result.status
        except Exception:
            return "ERROR"

    def list_available_tasks(self) -> list:
        """Lista tareas disponibles"""
        return list_available_tasks()

    def list_tasks_from_redis(self) -> list:
        """Lista todas las tareas: activas, pendientes, reservadas y completadas"""
        logger.info("Listando tareas desde Redis backend")
        if not self.celery:
            return []

        all_tasks = []

        try:
            # 1. Obtener tareas activas/pendientes/reservadas usando inspect
            i = self.celery.control.inspect()

            # Tareas activas (en ejecución)
            active = i.active()
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        task["worker"] = worker
                        task["state"] = "ACTIVE"
                        all_tasks.append(task)

            # Tareas pendientes (en cola)
            scheduled = i.scheduled()
            if scheduled:
                for worker, tasks in scheduled.items():
                    for task in tasks:
                        task["worker"] = worker
                        task["state"] = "SCHEDULED"
                        all_tasks.append(task)

            # Tareas reservadas
            reserved = i.reserved()
            if reserved:
                for worker, tasks in reserved.items():
                    for task in tasks:
                        task["worker"] = worker
                        task["state"] = "RESERVED"
                        all_tasks.append(task)

            logger.info(
                f"Tareas activas/pendientes/reservadas encontradas: {len(all_tasks)}"
            )

        except Exception as e:
            logger.error(f"Error obteniendo tareas activas: {e}")

        try:
            # 2. Obtener tareas completadas desde el backend de resultados
            backend = self.celery.backend

            if hasattr(backend, "client") and backend.client:
                # Para Redis backend
                try:
                    keys = backend.client.keys("celery-task-meta-*")
                    logger.info(f"Claves encontradas en Redis backend: {len(keys)}")

                    for key in keys[:100]:  # Limitar a 100 para evitar sobrecarga
                        try:
                            if isinstance(key, bytes):
                                key_str = key.decode("utf-8")
                            else:
                                key_str = str(key)

                            task_id = key_str.replace("celery-task-meta-", "")

                            # Usar AsyncResult para obtener información completa
                            result = AsyncResult(task_id, app=self.celery)

                            # Obtener metadatos del resultado
                            task_meta = backend.client.get(key)
                            if task_meta:
                                import json

                                try:
                                    meta_data = json.loads(task_meta.decode("utf-8"))

                                    task_info = {
                                        "id": task_id,
                                        "name": meta_data.get("task_name", "unknown"),
                                        "state": result.status,
                                        "result": meta_data.get("result"),
                                        "args": meta_data.get("args", []),
                                        "kwargs": meta_data.get("kwargs", {}),
                                        "received": meta_data.get("date_received"),
                                        "finished": meta_data.get("date_done"),
                                        "worker": "completed",
                                        "source": "result_backend",
                                        "metadata": meta_data,
                                    }

                                    all_tasks.append(task_info)

                                except json.JSONDecodeError:
                                    # Si no se puede parsear JSON, usar información básica
                                    all_tasks.append(
                                        {
                                            "id": task_id,
                                            "name": "unknown",
                                            "state": result.status,
                                            "result": (
                                                str(result.result)
                                                if result.ready()
                                                else None
                                            ),
                                            "args": [],
                                            "kwargs": {},
                                            "worker": "completed",
                                            "source": "result_backend",
                                        }
                                    )

                        except Exception as task_error:
                            logger.error(
                                f"Error procesando tarea {task_id}: {task_error}"
                            )
                            continue

                except Exception as redis_error:
                    logger.error(f"Error accediendo a Redis backend: {redis_error}")

            else:
                logger.warning("Backend no es Redis o no tiene cliente disponible")

        except Exception as e:
            logger.error(f"Error obteniendo tareas completadas: {e}")

        logger.info(f"Total de tareas encontradas: {len(all_tasks)}")
        return all_tasks


# Instancia global del dispatcher
task_dispatcher = TaskDispatcher()


# Funciones de conveniencia para tareas específicas
class LogisticaTasks:
    """Wrapper para tareas de logística sin importar código directo"""

    @staticmethod
    def procesar_entrega(
        entrega_id: int,
        status: str,
        retry_count: int = 0,
        confirmacion_info: dict = {},
        **options,
    ):
        return task_dispatcher.dispatch_task(
            "logistica.procesar_entrega",
            entrega_id,
            status,
            retry_count,
            confirmacion_info,
            **options,
        )

    @staticmethod
    def validar_inventario(producto_id: int, cantidad: int, **options):
        return task_dispatcher.dispatch_task(
            "logistica.validar_inventario", producto_id, cantidad, **options
        )

    @staticmethod
    def generar_reporte(
        fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None, **options
    ):
        return task_dispatcher.dispatch_task(
            "logistica.generar_reporte", fecha_inicio, fecha_fin, **options
        )


class MonitorTasks:
    """Wrapper para tareas de monitoreo"""

    @staticmethod
    def health_check(**options):
        return task_dispatcher.dispatch_task("monitor.health_check", **options)

    @staticmethod
    def log_activity(activity_data: dict, **options):
        return task_dispatcher.dispatch_task(
            "monitor.log_activity", activity_data, **options
        )

    @staticmethod
    def generate_metrics(**options):
        return task_dispatcher.dispatch_task("monitor.generate_metrics", **options)
