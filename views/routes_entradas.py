from flask import Blueprint, redirect, flash, url_for, request, session
from datetime import datetime

from database.utils import check_saldo, recalculate_entries_balance, get_last_movement
from utils.utils import login_required

from database.db import get_session
from database.models import *

entradas_bp = Blueprint('entradas', __name__)

@entradas_bp.route('/cadastro/entrada/', methods=['POST'])
@login_required
def cadastro_entrada():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias', tipo='entrada'))
    
    produto_id = request.form.get('produto_id')
    data = request.form.get('data_entrada')
    quantidade = request.form.get('quantidade')
    observacao = request.form.get('observacao')
    marca_id = request.form.get('marca_id')
    data_validade = request.form.get('data_validade')
    fornecedor_id = request.form.get('fornecedor_id')
    nota_fiscal_id = request.form.get('nota_fiscal_id')

    nova_entrada = Entrada(produto_id=produto_id, data_entrada=data, quantidade=quantidade, observacao=observacao, usuario_id=session['user_id'], marca_id=marca_id, data_validade=data_validade, fornecedor_id=fornecedor_id, nota_fiscal_id=nota_fiscal_id)
    if not validar_dados(nova_entrada):
        flash('Insira dados validos')
        return redirect(url_for('movimentacoes_diarias', data=data, tipo='entrada'))
    
    try:
        with get_session() as session_db:
            last_movement = get_last_movement(produto_id, session_db)
            veriry_fields(last_movement, nova_entrada)

            if not check_saldo(data, session_db):
                flash('Não é possivel adicionar entrada para esse dia')
                return redirect(url_for('movimentacoes_diarias', data=data, tipo='entrada'))

            recalculate_entries_balance(data, nova_entrada, session_db)
            session_db.add(nova_entrada)
            session_db.flush()

            log = Log(produto_id=produto_id, usuario_id=session.get('user_id'), operacao_id=nova_entrada.id, tipo_operacao='entrada', tipo_operacao_2='inserção')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao cadastrar entrada: {e}')
    else:
        flash('Entrada cadastrada com sucesso!')

    return redirect(url_for('movimentacoes_diarias', data=data, tipo='entrada'))


@entradas_bp.route('/editar/entrada/<int:entrada_id>/', methods=['POST'])
@login_required
def editar_entrada(entrada_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias', tipo='entrada'))
    
    try:
        with get_session() as session_db:
            entrie = session_db.query(Entrada).filter_by(id=entrada_id).first()
            entrie.quantidade = request.form.get('edit_quantidade_entrada')
            entrie.observacao = request.form.get('edit_observacao_entrada')
            entrie.marca_id = request.form.get('edit_marca_id_entrada')
            entrie.data_validade = request.form.get('edit_data_validade_entrada')
            entrie.fornecedor_id = request.form.get('edit_fornecedor_id_entrada')
            entrie.nota_fiscal_id = request.form.get('edit_nota_fiscal_id_entrada')
            
            if not validar_dados(entrie, True):
                flash('Insira dados válidos')
                return redirect(url_for('movimentacoes_diarias', data=entrie.data_entrada, tipo='entrada'))

            # Verifica se é possivel alterar o saldo do dia
            if not check_saldo(entrie.data_entrada, session_db):
                flash('Não é possivel editar entrada para esse dia')
                return redirect(url_for('movimentacoes_diarias', data=entrie.data_entrada, tipo='entrada'))

            recalculate_entries_balance(entrie.data_entrada, entrie, session_db, update=True)

            log = Log(produto_id=entrie.produto_id, usuario_id=session.get('user_id'), operacao_id=entrada_id, tipo_operacao='entrada', tipo_operacao_2='edição')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao atualizar entrada: {e}')
    else:
        flash('Entrada atualizada com sucesso')
    
    return redirect(url_for('movimentacoes_diarias', data=entrie.data_entrada, tipo='entrada'))


@entradas_bp.route('/excluir/entrada/<int:entrada_id>/', methods=['POST'])
@login_required
def excluir_entrada(entrada_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias', tipo='entrada'))
    
    try:
        with get_session() as session_db:
            entrie = session_db.query(Entrada).filter_by(id=entrada_id).first()

            # Verifica se é possivel alterar o saldo do dia
            if not check_saldo(entrie.data_entrada, session_db):
                flash('Não é possivel excluir saida para esse dia')
                return redirect(url_for('movimentacoes_diarias', data=entrie.data_entrada, tipo='entrada'))

            session_db.delete(entrie)
            recalculate_entries_balance(entrie.data_entrada, entrie, session_db, delete=True)

            log = Log(produto_id=entrie.produto_id, usuario_id=session.get('user_id'), operacao_id=entrada_id, tipo_operacao='entrada', tipo_operacao_2='exclusão')
            session_db.add(log)
    except Exception as e:
        flash(f'Falha ao deletar entrada: {e}')
    else:
        flash('Entrada deletada com sucesso')

    return redirect(url_for('movimentacoes_diarias', data=entrie.data_entrada, tipo='entrada'))


def validar_dados(entrie: Entrada, update=False):
    if not update:
        try:
            datetime.strptime(entrie.data_entrada, '%Y-%m-%d')
        except ValueError:
            return False

    try:
        quantidade = int(entrie.quantidade)
    except (ValueError, TypeError):
        return False
    
    if quantidade <= 0:
        return False
    
    return True

def veriry_fields(last_movement: Entrada, nova_entrada: Entrada):
    if nova_entrada.data_validade == '':
        if last_movement is None or last_movement.data_validade is None:
            raise Exception('Insira uma data de validade')
        else:
            nova_entrada.data_validade = last_movement.data_validade

    if nova_entrada.marca_id == '0' or nova_entrada.marca_id is None:
        if last_movement is None or last_movement.marca_id is None:
            nova_entrada.marca_id = 1
        else:
            nova_entrada.marca_id = last_movement.marca_id

    if nova_entrada.fornecedor_id == '0' or nova_entrada.fornecedor_id is None:
        if last_movement is None or last_movement.fornecedor_id is None:
            nova_entrada.fornecedor_id = 1
        else:
            nova_entrada.fornecedor_id = last_movement.fornecedor_id

    if nova_entrada.nota_fiscal_id == '0' or nova_entrada.nota_fiscal_id is None:
        if last_movement is None or last_movement.nota_fiscal_id is None:
            nova_entrada.nota_fiscal_id = 1
        else:
            nova_entrada.nota_fiscal_id = last_movement.nota_fiscal_id
