from flask import Blueprint, request, session, render_template, redirect, flash, url_for
from sqlalchemy.exc import IntegrityError

from app.utils import login_required, role_required
from app.models import *
from app.database.db import get_session

fornecedores_bp = Blueprint('fornecedores', __name__, template_folder='templates')

@fornecedores_bp.route('/fornecedores/')
@login_required
def fornecedores_lista():
    try:
        with get_session() as session_db:
            fornecedores = session_db.query(Fornecedor).all()
    except:
        flash('Erro ao recuperar fornecedores')
        return redirect('/')

    return render_template('main/fornecedores.html', fornecedores=fornecedores)


@fornecedores_bp.route('/cadastro/fornecedor/', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista')
def cadastro_fornecedor():
    nome = request.form.get('nome', '').strip()
    telefone = request.form.get('telefone', '').strip()
    email = request.form.get('email', '').strip()

    novo_fornecedor = Fornecedor(nome=nome, telefone=telefone, email=email)
    
    if not validar_dados_fornecedor(novo_fornecedor):
        flash('Insira dados válidos para o fornecedor', 'danger')
        return redirect(url_for('fornecedores.fornecedores_lista'))

    try:
        with get_session() as session_db:
            session_db.add(novo_fornecedor)
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'unique' in msg or 'duplicate' in msg:
            flash('Telefone ou email já cadastrados!', 'danger')
        else:
            flash('Erro de integridade ao cadastrar fornecedor!', 'danger')
    except:
        flash('Falha ao cadastrar fornecedor!', 'danger')
    else:
        flash('Fornecedor cadastrado com sucesso!', 'success')

    return redirect(url_for('fornecedores.fornecedores_lista'))

@fornecedores_bp.route('/editar/fornecedor/<int:fornecedor_id>/', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista')
def editar_fornecedor(fornecedor_id):
    try:
        with get_session() as session_db:
            fornecedor = session_db.query(Fornecedor).filter_by(id=fornecedor_id).first()
            if not fornecedor:
                flash('Fornecedor não encontrado', 'danger')
                return redirect(url_for('fornecedores.fornecedores_lista'))
            
            fornecedor.nome = request.form.get('edit_nome', '').strip()
            fornecedor.telefone = request.form.get('edit_telefone', '').strip()
            fornecedor.email = request.form.get('edit_email', '').strip()
            fornecedor.status = request.form.get('edit_status', '').strip()

            if not validar_dados_fornecedor(fornecedor):
                raise Exception('Insira dados válidos')

    except:
        flash('Falha ao atualizar fornecedor!', 'danger')
    else:
        flash('Fornecedor atualizado com sucesso!', 'success')

    return redirect(url_for('fornecedores.fornecedores_lista'))


def validar_dados_fornecedor(fornecedor: Fornecedor):
    if not fornecedor.nome or not fornecedor.telefone or not fornecedor.email:
        return False

    if '@' not in fornecedor.email or '.' not in fornecedor.email:
        return False

    try:
        for n in fornecedor.telefone:
            if n not in ['-', '(', ')', ' ']:
                int(n)
    except (TypeError, ValueError):
        return False

    return True
