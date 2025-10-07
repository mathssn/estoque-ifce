from app.database.base import Base, StatusEnum, Tipo
from sqlalchemy import DECIMAL, Column, Integer, String, Enum, ForeignKey, UniqueConstraint, Date


class RegistroRefeicao(Base):
    __tablename__ = 'registro_refeicao'

    id = Column(Integer, primary_key=True, autoincrement=True)
    refeicao_id = Column(Integer, ForeignKey('refeicao.id'), nullable=False)
    qntd_aluno = Column(Integer, nullable=False)
    qntd_servidores = Column(Integer, nullable=False)
    qntd_terceirizados = Column(Integer, nullable=False)
    qntd_outros = Column(Integer, nullable=False)
    data = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint('refeicao_id', 'data', name='uix_refeicao_id_data'),
    )
