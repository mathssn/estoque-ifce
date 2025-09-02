from flask import session, redirect, flash
from functools import wraps
from datetime import datetime, timedelta


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'nome' not in session or 'user_id' not in session:
            flash('Você precisa estar logado para acessar essa página')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def somar_dia(data: str, formato: str, quantidade: int = 1) -> str:
    new_date = datetime.strptime(data, formato).date() + timedelta(days=quantidade)
    new_date = new_date.isoformat()
    return new_date

