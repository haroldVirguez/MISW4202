from flask import request
from ..modelos import db, Entrega, EntregaSchema, Usuario, UsuarioSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token
from datetime import datetime
import random
from celery_app.dispatcher import LogisticaTasks, MonitorTasks, task_dispatcher

# Importar celery desde la configuración global
entrega_schema = EntregaSchema()
usuario_schema = UsuarioSchema()



class VistaEntregas(Resource):

    def post(self):
        nueva_entrega = Entrega(
            titulo=request.json["titulo"], 
            minutos=request.json["minutos"], 
            segundos=request.json["segundos"], 
            interprete=request.json["interprete"]
        )
        db.session.add(nueva_entrega)
        db.session.commit()
        return entrega_schema.dump(nueva_entrega)

    def get(self):
        return [entrega_schema.dump(ca) for ca in Entrega.query.all()]

class VistaEntrega(Resource):

    def get(self, id_entrega):
        return entrega_schema.dump(Entrega.query.get_or_404(id_entrega))

    def put(self, id_entrega):
        entrega = Entrega.query.get_or_404(id_entrega)
        entrega.titulo = request.json.get("titulo",entrega.titulo)
        entrega.minutos = request.json.get("minutos",entrega.minutos)
        entrega.segundos = request.json.get("segundos",entrega.segundos)
        entrega.interprete = request.json.get("interprete",entrega.interprete)
        db.session.commit()
        return entrega_schema.dump(entrega)

    def delete(self, id_entrega):
        entrega = Entrega.query.get_or_404(id_entrega)
        db.session.delete(entrega)
        db.session.commit()
        return 'Operación exitosa',204

class VistaLogIn(Resource):

    def post(self):
            u_nombre = request.json["nombre"]
            u_contrasena = request.json["contrasena"]
            usuario = Usuario.query.filter_by(nombre=u_nombre, contrasena = u_contrasena).all()
            if usuario:
                
                token_de_acceso = create_access_token(identity=u_nombre)
                return {'mensaje':'Inicio de sesión exitoso', 'token': token_de_acceso}, 200
            else:
                return {'mensaje':'Nombre de usuario o contraseña incorrectos'}, 401


class VistaSignIn(Resource):
    
    def post(self):
        nuevo_usuario = Usuario(nombre=request.json["nombre"], contrasena=request.json["contrasena"])
        token_de_acceso = create_access_token(identity=request.json["nombre"])
        db.session.add(nuevo_usuario)
        db.session.commit()
        return {'mensaje': 'Usuario creado exitosamente', 'token': token_de_acceso}

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena",usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return '',204


class VistaTareas(Resource):
    """
    Endpoints para enviar y consultar tareas asíncronas usando el nuevo dispatcher
    """
    
    def post(self):
        """
        Envía una tarea asíncrona usando el dispatcher desacoplado
        """
        # Importar el dispatcher limpio
        
        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400
        
        tipo_tarea = data.get("tipo")
        
        if tipo_tarea == "procesar_entrega":
            entrega_id = data.get("entrega_id")
            if not entrega_id:
                return {"error": "entrega_id es requerido"}, 400
            
            try:
                if random.random() < 0.5:
                    raise Exception("Sistema temporalmente no disponible")
                
                task_result = LogisticaTasks.procesar_entrega(entrega_id)
                
                return {
                    "message": "Tarea enviada",
                    "entrega_id": entrega_id,
                    "estado": "exitoso",
                    "timestamp": datetime.utcnow().isoformat(),
                    **task_result
                }, 200
                
            except Exception as e:
                task_result = LogisticaTasks.procesar_entrega(entrega_id)
                raise e
            
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
        tasks= task_dispatcher.listar_task_from_redis()
        return {"message": "Lista de tareas en Redis", "tasks": [task for task in tasks]}, 200


class VistaTareaDetail(Resource):
    """
    Endpoint para consultar el estado de una tarea asíncrona por ID
    """
    def get(self, task_id=None):
        """
        Consulta el estado/resultado de una tarea específica
        """
        
        if task_id:
            # Obtener resultado de tarea específica
            task_result = task_dispatcher.get_task_result(task_id)
            return task_result, 200
        else:
            # Listar tareas disponibles
            available_tasks = task_dispatcher.list_available_tasks()
            return {
                "available_tasks": available_tasks,
                "endpoints": {
                    "dispatch": "POST /tareas",
                    "status": "GET /tareas/<task_id>"
                },
                "info": "Use POST para enviar tareas, GET con task_id para consultar estado"
            }, 200
        