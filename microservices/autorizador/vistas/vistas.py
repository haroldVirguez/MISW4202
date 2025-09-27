from flask import request

from scripts.crypto import compare_password, hash_password
from ..modelos import db, Usuario, UsuarioSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token
from datetime import datetime
import random

usuario_schema = UsuarioSchema()


class VistaLogIn(Resource):

    def post(self):
        u_nombre = request.json["nombre"]
        u_contrasena = request.json["contrasena"]
        usuario = Usuario.query.filter_by(nombre=u_nombre).first()
        
        if not usuario:
            return {"mensaje": "Nombre de usuario o contraseña incorrectos"}, 401
        
        if compare_password(usuario.contrasena, u_contrasena):

            token_de_acceso = create_access_token(identity=u_nombre)
            return {
                "mensaje": "Inicio de sesión exitoso",
                "token": token_de_acceso,
            }, 200
        else:
            return {"mensaje": "Nombre de usuario o contraseña incorrectos"}, 401


class VistaSignUp(Resource):

    def post(self):
        if Usuario.query.filter_by(nombre=request.json["nombre"]).first():
            return {"mensaje": "El nombre de usuario ya existe"}, 400

        nuevo_usuario = Usuario(
            nombre=request.json["nombre"],
            contrasena=hash_password(request.json["contrasena"]),
        )
        token_de_acceso = create_access_token(
            identity={"nombre": nuevo_usuario.nombre, "id": nuevo_usuario.id}
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return {"mensaje": "Usuario creado exitosamente", "token": token_de_acceso}
