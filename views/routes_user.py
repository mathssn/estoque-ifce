from flask import Blueprint, render_template, redirect, flash, url_for, request, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from utils.utils import login_required
from database.models import *
from database.db import get_session

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.route('/usuarios')
@login_required
def usuarios_lista():
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada')
        return redirect('/')

    with get_session() as session_db:
        usuarios = session_db.query(Usuario).all()

    return render_template('usuarios.html', usuarios=usuarios)


@usuarios_bp.route('/cadastro/usuarios', methods=['POST'])
@login_required
def cadastro_usuarios():
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada')
        return redirect('/')

    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    data_nascimento = request.form.get('data_nascimento')
    nivel_acesso = request.form.get('nivel_acesso')

    novo_usuario = Usuario(nome=nome, email=email, senha=senha, data_nascimento=data_nascimento, nivel_acesso=nivel_acesso)
    if not validar_dados(novo_usuario):
        flash('Insira dados válidos')
        return redirect(url_for('usuarios.usuarios_lista'))
    
    novo_usuario.senha = generate_password_hash(novo_usuario.senha)

    try:
        with get_session() as session_db:
            session_db.add(novo_usuario)
    except Exception as e:
        flash(f'Erro ao cadastrar usuario: {e}')
    else:
        flash('Usuário cadastrado com sucesso')    
    return redirect(url_for('usuarios.usuarios_lista'))


@usuarios_bp.route('/editar/usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissao negada')
        return redirect('/')
    
    try:
        with get_session() as session_db:
            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
        
            usuario.nome = request.form.get('edit_nome')
            usuario.email = request.form.get('edit_email')
            usuario.data_nascimento = request.form.get('edit_data_nascimento')
            usuario.nivel_acesso = request.form.get('edit_nivel_acesso')
            usuario.status = request.form.get('edit_status')

            if not validar_dados(usuario):
                flash('Insira dadados válidos')
                return redirect(url_for('usuarios.usuarios_lista'))            

    except Exception as e:
        flash(f'Erro ao editar usuario: {e}')
    else:
        flash('Usuário editado com sucesso')    

    return redirect(url_for('usuarios.usuarios_lista'))

@usuarios_bp.route('/perfil/<int:user_id>')
@login_required
def perfil_usuario(user_id):
    if user_id != session.get('user_id'):
        flash('Permisão negada')
        return redirect('/')

    with get_session() as session_db:
        user = session_db.query(Usuario).filter_by(id=user_id).first()
        if user == None:
            flash('Usuário não encontrado')
            return redirect('/')
    
    return render_template('usuario.html', usuario=user)

@usuarios_bp.route('/usuario/alterar-senha/<int:user_id>', methods=['POST'])
@login_required
def alterar_senha(user_id):
    if user_id != session.get('user_id'):
        flash('Permissão negada')
        return redirect('/')
    
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmacao = request.form.get('confirmar_senha')

    if nova_senha != confirmacao:
        flash('As senhas devem ser identicas!')
        return redirect(url_for('usuarios.perfil_usuario', user_id=user_id))

    try:
        with get_session() as session_db:
            user = session_db.query(Usuario).filter_by(id=user_id).first()
            if not user:
                flash('Não é possivel encontrar o usuário')
                return redirect('/')

            if not check_password_hash(user.senha, senha_atual):
                flash('Senha incorreta')
                return redirect(url_for('usuarios.perfil_usuario', user_id=user_id))

            senha_nova_hash = generate_password_hash(nova_senha)
            user.senha = senha_nova_hash
    except Exception as e:
        flash('Não foi possivel mudar sua senha')
    else:
        flash('Senha alterada com sucesso')

    return redirect(url_for('usuarios.perfil_usuario', user_id=user_id))


@usuarios_bp.route('/usuarios/resetar-senha/<int:user_id>', methods=['POST'])
@login_required
def resetar_senha(user_id):
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada')
        return redirect('/')

    senha_superusuario = request.form.get('senha_confirmacao')

    try:
        with get_session() as session_db:
            superusuario = session_db.query(Usuario).filter_by(id=session.get('user_id')).first()
            if superusuario == None:
                flash('Erro ao recuperar usuário')
                return redirect('/')
            
            if not check_password_hash(superusuario.senha, senha_superusuario):
                flash('Senha incorreta!')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
            if usuario == None:
                flash('Usuário não encontrado')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario.senha = generate_password_hash('12345678')
    except Exception as e:
        flash(f'Erro ao resetar senha: {e}')
    else:
        flash('Senha resetada com sucesso!')
    
    return redirect(url_for('usuarios.usuarios_lista'))

def validar_dados(usuario: Usuario):
    if usuario.nome == '' or usuario.email == '' or usuario.senha == '' or usuario.data_nascimento == '':
        return False
    
    try:
        datetime.strptime(usuario.data_nascimento, '%Y-%m-%d')
    except ValueError:
        return False
    
    return True