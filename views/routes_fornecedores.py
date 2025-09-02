from flask import Blueprint, request, session, render_template, redirect, flash, url_for

from utils.utils import login_required
from database.models import *
from database.db import get_session

fornecedores_bp = Blueprint('fornecedores', __name__)

@fornecedores_bp.route('/fornecedores/')
@login_required
def fornecedores_lista():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect('/')

    with get_session() as session_db:
        fornecedores = session_db.query(Fornecedor).all()

    return render_template('fornecedores.html', fornecedores=fornecedores)


@fornecedores_bp.route('/cadastro/fornecedor/', methods=['POST'])
@login_required
def cadastro_fornecedor():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('fornecedores.fornecedores_lista'))
    
    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    email = request.form.get('email')

    novo_fornecedor = Fornecedor(nome=nome, telefone=telefone, email=email)
    
    if not validar_dados_fornecedor(novo_fornecedor):
        flash('Insira dados válidos para o fornecedor')
        return redirect(url_for('fornecedores.fornecedores_lista'))

    try:
        with get_session() as session_db:
            session_db.add(novo_fornecedor)

    except Exception as e:
        flash(f'Falha ao cadastrar fornecedor: {e}')
    else:
        flash('Fornecedor cadastrado com sucesso!')

    return redirect(url_for('fornecedores.fornecedores_lista'))

@fornecedores_bp.route('/editar/fornecedor/<int:fornecedor_id>/', methods=['POST'])
@login_required
def editar_fornecedor(fornecedor_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('fornecedores.lista'))

    try:
        with get_session() as session_db:
            fornecedor = session_db.query(Fornecedor).filter_by(id=fornecedor_id).first()
            fornecedor.nome = request.form.get('edit_nome')
            fornecedor.telefone = request.form.get('edit_telefone')
            fornecedor.email = request.form.get('edit_email')
            fornecedor.status = request.form.get('edit_status')

            if not validar_dados_fornecedor(fornecedor):
                flash('Insira dados válidos')
                return redirect(url_for('fornecedores.fornecedores_lista'))

    except Exception as e:
        flash(f'Falha ao atualizar fornecedor: {e}')
    else:
        flash('Fornecedor atualizado com sucesso!')

    return redirect(url_for('fornecedores.fornecedores_lista'))


def validar_dados_fornecedor(fornecedor: Fornecedor):
    if fornecedor.nome.strip() == '' or fornecedor.telefone.strip() == '' or fornecedor.email.strip() == '':
        return False

    if '@' not in fornecedor.email or '.' not in fornecedor.email:
        return False

    return True
