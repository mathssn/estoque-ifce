from .entradas import entradas_bp
from .saidas import saidas_bp
from .marcas import marcas_bp
from .routes import estoque_bp
from .relatorios import relatorios_bp

blueprints = [entradas_bp, saidas_bp, marcas_bp, estoque_bp, relatorios_bp]