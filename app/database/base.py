from sqlalchemy.orm import declarative_base
import enum


Base = declarative_base()


class StatusEnum(str, enum.Enum):
    ativo = "ativo"
    inativo = "inativo"


class Tipo(enum.Enum):
    perecivel = "perecivel"
    nao_perecivel = "nao_perecivel"
