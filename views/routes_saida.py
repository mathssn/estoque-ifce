from flask import Blueprint, redirect, flash, url_for, request, session
from datetime import datetime

from database.utils import check_saldo, recalculate_exits_balance, get_last_movement
from utils.utils import login_required
from database.models import *
from database.db import get_session

saidas_bp = Blueprint('saidas', __name__)

@saidas_bp.route('/cadastro/saida/', methods=['POST'])
@login_required
def cadastro_saida():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias'))
    
    produto_id = request.form.get('produto_id')
    destino_id = request.form.get('destino_id')
    data = request.form.get('data_saida')
    quantidade = request.form.get('quantidade')
    observacao = request.form.get('observacao')
    marca_id = request.form.get('marca_id')
    data_validade = request.form.get('data_validade')
    fornecedor_id = request.form.get('fornecedor_id')
    nota_fiscal_id = request.form.get('nota_fiscal_id')

    nova_saida = Saida(produto_id=produto_id, destino_id=destino_id, data_saida=data, quantidade=quantidade, observacao=observacao, usuario_id=session['user_id'], marca_id=marca_id, data_validade=data_validade, fornecedor_id=fornecedor_id, nota_fiscal_id=nota_fiscal_id)

    if not validar_dados(nova_saida):
        flash('Insira dados válidos para o cadastro da saída.')
        return redirect(url_for('movimentacoes_diarias', data=data))
    
    try:
        with get_session() as session_db:
            last_movement = get_last_movement(produto_id, session_db)
            if last_movement != None:
                veriry_fields(last_movement, nova_saida)

            if not check_saldo(data, session_db):
                flash('Não é possível adicionar saída para esse dia')
                return redirect(url_for('movimentacoes_diarias', data=data))

            recalculate_exits_balance(data, nova_saida, session_db)
            session_db.add(nova_saida)
            session_db.flush()

            log = Log(produto_id=produto_id, usuario_id=session.get('user_id'), operacao_id=nova_saida.id, tipo_operacao='saida', tipo_operacao_2='inserção')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao cadastrar saída: {e}')
    else:
        flash('Saída cadastrada com sucesso!')

    return redirect(url_for('movimentacoes_diarias', data=data))


@saidas_bp.route('/editar/saida/<int:saida_id>/', methods=['POST'])
@login_required
def editar_saida(saida_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias'))
    
    try:
        with get_session() as session_db:
            exit = session_db.query(Saida).filter_by(id=saida_id).first()
            
            exit.destino_id = request.form.get('edit_destino_id_saida')
            exit.quantidade = request.form.get('edit_quantidade_saida')
            exit.observacao = request.form.get('edit_observacao_saida')
            exit.marca_id = request.form.get('edit_marca_id_saida')
            exit.data_validade = request.form.get('edit_data_validade_saida')
            exit.fornecedor_id = request.form.get('edit_fornecedor_id_saida')
            exit.nota_fiscal_id = request.form.get('edit_nota_fiscal_id_saida')
            
            if not validar_dados(exit, True):
                flash('Insira dados válidos para a edição da saída.')
                return redirect(url_for('movimentacoes_diarias', data=exit.data_saida))

            if not check_saldo(exit.data_saida, session_db):
                flash('Não é possível editar saída para esse dia')
                return redirect(url_for('movimentacoes_diarias', data=exit.data_saida))

            recalculate_exits_balance(exit.data_saida, exit, session_db)

            log = Log(produto_id=exit.produto_id, usuario_id=session.get('user_id'), operacao_id=saida_id, tipo_operacao='saida', tipo_operacao_2='edição')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao atualizar saída: {e}')
    else:
        flash('Saída atualizada com sucesso!')
    
    return redirect(url_for('movimentacoes_diarias', data=exit.data_saida))


@saidas_bp.route('/excluir/saida/<int:saida_id>/', methods=['POST'])
@login_required
def excluir_saida(saida_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias'))
    
    try:
        with get_session() as session_db:
            exit = session_db.query(Saida).filter_by(id=saida_id).first()

            if not check_saldo(exit.data_saida, session_db):
                flash('Não é possível excluir saída para esse dia. Saldo bloqueado.')
                return redirect(url_for('movimentacoes_diarias', data=exit.data_saida))

            session_db.delete(exit)
            
            recalculate_exits_balance(exit.data_saida, exit, session_db, delete=True)

            log = Log(produto_id=exit.produto_id, usuario_id=session.get('user_id'), operacao_id=saida_id, tipo_operacao='saida', tipo_operacao_2='exclusão')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao deletar saída: {e}')
    else:
        flash('Saída deletada com sucesso!')

    return redirect(url_for('movimentacoes_diarias', data=exit.data_saida))


def validar_dados(exit: Saida, update=False):
    if not update:
        try:
            datetime.strptime(exit.data_saida, '%Y-%m-%d')
        except ValueError:
            return False

    try:
        quantidade = int(exit.quantidade)
    except (ValueError, TypeError):
        return False
    
    if quantidade <= 0:
        return False
    
    return True

def veriry_fields(last_movement: Saida, nova_saida: Saida):
    if last_movement.data_validade == None and nova_saida.data_validade == "":
        raise Exception('Insira uma data de validade!')
    elif last_movement.data_validade != None and nova_saida.data_validade == "":
        nova_saida.data_validade = last_movement.data_validade

    if last_movement.marca_id == None and nova_saida.marca_id == "0":
        nova_saida.marca_id = 1
    elif last_movement.marca_id != None and nova_saida.marca_id == "0":
        nova_saida.marca_id = last_movement.marca_id

    if last_movement.fornecedor_id == None and nova_saida.fornecedor_id == "0":
        nova_saida.fornecedor_id = 1
    elif last_movement.fornecedor_id != None and nova_saida.fornecedor_id == "0":
        nova_saida.fornecedor_id = last_movement.fornecedor_id

    if last_movement.nota_fiscal_id == None and nova_saida.nota_fiscal_id == "0":
        nova_saida.nota_fiscal_id = 1
    elif last_movement.nota_fiscal_id != None and nova_saida.nota_fiscal_id == "0":
        nova_saida.nota_fiscal_id = last_movement.nota_fiscal_id