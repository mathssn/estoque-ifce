from flask import render_template, redirect, flash, url_for, request, session
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from app.utils import login_required
from app.usuarios.models import Usuario
from app.database.db import get_session

from . import usuarios_bp


@usuarios_bp.route('/usuarios')
@login_required
def usuarios_lista():
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('main.index'))

    try:
        with get_session() as session_db:
            usuarios = session_db.query(Usuario).all()
    except Exception as e:
        flash(f'Erro recuperar usuarios: {e}', 'danger')
        return redirect('/')

    return render_template('usuarios/usuarios.html', usuarios=usuarios)


@usuarios_bp.route('/cadastro/usuarios', methods=['POST'])
@login_required
def cadastro_usuarios():
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('main.index'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    data_nascimento = request.form.get('data_nascimento')
    nivel_acesso = request.form.get('nivel_acesso')

    senha = generate_password_hash(senha)

    novo_usuario = Usuario(nome=nome, email=email, senha=senha, data_nascimento=data_nascimento, nivel_acesso=nivel_acesso)
    if not validar_dados(novo_usuario):
        flash('Insira dados válidos', 'danger')
        return redirect(url_for('usuarios.usuarios_lista'))
    
    try:
        with get_session() as session_db:
            session_db.add(novo_usuario)
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'unique' in msg or 'duplicate' in msg:
            flash('Já existe um usuario com este e-mail!', 'danger')
        else:
            flash(f'Erro de integridade ao cadastrar usuario: {e}', 'danger')
    except:
        flash('Erro ao cadastrar usuario!', 'danger')
    else:
        flash('Usuário cadastrado com sucesso', 'success')    

    return redirect(url_for('usuarios.usuarios_lista'))


@usuarios_bp.route('/editar/usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('main.index'))
    
    try:
        with get_session() as session_db:
            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
            if not usuario:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))
        
            usuario.nome = request.form.get('edit_nome')
            usuario.email = request.form.get('edit_email')
            usuario.data_nascimento = request.form.get('edit_data_nascimento')
            usuario.nivel_acesso = request.form.get('edit_nivel_acesso')
            usuario.status = request.form.get('edit_status')

            if not validar_dados(usuario):
                raise Exception('Insira dadados válidos')
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'unique' in msg or 'duplicate' in msg:
            flash('Já existe um usuario com este e-mail!', 'danger')
        else:
            flash(f'Erro de integridade ao editar usuario: {e}', 'danger')
    except:
        flash('Erro ao editar usuario!', 'danger')
    else:
        flash('Usuário editado com sucesso', 'success')    

    return redirect(url_for('usuarios.usuarios_lista'))

@usuarios_bp.route('/perfil-usuario')
@login_required
def perfil_usuario():
    try:
        with get_session() as session_db:
            user = session_db.query(Usuario).filter_by(id=session.get('user_id')).first()
            if user == None:
                flash('Usuário não encontrado', 'danger')
                return redirect('/')
    except:
        flash('Não foi possivel acessar o perfil', 'danger')
        return redirect('/')
        
    return render_template('usuarios/usuario.html', usuario=user)

@usuarios_bp.route('/usuario/alterar-senha/<int:user_id>', methods=['POST'])
@login_required
def alterar_senha(user_id):
    if user_id != session.get('user_id'):
        flash('Permissão negada', 'warning')
        return redirect('/')
    
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirmacao = request.form.get('confirmar_senha')

    if nova_senha != confirmacao:
        flash('As senhas devem ser identicas!', 'warning')
        return redirect(url_for('usuarios.perfil_usuario'))

    try:
        with get_session() as session_db:
            user = session_db.query(Usuario).filter_by(id=user_id).first()
            if not user:
                flash('Não é possivel encontrar o usuário', 'danger')
                return redirect('/')

            if not check_password_hash(user.senha, senha_atual):
                flash('Senha incorreta', 'danger')
                return redirect(url_for('usuarios.perfil_usuario'))

            senha_nova_hash = generate_password_hash(nova_senha)
            user.senha = senha_nova_hash
    except:
        flash('Não foi possivel alterar sua senha', 'danger')
    else:
        flash('Senha alterada com sucesso', 'success')

    return redirect(url_for('usuarios.perfil_usuario'))


@usuarios_bp.route('/usuarios/resetar-senha/<int:user_id>', methods=['POST'])
@login_required
def resetar_senha(user_id):
    if session.get('nivel_acesso') not in ['Superusuario']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('main.index'))

    senha_superusuario = request.form.get('senha_confirmacao')

    try:
        with get_session() as session_db:
            superusuario = session_db.query(Usuario).filter_by(id=session.get('user_id')).first()
            if superusuario == None:
                flash('Erro ao recuperar usuário', 'danger')
                return redirect(url_for('main.index'))
            
            if not check_password_hash(superusuario.senha, senha_superusuario):
                flash('Senha incorreta!', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
            if usuario == None:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario.senha = generate_password_hash('12345678')
    except:
        flash('Erro ao resetar senha', 'danger')
    else:
        flash('Senha resetada com sucesso!', 'success')
    
    return redirect(url_for('usuarios.usuarios_lista'))

def validar_dados(usuario: Usuario):
    if not usuario.nome or not usuario.email or not usuario.senha or not usuario.data_nascimento:
        return False

    if '@' not in usuario.email or '.' not in usuario.email:
        return False

    try:
        if isinstance(usuario.data_nascimento, str):
            datetime.strptime(usuario.data_nascimento, '%Y-%m-%d')
        elif not isinstance(usuario.data_nascimento, date):
            return False
    except ValueError:
        return False
    
    return True