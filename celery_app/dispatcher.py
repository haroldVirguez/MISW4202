"""
Task Dispatcher - Desacoplamiento para el envío de tareas asíncronas

Este módulo proporciona una interfaz uniforme para enviar tareas sin 
tener dependencias directas del código de las tareas.
Usa la instancia de Celery específica para Flask.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from celery.result import AsyncResult
from .client import flask_celery
from .task_registry import list_available_tasks,  get_task_info, validate_task_params

class TaskDispatcher:
    """
    Dispatcher para enviar tareas asíncronas sin acoplamiento directo
    Usa la instancia de Celery específica para Flask
    """
    
    def __init__(self):
        self.celery = flask_celery
        print("✓ TaskDispatcher configurado con flask_celery")
    
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
                'error': 'Celery no disponible',
                'task_name': task_name,
                'status': 'FAILED'
            }
      
        
        task_info = get_task_info(task_name)
        if not task_info:
            return {
                'error': f"Tarea '{task_name}' no encontrada en el registro",
                'task_name': task_name,
                'status': 'FAILED'
            }
        
        # Validar parámetros
        is_valid, validation_msg = validate_task_params(task_name, args)
        if not is_valid:
            return {
                'error': f"Parámetros inválidos: {validation_msg}",
                'task_name': task_name,
                'status': 'FAILED'
            }
        
        try:
            # Enviar tarea usando Celery (por nombre)
            result = self.celery.send_task(
                task_name, 
                args=args, 
                kwargs=kwargs,
                queue=task_info.get('queue', 'celery')
            )
            
            return {
                'task_id': result.id,
                'task_name': task_name,
                'status': 'PENDING',
                'queue': task_info.get('queue', 'celery'),
                'timestamp': datetime.now().isoformat(),
                'args': args,
                'kwargs': kwargs
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'task_name': task_name,
                'status': 'FAILED'
            }
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el resultado completo de una tarea"""
        if not self.celery:
            return {'error': 'Celery no disponible', 'task_id': task_id}
        
        try:
            result = AsyncResult(task_id, app=self.celery)
            
            response = {
                'task_id': task_id,
                'status': result.status,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.ready():
                if result.successful():
                    response['result'] = result.result
                else:
                    response['error'] = str(result.result)
            else:
                # Para tareas en progreso
                if isinstance(result.info, dict):
                    response.update(result.info)
                    
            return response
            
        except Exception as e:
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def get_task_status(self, task_id: str) -> str:
        """Obtiene solo el estado de una tarea"""
        if not self.celery:
            return 'ERROR'
        
        try:
            result = AsyncResult(task_id, app=self.celery)
            return result.status
        except Exception:
            return 'ERROR'
    
    def list_available_tasks(self) -> list:
        """Lista tareas disponibles"""
        return list_available_tasks()
    
    def listar_task_from_redis(self) -> list:
        """Lista tareas activas/pendientes/en proceso en Redis"""
        if not self.celery:
            return []
        
        i = self.celery.control.inspect()
        all_active_tasks = []
        
        # Obtener tareas activas (en ejecución)
        active = i.active()
        if active:
            for worker, tasks in active.items():
                all_active_tasks.extend(tasks)
        
        # Obtener tareas pendientes (en cola)
        scheduled = i.scheduled()
        if scheduled:
            for worker, tasks in scheduled.items():
                all_active_tasks.extend(tasks)
        
        # Obtener tareas reservadas
        reserved = i.reserved()
        if reserved:
            for worker, tasks in reserved.items():
                all_active_tasks.extend(tasks)
        
        return all_active_tasks

# Instancia global del dispatcher
task_dispatcher = TaskDispatcher()

# Funciones de conveniencia para tareas específicas
class LogisticaTasks:
    """Wrapper para tareas de logística sin importar código directo"""
    
    @staticmethod
    def procesar_entrega(entrega_id: int, **options):
        return task_dispatcher.dispatch_task(
            'logistica.procesar_entrega',
            entrega_id,
            **options
        )
    
    @staticmethod  
    def validar_inventario(producto_id: int, cantidad: int, **options):
        return task_dispatcher.dispatch_task(
            'logistica.validar_inventario', 
            producto_id, 
            cantidad,
            **options
        )
    
    @staticmethod
    def generar_reporte(fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None, **options):
        return task_dispatcher.dispatch_task(
            'logistica.generar_reporte',
            fecha_inicio,
            fecha_fin,
            **options
        )

class MonitorTasks:
    """Wrapper para tareas de monitoreo"""
    
    @staticmethod
    def health_check(**options):
        return task_dispatcher.dispatch_task(
            'monitor.health_check',
            **options
        )
    
    @staticmethod
    def log_activity(activity_data: dict, **options):
        return task_dispatcher.dispatch_task(
            'monitor.log_activity',
            activity_data,
            **options
        )
    
    @staticmethod
    def generate_metrics(**options):
        return task_dispatcher.dispatch_task(
            'monitor.generate_metrics',
            **options
        )
