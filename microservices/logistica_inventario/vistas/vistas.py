import os
from flask import request

from scripts.utils import api_key_required, api_require_some_auth

from ..services import sync_procesar_entrega
from ..modelos import db, Entrega, EntregaSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import get_jwt, jwt_required, create_access_token
from datetime import datetime
import random
from celery_app.dispatcher import LogisticaTasks, MonitorTasks, task_dispatcher

# Importar celery desde la configuración global
entrega_schema = EntregaSchema()



class VistaEntregas(Resource):

    def post(self):
        nueva_entrega = Entrega(
            direccion=request.json["direccion"], 
            estado=request.json["estado"], 
            pedido_id=request.json["pedido_id"]
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
        return entrega_schema.dump(entrega)

class VistaConfirmarEntrega(Resource):
    """
    Endpoint para confirmar la entrega de un paquete
    """
    @jwt_required()
    def post(self, id_entrega):

        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400
        return sync_procesar_entrega(id_entrega)

class VistaTareas(Resource):
    """
    Endpoints para enviar y consultar tareas asíncronas usando el nuevo dispatcher
    """
    @api_require_some_auth()
    @api_key_required(optional=True, key=os.getenv("API_KEY"))
    @jwt_required(optional=True)
    def post(self):
        """
        Envía una tarea asíncrona usando el dispatcher desacoplado
        """
        # Importar el dispatcher limpio
        jwt_data = get_jwt()
        
        roles = jwt_data.get("roles", "").split(",")
        if 'Admin' not in roles or 'System' not in roles:
            return {"error": "No tiene permisos para realizar esta acción"}, 403
        
        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400
        
        tipo_tarea = data.get("tipo")
        
        if tipo_tarea == "procesar_entrega":
            entrega_id = data.get("entrega_id")
            retry_count = data.get("_retry_count", 0)  # Parámetro interno para reintentos
            
            return sync_procesar_entrega(entrega_id, retry_count)
            
        elif tipo_tarea == "validar_inventario":
            producto_id = data.get("producto_id")
            cantidad = data.get("cantidad")
            
            if not producto_id or not cantidad:
                return {"error": "producto_id y cantidad son requeridos"}, 400
            
            task_result = LogisticaTasks.validar_inventario(producto_id, cantidad)
            
            return {
                "message": "Validación enviada via dispatcher",
                **task_result
            }, 202
            
        elif tipo_tarea == "generar_reporte":
            fecha_inicio = data.get("fecha_inicio")
            fecha_fin = data.get("fecha_fin")
            
            task_result = LogisticaTasks.generar_reporte(fecha_inicio, fecha_fin)
            
            return {
                "message": "Reporte enviado via dispatcher", 
                **task_result
            }, 202
            
        elif tipo_tarea == "health_check":
            task_result = MonitorTasks.health_check()
            
            return {
                "message": "Health check iniciado via dispatcher",
                **task_result
            }, 202
            
        elif tipo_tarea == "log_activity":
            activity_data = data.get("activity_data", {})
            
            task_result = MonitorTasks.log_activity(activity_data)
            
            return {
                "message": "Log activity enviado via dispatcher",
                **task_result
            }, 202
            
        elif tipo_tarea == "generate_metrics":
            task_result = MonitorTasks.generate_metrics()
            
            return {
                "message": "Generación de métricas iniciada via dispatcher",
                **task_result
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
                    {"tipo": "generar_reporte", "fecha_inicio": "2025-01-01", "fecha_fin": "2025-01-31"},
                    {"tipo": "health_check"},
                    {"tipo": "log_activity", "activity_data": {"evento": "login", "usuario": "test"}},
                    {"tipo": "generate_metrics"}
                ]
            }, 400
        
    def get(self):
        tasks= task_dispatcher.list_tasks_from_redis()
        return {"message": "Lista de tareas en Redis", "tasks": [task for task in tasks]}, 200


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
        
        