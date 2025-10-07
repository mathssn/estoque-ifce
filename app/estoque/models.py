from app.database.base import Base
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, Text, TIMESTAMP, Boolean, text
import enum


class TipoOperacaoEnum(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"


class TipoOperacao2Enum(str, enum.Enum):
    insercao = "inserção"
    edicao = "edição"
    exclusao = "exclusão"


class Marca(Base):
    __tablename__ = "marca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100))
    produto_id = Column(Integer, ForeignKey("produto.id"))


class Saida(Base):
    __tablename__ = "saidas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    refeicao_id = Column(Integer, ForeignKey("refeicao.id"), nullable=False)
    data_saida = Column(Date, nullable=False)
    quantidade = Column(Integer, nullable=False)
    observacao = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    marca_id = Column(Integer, ForeignKey("marca.id"), nullable=False)
    data_validade = Column(Date, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=False)


class Entrada(Base):
    __tablename__ = "entradas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    data_entrada = Column(Date, nullable=False)
    quantidade = Column(Integer, nullable=False)
    observacao = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    marca_id = Column(Integer, ForeignKey("marca.id"), nullable=False)
    data_validade = Column(Date, nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    nota_fiscal_id = Column(Integer, ForeignKey("nota_fiscal.id"), nullable=False)


class SaldoDiario(Base):
    __tablename__ = "saldo_diario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    data = Column(Date, nullable=False)
    quantidade_inicial = Column(Integer, nullable=False)
    quantidade_entrada = Column(Integer, nullable=False)
    quantidade_saida = Column(Integer, nullable=False)
    quantidade_final = Column(Integer, nullable=False)


class DiasFechados(Base):
    __tablename__ = "dias_fechados"

    data = Column(Date, primary_key=True)
    fechado = Column(Boolean, nullable=False)


class Log(Base):
    __tablename__ = "logs"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    operacao_id = Column(Integer, nullable=False)
    tipo_operacao = Column(Enum(TipoOperacaoEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    tipo_operacao_2 = Column(Enum(TipoOperacao2Enum, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    data_hora = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    