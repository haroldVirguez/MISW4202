from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

db = SQLAlchemy()

class Entrega(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    direccion = db.Column(db.String(128))
    pedido_id = db.Column(db.Integer)
    estado = db.Column(db.String(64))
    tiempo_entrega = db.Column(db.DateTime, default=None, nullable=True)
    
class EntregaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Entrega
        include_relationships = True
        load_instance = True
