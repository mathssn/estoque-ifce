from flask import Blueprint

registro_refeicao_bp = Blueprint('registro_refeicao', __name__, template_folder='templates')

from . import routes
