"""
Ejemplo de cómo usar tareas de Celery en las vistas

Este archivo muestra cómo integrar tareas asíncronas en tu microservicio
"""

from flask import jsonify, request
from flask_restful import Resource

# Importar las tareas de Celery
from .tasks import procesar_entrega, validar_inventario, generar_reporte_entregas

class VistaEntregaAsincrona(Resource):
    """Ejemplo de vista que usa tareas asíncronas"""
    
    def post(self):
        """Procesar entrega de forma asíncrona"""
        data = request.get_json()
        entrega_id = data.get('entrega_id')
        
        if not entrega_id:
            return {'error': 'entrega_id requerido'}, 400
        
        # Ejecutar tarea asíncrona
        task = procesar_entrega.delay(entrega_id)
        
        return {
            'mensaje': 'Entrega enviada para procesamiento',
            'task_id': task.id,
            'entrega_id': entrega_id
        }, 202

class VistaValidarInventario(Resource):
    """Ejemplo de validación asíncrona de inventario"""
    
    def post(self):
        """Validar inventario de forma asíncrona"""
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad')
        
        if not all([producto_id, cantidad]):
            return {'error': 'producto_id y cantidad requeridos'}, 400
        
        # Ejecutar validación asíncrona
        task = validar_inventario.delay(producto_id, cantidad)
        
        return {
            'mensaje': 'Validación iniciada',
            'task_id': task.id,
            'producto_id': producto_id,
            'cantidad': cantidad
        }, 202

class VistaReporte(Resource):
    """Ejemplo de generación asíncrona de reportes"""
    
    def post(self):
        """Generar reporte de entregas"""
        # Ejecutar generación de reporte
        task = generar_reporte_entregas.delay()
        
        return {
            'mensaje': 'Generación de reporte iniciada',
            'task_id': task.id
        }, 202

class VistaEstadoTarea(Resource):
    """Consultar el estado de una tarea asíncrona"""
    
    def get(self, task_id):
        """Obtener el estado de una tarea"""
        from celery_config import celery
        
        task = celery.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Tarea pendiente...'
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'result': task.result
            }
        else:
            response = {
                'state': task.state,
                'status': str(task.info)
            }
        
        return response

# Para agregar estas vistas a tu app.py:
# api.add_resource(VistaEntregaAsincrona, '/entrega-async')
# api.add_resource(VistaValidarInventario, '/validar-inventario')
# api.add_resource(VistaReporte, '/generar-reporte')
# api.add_resource(VistaEstadoTarea, '/task-status/<task_id>')
