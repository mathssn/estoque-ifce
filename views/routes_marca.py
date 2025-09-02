from flask import Blueprint, request, session, render_template, redirect, flash, url_for

from utils.utils import login_required
from database.models import *
from database.db import get_session

marcas_bp = Blueprint('marcas', __name__)

@marcas_bp.route('/marcas/')
@login_required
def marcas_lista():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect('/')

    with get_session() as session_db:
        marcas = session_db.query(Marca).order_by(Marca.nome).all()
        produtos = {p.id: p for p in session_db.query(Produto).all()}

    return render_template('marcas.html', marcas=marcas, produtos=produtos)

@marcas_bp.route('/cadastro/marca/', methods=['POST'])
@login_required
def cadastro_marca():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('marcas.marcas_lista'))

    nome = request.form.get('nome')
    produto_id = request.form.get('produto_id')
    nova_marca = Marca(nome=nome, produto_id=produto_id)

    if not validar_dados_marca(nova_marca):
        flash('Insira um nome válido para a marca')
        return redirect(url_for('marcas.marcas_lista'))

    try:
        with get_session() as session_db:
            session_db.add(nova_marca)
    except Exception as e:
        flash(f'Falha ao cadastrar marca: {e}')
    else:
        flash('Marca cadastrada com sucesso!')

    return redirect(url_for('marcas.marcas_lista'))

@marcas_bp.route('/editar/marca/<int:marca_id>/', methods=['POST'])
@login_required
def editar_marca(marca_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('marcas.marcas_lista'))

    try:
        with get_session() as session_db:
            marca = session_db.query(Marca).filter_by(id=marca_id).first()

            if not marca:
                flash('Marca não encontrada')
                return redirect(url_for('marcas.marcas_lista'))

            marca.nome = request.form.get('edit_nome')
            marca.produto_id = request.form.get('edit_produto_id')

            if not validar_dados_marca(marca):
                flash('Insira um nome válido')
                return redirect(url_for('marcas.marcas_lista'))

    except Exception as e:
        flash(f'Falha ao atualizar marca: {e}')
    else:
        flash('Marca atualizada com sucesso!')

    return redirect(url_for('marcas.marcas_lista'))
    
def validar_dados_marca(marca: Marca):
    return bool(marca.nome and marca.nome.strip())
