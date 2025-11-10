from flask import Blueprint, session, render_template, redirect, url_for, flash
from datetime import date, datetime
from decimal import Decimal

from app.utils import login_required
from app.database.db import get_session
from app.estoque.models import DiasFechados, SaldoDiario
from app.models import Produto

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    if 'user_id' not in session.keys():
        return redirect(url_for('usuarios.login'))

    return render_template('main/index.html')

@main_bp.route('/sobre')
@login_required
def sobre():
    return render_template('main/sobre.html')

@main_bp.route('/estoque-menu')
@login_required
def estoque_menu():
    try:
        with get_session() as session_db:
            dia = session_db.query(DiasFechados).filter_by(fechado=False).first()
            if dia:
                produtos = session_db.query(Produto).filter_by(tipo='nao_perecivel').all()
                saldos = {s.produto_id: s for s in session_db.query(SaldoDiario).filter_by(data=dia.data).all()}
    except Exception as e:
        flash('Erro ao recuperar dia aberto!', 'danger')
        return render_template('main/index.html')
    
    produtos_zerados = []
    baixo_estoque = []
    for p in produtos:
        saldo = saldos.get(p.id)
        if not saldo or p.status == 'inativo':
            continue

        if saldo.quantidade_final == 0:
            produtos_zerados.append(p)
        elif saldo.quantidade_final < p.quantidade_minima:
            p.quantidade = saldo.quantidade_final
            baixo_estoque.append(p)
    
    return render_template('main/estoque.html', dia=dia, produtos_zerados=produtos_zerados, baixo_estoque=baixo_estoque)


@main_bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('erros/404.html'), 404


@main_bp.app_errorhandler(500)
def page_not_found(error):
    return render_template('erros/500.html'), 500

@main_bp.route('/atas-menu')
@login_required
def atas_menu():
    return render_template('main/atas.html')

@main_bp.route('/registro-refeicao-menu')
@login_required
def registro_refeicao_menu():
    return render_template('main/registro_refeicao.html')


@main_bp.app_template_filter('format_date')
def format_date(value, formato='%d/%m/%Y'):
    if isinstance(value, date):
        return value.strftime(formato)
    return value


@main_bp.app_template_filter('format_money')
def format_money(value: Decimal, rs=True):
    if isinstance(value, Decimal):
        if rs:
            return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return value

@main_bp.app_template_filter('capitalize')
def capitalize(value: str):
    try:
        string = value.capitalize()
        return string
    except Exception as e:
        print(e)
        return value
    
@main_bp.app_template_filter('replace')
def replace(value: str, old: str, new: str):
    try:
        string = value.replace(old, new)
        return string
    except:
        return value
    
@main_bp.app_template_filter('format_empenho')
def format_empenho(value: int, ano: int):
    try:
        if not ano:
            ano = str(datetime.now().year)
        
        qntd_zeros = 6 - len(str(value))
        if qntd_zeros < 0:
            return f'{ano}NE{value}'
        
        string = str(ano) + 'NE'
        for i in range(qntd_zeros):
            string += '0'
        
        string += str(value)
        return string
    except:
        return f'{ano}NE{value}'
    
@main_bp.app_template_filter('check_intersection')
def check_intersection(iteravel_1, iteravel_2):
    try:
        if any(i1 == i2 for i1 in iteravel_1 for i2 in iteravel_2):
            return True
    except:
        pass
    return False

def register_filters(app):
    app.add_template_filter(format_date, 'format_date')
    app.add_template_filter(format_money, 'format_money')
    app.add_template_filter(format_empenho, 'format_empenho')
    app.add_template_filter(capitalize, 'capitalize')
    app.add_template_filter(replace, 'replace')
    app.add_template_filter(check_intersection, 'check_intersection')
