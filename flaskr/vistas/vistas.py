from flask import request
from ..modelos import db, Entrega, EntregaSchema, Usuario, UsuarioSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token
from datetime import datetime
from ..app import celery

entrega_schema = EntregaSchema()
usuario_schema = UsuarioSchema()

@celery.task(name='registrar_log')
def registrar_log(usuario, fecha):
    with open('logs_signin.txt', 'a+') as file:
        file.write('{} - inicio de sesión: {}\n'.format(usuario, fecha))


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
                registrar_log.apply_async(args=(u_nombre, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), queue='logs')
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
