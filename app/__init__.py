from flask import Flask
from dotenv import load_dotenv
import os
import smtplib

from app.estoque import blueprints as estoque_blueprints
from app.main import blueprints as main_blueprints
from app.usuarios import usuarios_bp
from app.empenho import blueprints as empenho_blueprints
from app.refeicao_contagem import registro_refeicao_bp
from app.main.routes import register_filters

from app.empenho.models import *
from app.models import *
from app.estoque.models import *
from app.usuarios.models import *
from app.refeicao_contagem.models import *

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('mail_username')
    app.config['MAIL_PASSWORD'] = os.environ.get('mail_password')

    app.register_blueprint(usuarios_bp)
    app.register_blueprint(registro_refeicao_bp)
    for bp in estoque_blueprints + main_blueprints + empenho_blueprints:
        app.register_blueprint(bp)

    register_filters(app)

    return app
    