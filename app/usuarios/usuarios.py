from flask import render_template, redirect, flash, url_for, request, session
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from app.utils import login_required, role_required
from app.usuarios.models import Usuario
from app.models import Role, RoleUser
from app.database.db import get_session

from . import usuarios_bp


@usuarios_bp.route('/usuarios')
@login_required
@role_required('admin')
def usuarios_lista():
    try:
        with get_session() as session_db:
            usuarios = session_db.query(Usuario).all()
            roles = session_db.query(Role).all()
            roles_users = session_db.query(RoleUser).all()

            roles_por_usuario = {}
            for ru in roles_users:
                if ru.ativado:
                    roles_por_usuario.setdefault(ru.usuario_id, []).append(ru.role_id)
    except Exception as e:
        flash(f'Erro recuperar usuarios: {e}', 'danger')
        return redirect('/')

    return render_template('usuarios/usuarios.html', usuarios=usuarios, roles=roles, roles_por_usuario=roles_por_usuario)


@usuarios_bp.route('/cadastro/usuarios', methods=['POST'])
@login_required
@role_required('admin')
def cadastro_usuarios():
    try:
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        data_nascimento = request.form.get('data_nascimento', '').strip()
        roles_ids = [int(n) for n in request.form.getlist('roles')]
    except:
        flash('insira dados válidos', 'danger')
        return redirect(url_for('usuarios.usuarios_lista'))

    senha = generate_password_hash(senha)

    novo_usuario = Usuario(nome=nome, email=email, senha=senha, data_nascimento=data_nascimento)
    if not validar_dados(novo_usuario):
        flash('Insira dados válidos', 'danger')
        return redirect(url_for('usuarios.usuarios_lista'))
    
    try:
        with get_session() as session_db:
            session_db.add(novo_usuario)
            session_db.flush()
            roles = session_db.query(Role).all()
            for role in roles:
                ativado = False
                if role.id in roles_ids:
                    ativado = True

                role_user = RoleUser(usuario_id=novo_usuario.id, role_id=role.id, ativado=ativado)
                session_db.add(role_user)
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
@role_required('admin')
def editar_usuario(user_id):
    try:
        with get_session() as session_db:
            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
            if not usuario:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))
        
            usuario.nome = request.form.get('edit_nome')
            usuario.email = request.form.get('edit_email')
            usuario.data_nascimento = request.form.get('edit_data_nascimento')
            usuario.status = request.form.get('edit_status')
            roles_ids = [int(n) for n in request.form.getlist('roles')]
            roles = session_db.query(Role).all()
            for role in roles:
                ativado = False
                if role.id in roles_ids:
                    ativado = True

                role_user = session_db.query(RoleUser).filter_by(usuario_id=usuario.id).filter_by(role_id=role.id).first()
                if not role_user:
                    role_user = RoleUser(usuario_id=usuario.id, role_id=role.id, ativado=ativado)
                    session_db.add(role_user)
                elif role_user:
                    role_user.ativado = ativado

            if not validar_dados(usuario):
                raise Exception('Insira dadados válidos')
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'unique' in msg or 'duplicate' in msg:
            flash('Já existe um usuario com este e-mail!', 'danger')
        else:
            flash(f'Erro de integridade ao editar usuario: {e}', 'danger')
    except Exception as e:
        flash(f'Erro ao editar usuario! {e}', 'danger')
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
@role_required('admin')
def resetar_senha(user_id):
    senha_admin = request.form.get('senha_confirmacao')

    try:
        with get_session() as session_db:
            admin = session_db.query(Usuario).filter_by(id=session.get('user_id')).first()
            if admin == None:
                flash('Erro ao recuperar usuário', 'danger')
                return redirect(url_for('main.index'))
            
            if not check_password_hash(admin.senha, senha_admin):
                flash('Senha incorreta!', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario = session_db.query(Usuario).filter_by(id=user_id).first()
            if usuario == None:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('usuarios.usuarios_lista'))

            usuario.senha = generate_password_hash('1234')
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