from flask import Blueprint, redirect, flash, url_for, request, session
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database.utils import check_saldo, recalculate_entries_balance, get_last_movement
from app.utils import login_required, get_form

from app.database.db import get_session
from app.estoque.models import *

entradas_bp = Blueprint('entradas', __name__, template_folder='templates')


@entradas_bp.route('/cadastro/entrada/', methods=['POST'])
@login_required
def cadastro_entrada():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        session['tipo_movimentacao'] = 'entrada'
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    try:
        produto_id = int(request.form.get('produto_id'))
        data = request.form.get('data_entrada', '').strip()
        quantidade = int(request.form.get('quantidade', 0))
        observacao = request.form.get('observacao', '').strip()
        marca_id = int(request.form.get('marca_id'))
        data_validade = request.form.get('data_validade').strip()
        fornecedor_id = int(request.form.get('fornecedor_id'))
        nota_fiscal_id = int(request.form.get('nota_fiscal_id'))
    except (ValueError, TypeError):
        flash('Insira dados válidos', 'danger')
        session['tipo_movimentacao'] = 'entrada'
        return redirect(url_for('estoque.movimentacoes_diarias'))

    nova_entrada = Entrada(produto_id=produto_id, data_entrada=data, quantidade=quantidade, observacao=observacao, usuario_id=session['user_id'], marca_id=marca_id, data_validade=data_validade, fornecedor_id=fornecedor_id, nota_fiscal_id=nota_fiscal_id)
    if not validar_dados(nova_entrada):
        flash('Insira dados validos', 'danger')
        session['date'] = data
        session['tipo_movimentacao'] = 'entrada'
        return redirect(url_for('estoque.movimentacoes_diarias'))

    try:
        with get_session() as session_db:
            last_movement = get_last_movement(produto_id, session_db)
            veriry_fields(last_movement, nova_entrada)

            if not check_saldo(data, session_db):
                flash('Não é possivel adicionar entrada para esse dia', 'warning')
                session['date'] = data
                session['tipo_movimentacao'] = 'entrada'
                return redirect(url_for('estoque.movimentacoes_diarias'))

            recalculate_entries_balance(data, nova_entrada, session_db)
            session_db.add(nova_entrada)
            session_db.flush()

            log = Log(produto_id=produto_id, usuario_id=session.get('user_id'), operacao_id=nova_entrada.id, tipo_operacao='entrada', tipo_operacao_2='inserção')
            session_db.add(log)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            flash('Produto, Marca, Fornecedor ou Nota Fiscal não existe', 'danger')
        else:
            flash('Erro de integridade ao cadastrar entrada', 'danger')
    except:
        flash('Falha ao cadastrar entrada', 'danger')
    else:
        flash('Entrada cadastrada com sucesso!', 'success')

    session['date'] = data
    session['tipo_movimentacao'] = 'entrada'
    return redirect(url_for('estoque.movimentacoes_diarias'))


@entradas_bp.route('/editar/entrada/<int:entrada_id>/', methods=['POST'])
@login_required
def editar_entrada(entrada_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        session['tipo_movimentacao'] = 'entrada'
        return redirect(url_for('estoque.movimentacoes_diarias'))

    try:
        with get_session() as session_db:
            entrie = session_db.query(Entrada).filter_by(id=entrada_id).first()
            if not entrie:
                flash('Entrada não encontrada', 'danger')
                session['tipo_movimentacao'] = 'entrada'
                return redirect(url_for('estoque.movimentacoes_diarias'))
            
            entrie.quantidade = request.form.get('edit_quantidade_entrada')
            entrie.observacao = request.form.get('edit_observacao_entrada')
            entrie.marca_id = request.form.get('edit_marca_id_entrada')
            entrie.data_validade = request.form.get('edit_data_validade_entrada')
            entrie.fornecedor_id = request.form.get('edit_fornecedor_id_entrada')
            entrie.nota_fiscal_id = request.form.get('edit_nota_fiscal_id_entrada')
            
            if not validar_dados(entrie, True):
                raise Exception('Insira dados válidos')

            # Verifica se é possivel alterar o saldo do dia
            if not check_saldo(entrie.data_entrada, session_db):
                raise Exception('Não é possivel editar entrada nesse dia')

            recalculate_entries_balance(entrie.data_entrada, entrie, session_db, update=True)

            log = Log(produto_id=entrie.produto_id, usuario_id=session.get('user_id'), operacao_id=entrada_id, tipo_operacao='entrada', tipo_operacao_2='edição')
            session_db.add(log)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            flash('Produto, Marca, Fornecedor ou Nota Fiscal não existe', 'danger')
        else:
            flash('Erro de integridade ao cadastrar entrada', 'danger')
    except:
        flash('Falha ao atualizar entrada', 'danger')
    else:
        flash('Entrada atualizada com sucesso', 'success')

    session['date'] = entrie.data_entrada.isoformat()
    session['tipo_movimentacao'] = 'entrada'
    return redirect(url_for('estoque.movimentacoes_diarias'))


@entradas_bp.route('/excluir/entrada/<int:entrada_id>/', methods=['POST'])
@login_required
def excluir_entrada(entrada_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        session['tipo_movimentacao'] = 'entrada'
        return redirect(url_for('estoque.movimentacoes_diarias'))

    try:
        with get_session() as session_db:
            entrie = session_db.query(Entrada).filter_by(id=entrada_id).first()
            if not entrie:
                flash('Nãp foi possivel recuperar a entrada')
                return redirect(url_for('estoque.movimentacoes_diarias'))
            data_entrada = entrie.data_entrada.isoformat()

            # Verifica se é possivel alterar o saldo do dia
            if not check_saldo(entrie.data_entrada, session_db):
                flash('Não é possivel excluir saida para esse dia', 'danger')
                session['date'] = entrie.data_entrada.isoformat()
                session['tipo_movimentacao'] = 'entrada'
                return redirect(url_for('estoque.movimentacoes_diarias'))

            recalculate_entries_balance(entrie.data_entrada, entrie, session_db, delete=True)
            session_db.delete(entrie)

            log = Log(produto_id=entrie.produto_id, usuario_id=session.get('user_id'), operacao_id=entrada_id, tipo_operacao='entrada', tipo_operacao_2='exclusão')
            session_db.add(log)
    except:
        flash('Falha ao deletar entrada', 'danger')
    else:
        flash('Entrada deletada com sucesso', 'success')

    session['date'] = data_entrada
    session['tipo_movimentacao'] = 'entrada'
    return redirect(url_for('estoque.movimentacoes_diarias'))


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

    if nova_entrada.marca_id == 0 or nova_entrada.marca_id is None:
        if last_movement is None or last_movement.marca_id is None:
            nova_entrada.marca_id = 1
        else:
            nova_entrada.marca_id = last_movement.marca_id

    if nova_entrada.fornecedor_id == 0 or nova_entrada.fornecedor_id is None:
        if last_movement is None or last_movement.fornecedor_id is None:
            nova_entrada.fornecedor_id = 1
        else:
            nova_entrada.fornecedor_id = last_movement.fornecedor_id

    if nova_entrada.nota_fiscal_id == 0 or nova_entrada.nota_fiscal_id is None:
        if last_movement is None or last_movement.nota_fiscal_id is None:
            nova_entrada.nota_fiscal_id = 1
        else:
            nova_entrada.nota_fiscal_id = last_movement.nota_fiscal_id
