from werkzeug.security import check_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.models import *
from database.db import db

def recalculate_exits_balance(data, saida: Saida, session_db: Session, update=False, delete=False):
    saldo = session_db.query(SaldoDiario).filter_by(data=data, produto_id=saida.produto_id).first()
    if not saldo:
        raise Exception('Não é possivel atualizar o saldo do dia')

    saidas_ = session_db.query(Saida).filter_by(data_saida=data).all()
    total_saidas = 0

    for s in saidas_:
        if s.produto_id == int(saida.produto_id):
            if s.id == saida.id:
                if update and not delete:
                    total_saidas += int(saida.quantidade)
            else:
                total_saidas += s.quantidade
    
    if not update and not delete:
        total_saidas += int(saida.quantidade)
    
    qntd_final = saldo.quantidade_inicial + saldo.quantidade_entrada - total_saidas
    if qntd_final < 0:
        raise Exception('Valor inválido')

    saldo.quantidade_saida = total_saidas
    saldo.quantidade_final = qntd_final


def recalculate_entries_balance(data, entrada: Entrada, session_db: Session, update=False, delete=False):

    saldo = session_db.query(SaldoDiario).filter_by(data=data, produto_id=entrada.produto_id).first()
    if not saldo:
        raise Exception('Não é possivel atualizar o saldo do dia')

    entradas_ = session_db.query(Entrada).filter_by(data_entrada=data).all()
    total_entradas = 0

    for e in entradas_:
        if e.produto_id == int(entrada.produto_id):
            if e.id == entrada.id:
                if update and not delete:
                    total_entradas += int(entrada.quantidade)
            else:
                total_entradas += e.quantidade
    
    if not update and not delete:
        total_entradas += int(entrada.quantidade)
    
    qntd_final = saldo.quantidade_inicial + total_entradas - saldo.quantidade_saida
    if qntd_final < 0:
        raise Exception('Valor inválido')

    saldo.quantidade_entrada = total_entradas
    saldo.quantidade_final = qntd_final


def check_saldo(data, session_db: Session):
    dia = session_db.query(DiasFechados).filter_by(data=data).first()
    if not dia:
        return False
    if dia.fechado:
        return False
    
    return True


def check_login(email: str, senha: str, session_db: Session):
    usuario = session_db.query(Usuario).filter_by(email=email).first()
    if usuario == None:
        return 1, None
    elif not check_password_hash(usuario.senha, senha):
        return 2, None
    return 0, usuario

def get_last_movement(produto_id, session_db: Session):
    from database.models import Saida, Entrada

    last_exit = session_db.query(Saida).filter_by(produto_id=produto_id).order_by(Saida.data_saida.desc()).first()
    last_entrie = session_db.query(Entrada).filter_by(produto_id=produto_id).order_by(Entrada.data_entrada.desc()).first()

    if last_exit != None and last_entrie != None:
        if last_exit.data_saida > last_entrie.data_entrada:
            return last_exit
        elif last_exit.data_saida <= last_entrie.data_entrada:
            return last_entrie
    elif last_exit != None:
        return last_exit
    elif last_entrie != None:
        return last_entrie
    else:
        return None
    

def list_movementation_by_product(produto_id, limit, offset):
    query = """
        SELECT * 
        FROM (
            SELECT 
                e.id,
                e.produto_id,
                e.data_entrada AS data_movimentacao,
                e.quantidade,
                e.observacao,
                e.usuario_id,
                e.marca_id,
                e.data_validade,
                e.fornecedor_id,
                e.nota_fiscal_id,
                NULL AS destino_id,
                'entrada' AS tipo
            FROM entradas e
            WHERE e.produto_id = :produto_id

            UNION ALL

            SELECT 
                s.id,
                s.produto_id,
                s.data_saida AS data_movimentacao,
                s.quantidade,
                s.observacao,
                s.usuario_id,
                s.marca_id,
                s.data_validade,
                s.fornecedor_id,
                s.nota_fiscal_id,
                s.destino_id,
                'saida' AS tipo
            FROM saidas s
            WHERE s.produto_id = :produto_id
        ) AS movimentacoes
        ORDER BY data_movimentacao DESC, destino_id DESC
        LIMIT :limit OFFSET :offset
    """

    with db.connect() as conn:
        result = conn.execute(
            text(query),
            ({'produto_id': produto_id, 'limit': limit, 'offset': offset})
        )
        rows = result.fetchall()

    movimentacoes = []
    for row in rows:
        movimentacoes.append({
            'id': row[0],
            'data': row[2],
            'quantidade': row[3],
            'destino_id': row[10],
            'responsavel': row[5],
            'observacao': row[4],
            'tipo': row[11]
        })

    
    query = """
        SELECT COUNT(*) AS total_movimentacoes
        FROM (
            SELECT 1 FROM entradas WHERE produto_id = :produto_id
            UNION ALL
            SELECT 1 FROM saidas   WHERE produto_id = :produto_id
        ) t
    """

    with db.connect() as conn:
        result = conn.execute(
            text(query),
            {'produto_id': produto_id}
        )
        total = result.scalar()
    return movimentacoes, total