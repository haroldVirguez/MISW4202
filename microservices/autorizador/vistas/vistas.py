from flask import current_app, request

from scripts.utils import (
    api_protect,
    compare_password,
    hash_password,
    sign_data,
    validate_signature,
)
from ..modelos import db, Usuario, UsuarioSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import get_jwt, jwt_required, create_access_token
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

            token_de_acceso = create_access_token(
                identity={
                    "nombre": usuario.nombre,
                    "id": usuario.id,
                    "roles": usuario.roles,
                }
            )
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
            roles="usuario",  # Asignar rol por defecto
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        token_de_acceso = create_access_token(
            identity={
                "nombre": nuevo_usuario.nombre,
                "id": nuevo_usuario.id,
                "roles": nuevo_usuario.roles,
            }
        )
        return {"mensaje": "Usuario creado exitosamente", "token": token_de_acceso}


class VistaSignatureGen(Resource):
    """
    Endpoint para firmar digitalmente un payload
    """

    @api_protect({"jwt_required": True, "api_key_required": False})
    def post(self):
        jwt_info = get_jwt()
        usuario_id = jwt_info.get("sub")["id"]
        data = request.get_json()
        if not data:
            return {"error": "Body JSON requerido"}, 400
        payload = data.get("payload")
        if not payload:
            return {"error": "payload es requerido"}, 400
        
        payload["usuario_id"] = usuario_id

       

        firma = sign_data(secret_key=current_app.config['PRIVATE_KEY'], data=payload)

        return {
            "payload": payload,
            "firma": firma,
            "usuario_id": usuario_id,
            "timestamp": datetime.now().isoformat(),
        }


class VistaSignatureVal(Resource):
    """
    Endpoint para validar una firma digital
    """

    @api_protect({"jwt_required": False, "api_key_required": False})
    def post(self):
        data = request.get_json()
        payload = data.get("payload")
        firma = data.get("firma")

        if not data:
            return {"error": "Body JSON requerido"}, 400
        if not payload:
            return {"error": "payload es requerido"}, 400
        if not firma:
            return {"error": "firma es requerida"}, 400
        print(data)
        print(payload)
        print(firma)
        es_valida = validate_signature(
            secret_key=current_app.config['PRIVATE_KEY'], data=payload, signature=firma
        )

        return {
            "payload": payload,
            "firma": firma,
            "timestamp": datetime.now().isoformat(),
            "firma_valida": es_valida,
        }, 200
