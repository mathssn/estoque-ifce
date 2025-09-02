from flask import Blueprint, render_template, redirect, flash, url_for, request, session
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from database.utils import list_movementation_by_product
from utils.utils import login_required
from database.models import *
from database.db import get_session

produtos_bp = Blueprint('produtos', __name__)

@produtos_bp.route('/produtos/')
@login_required
def produtos_lista():
    with get_session() as session_db:
        produtos_list = session_db.query(Produto).all()
    
    for produto in produtos_list.copy():
        if produto.status == 'inativo' and session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
            produtos_list.remove(produto)

    return render_template('produtos.html', produtos=produtos_list)

@produtos_bp.route('/cadastro/produtos/', methods=['POST'])
@login_required
def cadastro_produtos():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('produtos.produtos_lista'))
    
    codigo = request.form.get('codigo')
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    unidade = request.form.get('unidade')
    quantidade_minima = request.form.get('quantidade_minima')
    status = request.form.get('status')


    novo_produto = Produto(codigo=codigo, nome=nome, descricao=descricao, unidade=unidade, quantidade_minima=quantidade_minima, status=status)
    if not validar_dados(novo_produto):
        flash('Insira dados válidos')
        return redirect(url_for('produtos.produtos_lista'))

    try:
        with get_session() as session_db:
            session_db.add(novo_produto)

            # Cria a entrada inicial do produto
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
            
    except Exception as e:
        flash(f'Falha ao cadastrar produto: {e}')
    else:
        flash('Produto cadastrado com sucesso!')

    return redirect(url_for('produtos.produtos_lista'))

@produtos_bp.route('/editar/produto/<int:produto_id>/', methods=['POST'])
@login_required
def editar_produto(produto_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('produtos.produtos_lista'))
    
    try:
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            produto.codigo = request.form.get('edit_codigo')
            produto.nome = request.form.get('edit_nome')
            produto.descricao = request.form.get('edit_descricao')
            produto.unidade = request.form.get('edit_unidade')
            produto.quantidade_minima = request.form.get('edit_quantidade_minima')
            produto.status = request.form.get('edit_status')

            if not validar_dados(produto):
                flash('Insira dados válidos')
                return redirect(url_for('produtos.produtos_lista'))

    except Exception as e:
        flash(f'Falha ao atualizar produto: {e}')
    else:
        flash('Produto atualizado com sucesso!')

    return redirect(url_for('produtos.produtos_lista'))


@produtos_bp.route('/excluir/produto/<int:produto_id>/', methods=['POST'])
@login_required
def excluir_produto(produto_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('produtos.produtos_lista'))
    
    try:
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            session_db.delete(produto)
    except Exception as e:
        flash(f'Falha ao deletar produto: {e}')
    else:
        flash('Produto deletado com sucesso!')

    return redirect(url_for('produtos.produtos_lista'))


@produtos_bp.route('/movimentacao/<int:produto_id>/')
@login_required
def movimentacao_por_produto(produto_id):
    page = request.args.get('page', default=1, type=int)
    p_page = 20
    offset = (page - 1) * p_page
    movimentacoes: list[dict] = []
    logs_saidas = {}
    logs_entradas = {}
    total = 0
    
    try:
        movimentacoes, total = list_movementation_by_product(produto_id, p_page, offset)
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            destinos = {d.id: d for d in session_db.query(Destino).all()}
            usuarios = {u.id: u for u in session_db.query(Usuario).all()}
            
            for movimentacao in movimentacoes:
                log = session_db.query(Log).filter_by(operacao_id=movimentacao.get('id')).filter_by(tipo_operacao_2='inserção').filter_by(tipo_operacao=movimentacao.get('tipo')).first()
                if log:
                    if movimentacao.get('tipo') == 'saida':
                        logs_saidas[movimentacao['id']] = log
                    elif movimentacao.get('tipo') == 'entrada':
                        logs_entradas[movimentacao['id']] = log

    except Exception as e:
        flash(f'{e}')
        return redirect('/')
    
    if produto == None:
        flash('Produto não encontrado')
        return redirect('/')
    
    produto.nome = produto.nome.replace('\n', ' ')
    total_pages = (total + p_page - 1) // p_page
    
    return render_template('movimentacao_por_produto.html', movimentacoes=movimentacoes, produto=produto, destinos=destinos, page=page, total_pages=total_pages, usuarios=usuarios, logs_saidas=logs_saidas, logs_entradas=logs_entradas)

def validar_dados(produto: Produto):
    if produto.codigo == '' or produto.nome == '' or produto.quantidade_minima == '' or produto.status == '':
        return False
    
    try:
        codigo = int(produto.codigo)
        quantidade_minima = int(produto.quantidade_minima)
    except (ValueError, TypeError):
        return False

    if codigo < 0 or quantidade_minima <= 0:
        return False
    
    if produto.status not in ['ativo', 'inativo'] :
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
                s = SaldoDiario(produto_id=saldo.produto_id, data=data_mais_recente.isoformat(), quantidade_inicial=saldo.quantidade_final, entradas=0, saídas=0, quantidade_final=saldo.quantidade_final)
                session_db.add(s)

            if data_mais_recente == data:
                fechado = False
            else:
                fechado = True
            
            dia = DiasFechados(data_mais_recente.isoformat(), fechado)
            session_db.add(dia)
