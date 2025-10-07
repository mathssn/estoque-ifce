from flask import Blueprint, render_template, redirect, flash, url_for, request, session
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.utils import login_required
from app.models import *
from app.estoque.models import *
from app.database.db import get_session

produtos_bp = Blueprint('produtos', __name__, template_folder='templates')

@produtos_bp.route('/produtos/')
@login_required
def produtos_lista():
    try:
        with get_session() as session_db:
            produtos_list = session_db.query(Produto).all()
    except:
        flash('Erro ao recuperar produtos!', 'danger')
        return redirect('/')
    
    for produto in produtos_list.copy():
        if produto.status == 'inativo' and session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
            produtos_list.remove(produto)

    return render_template('main/produtos.html', produtos=produtos_list)

@produtos_bp.route('/cadastro/produtos/', methods=['POST'])
@login_required
def cadastro_produtos():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('produtos.produtos_lista'))
    
    try:
        codigo = int(request.form.get('codigo', 0))
        nome = request.form.get('nome').strip()
        descricao = request.form.get('descricao').strip()
        unidade = request.form.get('unidade').strip()
        quantidade_minima = int(request.form.get('quantidade_minima', 0))
        tipo = request.form.get('tipo').strip()
        status = 'ativo'
    except (TypeError, ValueError):
        flash('Valores invalidos', 'danger')
        return redirect(url_for('produtos.produtos_lista'))

    novo_produto = Produto(codigo=codigo, nome=nome, descricao=descricao, unidade=unidade, quantidade_minima=quantidade_minima, status=status, tipo=tipo)
    if not validar_dados(novo_produto):
        flash('Insira dados válidos', 'danger')
        return redirect(url_for('produtos.produtos_lista'))

    try:
        with get_session() as session_db:
            session_db.add(novo_produto)

            if tipo == 'nao_perecivel':
                data_atual = date.today().isoformat()
                verificar_dia_aberto(data_atual, session_db)

                dia = session_db.query(DiasFechados).filter_by(data=data_atual).first()
                if not dia:
                    dia = DiasFechados(data=data_atual, fechado=False)
                    session_db.add(dia)
                elif dia.fechado:
                    raise Exception('Não é possivel cadastrar produtos nesse dia, pois o dia está fechado!')

                saldo_diario = SaldoDiario(produto_id=novo_produto.id, data=data_atual, quantidade_inicial=0, quantidade_entrada=0, quantidade_saida=0, quantidade_final=0)
                session_db.add(saldo_diario)
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'uix_codigo_tipo' in msg:
            flash('Código já existente!', 'danger')
        else:
            flash('Erro de integridade ao cadastrar o produto!', 'danger')
    except:
        flash('Falha ao cadastrar produto!', 'danger')
    else:
        flash('Produto cadastrado com sucesso!', 'success')

    return redirect(url_for('produtos.produtos_lista'))

@produtos_bp.route('/editar/produto/<int:produto_id>/', methods=['POST'])
@login_required
def editar_produto(produto_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('produtos.produtos_lista'))
    
    try:
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            if not produto:
                flash('Produto não encontrado', 'danger')
                return redirect(url_for('produtos.produtos_lista'))
            
            produto.nome = request.form.get('edit_nome')
            produto.descricao = request.form.get('edit_descricao')
            produto.unidade = request.form.get('edit_unidade')
            produto.quantidade_minima = request.form.get('edit_quantidade_minima')
            produto.tipo = request.form.get('edit_tipo')
            produto.status = request.form.get('edit_status')

            if not validar_dados(produto):
                flash('Insira dados válidos', 'danger')
                raise Exception()

    except:
        flash('Falha ao atualizar produto!', 'danger')
    else:
        flash('Produto atualizado com sucesso!', 'success')

    return redirect(url_for('produtos.produtos_lista'))


@produtos_bp.route('/excluir/produto/<int:produto_id>/', methods=['POST'])
@login_required
def excluir_produto(produto_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('produtos.produtos_lista'))
    
    try:
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            session_db.delete(produto)
    except IntegrityError:
        flash('Não é possivel deletar este produto!', 'danger')
    except:
        flash('Falha ao deletar produto!', 'danger')
    else:
        flash('Produto deletado com sucesso!', 'success')

    return redirect(url_for('produtos.produtos_lista'))


def validar_dados(produto: Produto):
    if not produto.codigo or not produto.nome or not produto.quantidade_minima or not produto.status or not produto.tipo:
        return False
    
    try:
        codigo = int(produto.codigo)
        quantidade_minima = int(produto.quantidade_minima)
    except (ValueError, TypeError):
        return False

    if codigo < 0 or quantidade_minima < 0:
        return False
    
    if produto.status not in ['ativo', 'inativo'] :
        return False

    if "'" in produto.nome:
        return False
    
    return True

def verificar_dia_aberto(data: str, session_db: Session):
    mais_recente = session_db.query(DiasFechados).filter_by(fechado=False).order_by(DiasFechados.data.desc()).first()
    if mais_recente == None:
        return
    
    data_mais_recente = datetime.strptime(mais_recente.data.isoformat(), '%Y-%m-%d').date()
    data = datetime.strptime(data, '%Y-%m-%d').date()
    saldos_diarios = session_db.query(SaldoDiario).filter_by(data=data_mais_recente.isoformat()).all()

    if data_mais_recente == data:
        return

    if data_mais_recente < data:
        mais_recente.fechado = True

        while data_mais_recente < data:
            data_mais_recente += timedelta(days=1)

            for saldo in saldos_diarios:
                s = SaldoDiario(produto_id=saldo.produto_id, data=data_mais_recente.isoformat(), quantidade_inicial=saldo.quantidade_final, quantidade_entrada=0, quantidade_saida=0, quantidade_final=saldo.quantidade_final)
                session_db.add(s)

            if data_mais_recente == data:
                fechado = False
            else:
                fechado = True
            
            dia = DiasFechados(data_mais_recente.isoformat(), fechado)
            session_db.add(dia)
