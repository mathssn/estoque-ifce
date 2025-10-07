from app.database.base import Base, StatusEnum, Tipo
from sqlalchemy import DECIMAL, Column, Integer, String, Enum, ForeignKey, UniqueConstraint


class Ata(Base):
    __tablename__ = "ata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, nullable=False)
    ano = Column(String(4), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    tipo = Column(Enum(Tipo), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)

    __table_args__ = (
        UniqueConstraint('numero', 'ano', name='uix_numero_ano'),
    )


class ItemAta(Base):
    __tablename__ = "item_ata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ata_id = Column(Integer, ForeignKey("ata.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    quantidade_maxima = Column(Integer, nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('ata_id', 'produto_id', name='uix_ata_produto'),
    )


class Empenho(Base):
    __tablename__ = "empenho"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, nullable=False)
    ata_id = Column(Integer, ForeignKey("ata.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    ano = Column(String(4), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)

    __table_args__ = (
        UniqueConstraint('numero', 'ano', name='uix_numero_ano'),
    )


class ItemEmpenho(Base):
    __tablename__ = "item_empenho"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empenho_id = Column(Integer, ForeignKey("empenho.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    quantidade_empenhada = Column(Integer, nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('empenho_id', 'produto_id', name='uix_empenho_produto'),
    )