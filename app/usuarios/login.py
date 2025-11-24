from flask import session, render_template, request, redirect, flash, url_for, current_app
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash


from app.models import RoleUser, Role
from app.usuarios.models import Usuario
from app.utils import login_required
from app.database.db import get_session
from app.database.utils import check_login

from . import usuarios_bp


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3000):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except:
        return None
    

@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')
    if request.method == 'GET':
        return render_template('usuarios/login.html')
    elif request.method != 'POST':
        return redirect('/')
    
    email = request.form.get('email')
    senha = request.form.get('password')

    with get_session() as session_db:
        cod, user = check_login(email, senha, session_db)
        if cod == 1:
            flash('Usuário inexistente!', 'danger')
            return redirect('/login')
        elif cod == 2:
            flash('Senha incorreta!', 'danger')
            return redirect('/login')
        elif cod == 0:
            if user.status == 'inativo':
                flash('Não foi possivel completar seu login', 'danger')
                return redirect('/login')
            session['user_id'] = user.id
            session['nome'] = user.nome

            roles = []
            roles_user = session_db.query(RoleUser).filter_by(usuario_id=user.id).all()
            for role_user in roles_user:
                if role_user.ativado:
                    role = session_db.query(Role).filter_by(id=role_user.role_id).first()
                    if role:
                        roles.append(role.nome)

            session['roles'] = roles.copy()
            flash('Usuário logado com sucesso!', 'success')

    return redirect(url_for('main.index'))

@usuarios_bp.route('/logout')
@login_required
def logout():
    session.clear()

    return redirect(url_for('usuarios.login'))


@usuarios_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    if not email:
        flash('Insira um email!', 'danger')
        return redirect(url_for('usuarios.login'))
    
    mail = Mail(current_app)
    try:
        with get_session() as session_db:
            user = session_db.query(Usuario).filter_by(email=email).first()
            if not user:
                flash('Email não encontrado, verifique e tente novamente!', 'danger')

        token = generate_reset_token(email)
        reset_link = url_for('usuarios.reset_password', token=token, _external=True)

        print(current_app.config['MAIL_PASSWORD'])
        msg = Message('Alteração de senha', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
        print(msg.sender)
        msg.body = f'Você está recebendo está mensagem pois foi feito um pedido para alterar a senha da sua conta.\n\nSe não foi você que fez o pedido, ignore essa mensagem.\n\nLink para alteração: {reset_link}'
        mail.send(msg)

        flash('O link para a alteração de sua senha foi mandado, cheque seu email', 'success')
    except Exception as e:
        flash('Erro ao enviar email! Tente novamente', 'danger')
        print(e)

    return redirect(url_for('usuarios.login'))


@usuarios_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Token invalido ou expirado!', 'danger')
        return redirect(url_for('usuarios.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('As senhas devem ser identicas', 'danger')
            return redirect(url_for('usuarios.reset_password', token=token))

        hash_password = generate_password_hash(new_password)

        try:
            with get_session() as session_db:
                user = session_db.query(Usuario).filter_by(email=email).first()
                if not user:
                    flash('Email não encontrado, verifique e tente novamente!', 'danger')
                
                user.senha = hash_password
                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('usuarios.login'))
        except Exception as e:
            flash('Erro ao alterar senha!', 'danger')
            print(e)
    return render_template('usuarios/reset_password.html', token=token)


