from app.database.base import Base, StatusEnum, Tipo
from sqlalchemy import DECIMAL, Column, Integer, String, Date, Enum, ForeignKey, UniqueConstraint


class Refeicao(Base):
    __tablename__ = "refeicao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)


class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(Integer, nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(100))
    unidade = Column(String(10), nullable=False)
    quantidade_minima = Column(Integer, nullable=False)
    tipo = Column(Enum(Tipo), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)

    __table_args__ = (
        UniqueConstraint('codigo', 'tipo', name='uix_codigo_tipo'),
    )


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)


class NotaFiscal(Base):
    __tablename__ = "nota_fiscal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(100), nullable=False)
    data_emissao = Column(Date, nullable=False)
    serie = Column(Integer, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    empenho_id = Column(Integer, ForeignKey("empenho.id"), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)

    __table_args__ = (
        UniqueConstraint('numero', 'fornecedor_id', 'serie', name='uix_numero_fornecedor_id_serie'),
    )


class ItemNF(Base):
    __tablename__ = "item_nf"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)