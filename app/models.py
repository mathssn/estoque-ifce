from app.database.base import Base, StatusEnum, Tipo
from sqlalchemy import DECIMAL, Column, Integer, String, Date, Enum, ForeignKey, UniqueConstraint, Boolean
import enum

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


class StatusNotaFiscalEnum(str, enum.Enum):
    pendente = "pendente"
    em_ateste = "em_ateste"
    atestada = "atestada"
    liquidada = "liquidada"
    cancelada = "cancelada"

class NotaFiscal(Base):
    __tablename__ = "nota_fiscal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(100), nullable=False)
    data_emissao = Column(Date, nullable=False)
    serie = Column(Integer, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    empenho_id = Column(Integer, ForeignKey("empenho.id"), nullable=False)
    status = Column(Enum(StatusNotaFiscalEnum), nullable=False, default=StatusEnum.ativo)
    observacao = Column(String(500))

    __table_args__ = (
        UniqueConstraint('numero', 'fornecedor_id', 'serie', name='uix_numero_fornecedor_id_serie'),
    )


class ItemNF(Base):
    __tablename__ = "item_nf"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    item_empenho_id = Column(Integer, ForeignKey("item_empenho.id", ondelete="CASCADE"), nullable=False)

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), unique=True, nullable=False)


class RoleUser(Base):
    __tablename__ = "role_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    ativado = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint('usuario_id', 'role_id', name='uix_usuario_id_role_id'),
    )
