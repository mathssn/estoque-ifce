from flask import session, render_template, request, redirect, flash, url_for
from app.utils import login_required
from app.database.db import get_session
from app.database.utils import check_login

from . import usuarios_bp


@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login():
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
            session['user_id'] = user.id
            session['nome'] = user.nome
            session['nivel_acesso'] = user.nivel_acesso
            flash('Usuário logado com sucesso!', 'success')

    return redirect(url_for('main.index'))

@usuarios_bp.route('/logout')
@login_required
def logout():
    session.clear()

    return redirect(url_for('usuarios.login'))

