from flask import session, request, redirect, flash, url_for, abort
from functools import wraps
from datetime import datetime, timedelta


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'nome' not in session or 'user_id' not in session:
            flash('Você precisa estar logado para acessar essa página', 'warning')
            return redirect(url_for('usuarios.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            roles_user = session.get('roles', [])
            if not any(role in roles_user for role in roles_permitidos):
                flash('Permissão negada', 'warning')
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return wrapper
    return decorator



def somar_dia(data: str, formato: str, quantidade: int = 1) -> str:
    new_date = datetime.strptime(data, formato).date() + timedelta(days=quantidade)
    new_date = new_date.isoformat()
    return new_date


def get_form(fields: dict):
    values = []

    for f_name, f_type in fields.items():
        if f_type == 'int':
            try:
                value = int(request.form.get(f_name, 0))
            except:
                return None
            values.append(value)
        else:
            value = request.form.get(f_name, '').strip()
            values.append(value)
    
    return values