import os
from flask import request
import logging
from scripts.utils import api_protect, decrypt, encrypt, get_api_protect_validation_result
from ..services import sync_procesar_entrega
from ..modelos import db, Entrega, EntregaSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask_jwt_extended import get_jwt, jwt_required, create_access_token
from datetime import datetime
from celery_app.dispatcher import LogisticaTasks, MonitorTasks, task_dispatcher

# Importar celery desde la configuración global
entrega_schema = EntregaSchema()


class VistaEntregas(Resource):

    def post(self):
        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400
        
        if data.get("direccion") is None:
            return {"error": "direccion es requerida"}, 400
        if data.get("estado") is None:
            return {"error": "estado es requerido"}, 400
        if data.get("pedido_id") is None:
            return {"error": "pedido_id es requerido"}, 400
        
        direccion_encrypted = encrypt(data["direccion"])
        nueva_entrega = Entrega(
            direccion=direccion_encrypted,
            estado=data["estado"],
            pedido_id=data["pedido_id"],
        )
        db.session.add(nueva_entrega)
        db.session.commit()
        return entrega_schema.dump(nueva_entrega)

    def get(self):
        return [entrega_schema.dump(ca) for ca in Entrega.query.all()]


class VistaEntrega(Resource):

    def get(self, id_entrega):
        entrega = Entrega.query.get(id_entrega)
        if not entrega:
            return {"mensaje": "Entrega no encontrada"}, 404
        return {
            "id": entrega.id,
            "direccion": decrypt(entrega.direccion) if entrega.direccion and ':' in entrega.direccion else None,
            "pedido_id": entrega.pedido_id,
            "estado": entrega.estado,
            "nombre_recibe": decrypt(entrega.nombre_recibe) if entrega.nombre_recibe and ':' in entrega.nombre_recibe else None,
            "firma_recibe": decrypt(entrega.firma_recibe) if entrega.firma_recibe and ':' in entrega.firma_recibe else None,
            "integridad_firma": entrega.integridad_firma,
            "fecha_entrega": datetime.fromtimestamp(entrega.fecha_entrega.timestamp()).isoformat() if entrega.fecha_entrega else None,
        }


class VistaConfirmarEntrega(Resource):
    """
    Endpoint para confirmar la entrega de un paquete
    """

    @jwt_required()
    def post(self, id_entrega):

        jwt_info = get_jwt()
        usuario_id = jwt_info.get("sub")["id"]
        data = request.get_json()
        direccion = data.get("direccion")
        nombre_recibe = data.get("nombre_recibe")
        firma_recibe = data.get("firma_recibe")  # Asumimos que es una cadena base64
        firma_payload = data.get("firma_payload")  # Payload original que se firmó
        pedido_id = data.get("pedido_id")

        if not data:
            return {"error": "Body JSON requerido"}, 400
        if not direccion:
            return {"error": "direccion es requerida"}, 400
        if not nombre_recibe:
            return {"error": "nombre_recibe es requerido"}, 400
        if not firma_recibe:
            return {"error": "firma_recibe es requerida"}, 400

        return sync_procesar_entrega(
            id_entrega,
            0,
            confirmacion_info={
                "direccion": direccion,
                "nombre_recibe": nombre_recibe,
                "firma_recibe": firma_recibe,
                "firma_payload": firma_payload,
                "pedido_id": pedido_id,
                "usuario_id": usuario_id,
                "entrega_id": id_entrega,
            },
        )


class VistaTareas(Resource):
    """
    Endpoints para enviar y consultar tareas asíncronas usando el nuevo dispatcher
    """

    def get(self):
        tasks = task_dispatcher.list_tasks_from_redis()
        return {
            "message": "Lista de tareas en Redis",
            "tasks": [task for task in tasks],
        }, 200

    @api_protect(
        {
            "jwt_required": False,
            "api_key_required": False,
            "roles_required": ["Admin", "System"],
        }
    )
    def post(self):
        """
        Envía una tarea asíncrona usando el dispatcher desacoplado
        """

        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400

        tipo_tarea = data.get("tipo")

        if tipo_tarea == "procesar_entrega":
            entrega_id = data.get("entrega_id")
            retry_count = data.get(
                "_retry_count", 0
            )  # Parámetro interno para reintentos
            confirmacion_info = data.get("confirmacion_info", None)

            return sync_procesar_entrega(entrega_id, retry_count, confirmacion_info={
                **confirmacion_info,
                "entrega_id": entrega_id,
            })

        elif tipo_tarea == "validar_inventario":
            producto_id = data.get("producto_id")
            cantidad = data.get("cantidad")

            if not producto_id or not cantidad:
                return {"error": "producto_id y cantidad son requeridos"}, 400

            task_result = LogisticaTasks.validar_inventario(producto_id, cantidad)

            return {"message": "Validación enviada via dispatcher", **task_result}, 202

        elif tipo_tarea == "generar_reporte":
            fecha_inicio = data.get("fecha_inicio")
            fecha_fin = data.get("fecha_fin")

            task_result = LogisticaTasks.generar_reporte(fecha_inicio, fecha_fin)

            return {"message": "Reporte enviado via dispatcher", **task_result}, 202

        elif tipo_tarea == "health_check":
            task_result = MonitorTasks.health_check()

            return {
                "message": "Health check iniciado via dispatcher",
                **task_result,
            }, 202

        elif tipo_tarea == "log_activity":
            activity_data = data.get("activity_data", {})

            task_result = MonitorTasks.log_activity(activity_data)

            return {
                "message": "Log activity enviado via dispatcher",
                **task_result,
            }, 202

        elif tipo_tarea == "generate_metrics":
            task_result = MonitorTasks.generate_metrics()

            return {
                "message": "Generación de métricas iniciada via dispatcher",
                **task_result,
            }, 202

        else:
            # Lista de tareas disponibles
            available_tasks = task_dispatcher.list_available_tasks()
            return {
                "error": "Tipo de tarea no válido",
                "available_tasks": available_tasks,
                "ejemplos": [
                    {"tipo": "procesar_entrega", "entrega_id": 123},
                    {"tipo": "validar_inventario", "producto_id": 456, "cantidad": 10},
                    {
                        "tipo": "generar_reporte",
                        "fecha_inicio": "2025-01-01",
                        "fecha_fin": "2025-01-31",
                    },
                    {"tipo": "health_check"},
                    {
                        "tipo": "log_activity",
                        "activity_data": {"evento": "login", "usuario": "test"},
                    },
                    {"tipo": "generate_metrics"},
                ],
            }, 400


class VistaTareaDetail(Resource):
    """
    Endpoint para consultar el estado de una tarea asíncrona por ID
    """

    def get(self, task_id):
        """
        Consulta el estado/resultado de una tarea específica
        """
        # Obtener resultado de tarea específica
        task_result = task_dispatcher.get_task_result(task_id)
        return task_result, 200
