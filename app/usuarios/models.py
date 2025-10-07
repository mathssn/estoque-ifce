from sqlalchemy import Column, Integer, String, Date, Enum
from app.database.base import Base, StatusEnum
import enum

class NivelAcessoEnum(str, enum.Enum):
    superusuario = "Superusuario"
    admin = "Admin"
    editor = "Editor"
    leitor = "Leitor"



class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    senha = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    nivel_acesso = Column(Enum(NivelAcessoEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ativo)



