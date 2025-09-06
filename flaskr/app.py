from flaskr import create_app, make_celery
from flask_restful import Api
from .modelos import db
from .vistas import VistaEntregas, VistaEntrega, VistaSignIn, VistaLogIn
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = create_app('default')
app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaEntregas, '/entregas')
api.add_resource(VistaEntrega, '/entrega/<int:id_entrega>')
api.add_resource(VistaSignIn, '/signin', '/signin/<int:id_usuario>')
api.add_resource(VistaLogIn, '/login')

jwt = JWTManager(app)

celery = make_celery(app)