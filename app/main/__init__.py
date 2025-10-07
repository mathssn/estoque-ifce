from .routes import main_bp
from .produtos import produtos_bp
from .notas_fiscais import notas_fiscais_bp
from .fornecedores import fornecedores_bp

blueprints = [main_bp, produtos_bp, notas_fiscais_bp, fornecedores_bp]