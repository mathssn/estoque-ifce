from flask import Blueprint, redirect, flash, url_for, request, session
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database.utils import check_saldo, recalculate_exits_balance, get_last_movement
from app.utils import login_required
from app.estoque.models import *
from app.database.db import get_session

saidas_bp = Blueprint('saidas', __name__, template_folder='templates')

@saidas_bp.route('/cadastro/saida/', methods=['POST'])
@login_required
def cadastro_saida():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    try:
        produto_id = int(request.form.get('produto_id'))
        refeicao_id = int(request.form.get('refeicao_id'))
        data = request.form.get('data_saida', '').strip()
        quantidade = int(request.form.get('quantidade', 0))
        observacao = request.form.get('observacao', '').strip()
        marca_id = int(request.form.get('marca_id'))
        data_validade = request.form.get('data_validade', '').strip()
        fornecedor_id = int(request.form.get('fornecedor_id', 0))
        nota_fiscal_id = int(request.form.get('nota_fiscal_id', 0))
    except (ValueError, TypeError):
        flash('Insira dados válidos', 'danger')
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    nova_saida = Saida(produto_id=produto_id, refeicao_id=refeicao_id, data_saida=data, quantidade=quantidade, observacao=observacao, usuario_id=session['user_id'], marca_id=marca_id, data_validade=data_validade, fornecedor_id=fornecedor_id, nota_fiscal_id=nota_fiscal_id)

    if not validar_dados(nova_saida):
        flash('Insira dados válidos para o cadastro da saída.', 'danger')
        session['date'] = data
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    try:
        with get_session() as session_db:
            last_movement = get_last_movement(produto_id, session_db)
            if last_movement != None:
                verify_fields(last_movement, nova_saida)

            if not check_saldo(data, session_db):
                flash('Não é possível adicionar saída para esse dia', 'danger')
                session['date'] = data
                return redirect(url_for('estoque.movimentacoes_diarias'))

            n = recalculate_exits_balance(data, nova_saida, session_db)
            if n == 1:
                flash('Não é possive atuliazar o saldo do dia', 'danger')
                session['date'] = data
                return redirect(url_for('estoque.movimentacoes_diarias'))
            elif n == 2:
                flash('Essa valor excede o saldo em estoque!', 'danger')
                session['date'] = data
                return redirect(url_for('estoque.movimentacoes_diarias'))

            session_db.add(nova_saida)
            session_db.flush()

            log = Log(produto_id=produto_id, usuario_id=session.get('user_id'), operacao_id=nova_saida.id, tipo_operacao='saida', tipo_operacao_2='inserção')
            session_db.add(log)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            flash('Produto, Marca, Fornecedor, Refeição ou Nota Fiscal não existe', 'danger')
        else:
            flash('Erro de integridade ao cadastrar entrada', 'danger')
    except:
        flash('Falha ao cadastrar saída', 'danger')
    else:
        flash('Saída cadastrada com sucesso!', 'success')

    session['date'] = data
    return redirect(url_for('estoque.movimentacoes_diarias'))


@saidas_bp.route('/editar/saida/<int:saida_id>/', methods=['POST'])
@login_required
def editar_saida(saida_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    try:
        with get_session() as session_db:
            exit = session_db.query(Saida).filter_by(id=saida_id).first()
            if not exit:
                flash('Saida não encontrada', 'danger')
                return redirect(url_for('estoque.movimentacoes_diarias'))

            exit.refeicao_id = request.form.get('edit_refeicao_id_saida')
            exit.quantidade = request.form.get('edit_quantidade_saida')
            exit.observacao = request.form.get('edit_observacao_saida')
            exit.marca_id = request.form.get('edit_marca_id_saida')
            exit.data_validade = request.form.get('edit_data_validade_saida')
            exit.fornecedor_id = request.form.get('edit_fornecedor_id_saida')
            exit.nota_fiscal_id = request.form.get('edit_nota_fiscal_id_saida')
            
            if not validar_dados(exit, True):
                raise Exception('Insira dados válidos para a edição da saída.')

            if not check_saldo(exit.data_saida, session_db):
                raise Exception('Não é possível editar saída nesse dia')

            recalculate_exits_balance(exit.data_saida, exit, session_db)

            log = Log(produto_id=exit.produto_id, usuario_id=session.get('user_id'), operacao_id=saida_id, tipo_operacao='saida', tipo_operacao_2='edição')
            session_db.add(log)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            flash('Produto, Marca, Fornecedor, Refeição ou Nota Fiscal não existe', 'danger')
        else:
            flash('Erro de integridade ao cadastrar entrada', 'danger')
    except:
        flash('Falha ao atualizar saída', 'danger')
    else:
        flash('Saída atualizada com sucesso!', 'success')

    session['date'] = exit.data_saida.isoformat()
    return redirect(url_for('estoque.movimentacoes_diarias'))


@saidas_bp.route('/excluir/saida/<int:saida_id>/', methods=['POST'])
@login_required
def excluir_saida(saida_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('estoque.movimentacoes_diarias'))
    
    try:
        with get_session() as session_db:
            exit = session_db.query(Saida).filter_by(id=saida_id).first()
            if not exit:
                flash('Nãp foi possivel recuperar a saida')
                return redirect(url_for('estoque.movimentacoes_diarias'))

            if not check_saldo(exit.data_saida, session_db):
                flash('Não é possível excluir saída para esse dia. Saldo bloqueado.', 'danger')
                session['date'] = exit.data_saida.isoformat()
                return redirect(url_for('estoque.movimentacoes_diarias'))

            recalculate_exits_balance(exit.data_saida, exit, session_db, delete=True)
            session_db.delete(exit)

            log = Log(produto_id=exit.produto_id, usuario_id=session.get('user_id'), operacao_id=saida_id, tipo_operacao='saida', tipo_operacao_2='exclusão')
            session_db.add(log)
    except:
        flash('Falha ao deletar saída', 'danger')
    else:
        flash('Saída deletada com sucesso!', 'success')

    session['date'] = exit.data_saida.isoformat()
    return redirect(url_for('estoque.movimentacoes_diarias'))


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


def verify_fields(last_movement: Saida, nova_saida: Saida):
    if nova_saida.data_validade == '':
        if last_movement is None or last_movement.data_validade is None:
            raise Exception('Insira uma data de validade')
        else:
            nova_saida.data_validade = last_movement.data_validade

    if nova_saida.marca_id == 0 or nova_saida.marca_id is None:
        if last_movement is None or last_movement.marca_id is None:
            nova_saida.marca_id = 1
        else:
            nova_saida.marca_id = last_movement.marca_id

    if nova_saida.fornecedor_id == 0 or nova_saida.fornecedor_id is None:
        if last_movement is None or last_movement.fornecedor_id is None:
            nova_saida.fornecedor_id = 1
        else:
            nova_saida.fornecedor_id = last_movement.fornecedor_id

    if nova_saida.nota_fiscal_id == 0 or nova_saida.nota_fiscal_id is None:
        if last_movement is None or last_movement.nota_fiscal_id is None:
            nova_saida.nota_fiscal_id = 1
        else:
            nova_saida.nota_fiscal_id = last_movement.nota_fiscal_id
