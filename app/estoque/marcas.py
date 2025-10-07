from flask import Blueprint, request, session, render_template, redirect, flash, url_for
from sqlalchemy.exc import IntegrityError

from app.utils import login_required
from app.estoque.models import *
from app.models import *
from app.database.db import get_session

marcas_bp = Blueprint('marcas', __name__, template_folder='templates')

@marcas_bp.route('/marcas/')
@login_required
def marcas_lista():
    page = request.args.get('page', default=1, type=int)
    p_page = 10
    offset = (page - 1) * p_page

    try:
        with get_session() as session_db:
            query = session_db.query(Marca).order_by(Marca.nome)
            
            total = query.count()
            marcas = query.offset(offset).limit(p_page).all()
            total_pages = (total + p_page - 1) // p_page

            produtos = {p.id: p for p in session_db.query(Produto).all()}
    except:
        flash('Falha ao recuperar marcas', 'danger')
        return redirect(url_for('main.index'))

    return render_template('estoque/marcas.html', marcas=marcas, produtos=produtos, page=page, total_pages=total_pages)

@marcas_bp.route('/cadastro/marca/', methods=['POST'])
@login_required
def cadastro_marca():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('marcas.marcas_lista'))

    try:
        nome = request.form.get('nome', '').strip()
        produto_id = int(request.form.get('produto_id'))
    except (ValueError, TypeError):
        flash('Insira valores válidos', 'danger')
        return redirect(url_for('marcas.marcas_lista'))

    nova_marca = Marca(nome=nome, produto_id=produto_id)

    if not validar_dados_marca(nova_marca):
        flash('Insira um nome válido para a marca', 'danger')
        return redirect(url_for('marcas.marcas_lista'))

    try:
        with get_session() as session_db:
            session_db.add(nova_marca)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            flash('Produto inexistente', 'danger')
        else:
            flash('Erro de integridade ao cadastrar marca', 'danger')
    except:
        flash('Falha ao cadastrar marca', 'danger')
    else:
        flash('Marca cadastrada com sucesso!', 'success')

    return redirect(url_for('marcas.marcas_lista'))

@marcas_bp.route('/editar/marca/<int:marca_id>/', methods=['POST'])
@login_required
def editar_marca(marca_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('marcas.marcas_lista'))

    try:
        with get_session() as session_db:
            marca = session_db.query(Marca).filter_by(id=marca_id).first()

            if not marca:
                flash('Marca não encontrada', 'danger')
                return redirect(url_for('marcas.marcas_lista'))

            try:
                marca.nome = request.form.get('edit_nome', '').strip()
                marca.produto_id = int(request.form.get('edit_produto_id'))
            except (ValueError, TypeError):
                flash('Insira dados válidos', 'danger')
                return redirect(url_for('marcas.marcas_lista'))

            if not validar_dados_marca(marca):
                raise Exception('Insira um nome válido')

    except:
        flash('Falha ao atualizar marca', 'danger')
    else:
        flash('Marca atualizada com sucesso!', 'success')

    return redirect(url_for('marcas.marcas_lista'))
    
def validar_dados_marca(marca: Marca):
    return bool(marca.nome and marca.nome.strip())
