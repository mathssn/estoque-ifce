from flask import Flask, render_template, request, redirect, flash, url_for, session
from dotenv import load_dotenv
from datetime import date, datetime
import os
from sqlalchemy.orm import Session as S

from utils.utils import login_required, somar_dia
from database.models import *
from database.db import *
from database.insert import *

from database.utils import *

from views.routes_produto import produtos_bp
from views.routes_saida import saidas_bp
from views.routes_entradas import entradas_bp
from views.routes_user import usuarios_bp
from views.routes_relatorios import relatorios_bp
from views.routes_fornecedores import fornecedores_bp
from views.routes_marca import marcas_bp
from views.routes_nf import notas_fiscais_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.register_blueprint(produtos_bp)
app.register_blueprint(saidas_bp)
app.register_blueprint(entradas_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(fornecedores_bp)
app.register_blueprint(marcas_bp)
app.register_blueprint(notas_fiscais_bp)

@app.route('/')
def index():
    if 'user_id' not in session.keys():
        return redirect('/login')
    
    with get_session() as session_db:
        dia = session_db.query(DiasFechados).filter_by(fechado=False).first()

    return render_template('index.html', dia=dia)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method != 'POST':
        return redirect('/')
    
    email = request.form.get('email')
    senha = request.form.get('password')

    with get_session() as session_db:
        cod, user = check_login(email, senha, session_db)
        if cod == 1:
            flash('Usuário inexistente!')
            return redirect('/')
        elif cod == 2:
            flash('Senha incorreta!')
            return redirect('/')
        elif cod == 0:
            session['user_id'] = user.id
            session['nome'] = user.nome
            session['nivel_acesso'] = user.nivel_acesso
            flash('Usuário logado com sucesso!')

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()

    return redirect('/login')

@app.route('/movimentacoes-diarias/')
@app.route('/movimentacoes-diarias/<data>')
@login_required
def movimentacoes_diarias(data=None):
    d = request.args.get('date')
    tipo_movimentacao = request.args.get('tipo')

    if not tipo_movimentacao:
        tipo_movimentacao = 'saida'

    if d != None:
        data = d
    elif data == None:
        data = date.today().isoformat()

    with get_session() as session_db:
        entradas_diarias = session_db.query(Entrada).filter_by(data_entrada=data).order_by(Entrada.produto_id).all()
        saidas_diarias = session_db.query(Saida).filter_by(data_saida=data).order_by(Saida.destino_id).order_by(Saida.produto_id).all()

        produtos_dict, fornecedores_dict, marcas_dict, nota_fiscal_dict, destinos = get_additional_info(session_db)
        saldos_diarios = session_db.query(SaldoDiario).filter_by(data=data).all()

        dia = session_db.query(DiasFechados).filter_by(data=data).first()

        movs = entradas_diarias.copy()
        movs.extend(saidas_diarias.copy())

        usuarios = {}
        for mov in movs:
            if mov.usuario_id not in usuarios.keys():
                usuario = session_db.query(Usuario).filter_by(id=mov.usuario_id).first()
                if usuario:
                    usuarios[usuario.id] = usuario.nome
                else:
                    usuarios[mov.usuario_id] = 'Desconhecido'
    

    return render_template(
        'movimentacoes_diarias.html',
        saidas=saidas_diarias,
        data=data,
        produtos=produtos_dict,
        entradas=entradas_diarias,
        saldos_diarios=saldos_diarios,
        dia=dia,
        usuarios=usuarios,
        fornecedores=fornecedores_dict,
        marcas=marcas_dict,
        notas_fiscais=nota_fiscal_dict,
        destinos=destinos,
        tipo_movimentacao=tipo_movimentacao
    )

@app.route('/fechar/dia/<data>')
@login_required
def fechar_dia(data: str):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada')
        return redirect(url_for('movimentacoes_diarias'))

    cod = verificar_dias_abertos()
    if cod == 1:
        flash('Não há dia aberto')
        return
    
    try:
        with get_session() as session_db:
            saldos_ = session_db.query(SaldoDiario).filter_by(data=data).all()

            if not check_saldo(data, session_db):
                return redirect(url_for('movimentacoes_diarias', data=data))

            dia = session_db.query(DiasFechados).filter_by(data=data).first()
            dia.fechado = True

            # Soma 1 dia a data
            new_date = somar_dia(data, '%Y-%m-%d')

            dia = DiasFechados(data=new_date, fechado=False)
            session_db.add(dia)

            for saldo in saldos_:
                new_saldo = SaldoDiario(produto_id=saldo.produto_id, data=new_date, quantidade_inicial=saldo.quantidade_final, quantidade_entrada=0, quantidade_saida=0, quantidade_final=saldo.quantidade_final)
                session_db.add(new_saldo)
    except Exception as e:
        flash(f'Falha ao fechar dia: {data}')
        print(e)
    else:
        try:
            data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            flash(f"Dia {data_formatada} fechado com sucesso")
        except Exception as e:
            flash(f'Dia {data} fechado com sucesso')
        
    return redirect(url_for('movimentacoes_diarias', data=data))

@app.template_filter('format_date')
def format_date(value, formato='%d/%m/%Y'):
    if isinstance(value, date):
        return value.strftime(formato)
    return value

def verificar_dias_abertos() -> int:
    try:
        with get_session() as session_db:
            dias_ = session_db.query(DiasFechados).filter_by(fechado=False).all()

            if len(dias_) == 0:
                mais_recente = session_db.query(DiasFechados).filter_by(fechado=True).order_by(DiasFechados.data.desc()).first()
                if mais_recente == None:
                        return 1
            
            elif len(dias_) > 1:
                for dia in dias_[:-1]:
                    dia.fechado = True
                return 2
    except Exception as e:
        flash(f'Não foi possivel verificar os dias: {e}')
        return 3
    
    return 0


def get_additional_info(session_db: S):
    produtos_dict = {p.id: p for p in session_db.query(Produto).all()}
    fornecedores_dict = {f.id: f for f in session_db.query(Fornecedor).all()}
    marcas_dict = {m.id: m for m in session_db.query(Marca).order_by(Marca.nome).all()}
    nota_fiscal_dict = {nf.id: nf for nf in session_db.query(NotaFiscal).all()}
    destinos = {d.id: d for d in session_db.query(Destino).all()}

    return produtos_dict, fornecedores_dict, marcas_dict, nota_fiscal_dict, destinos



if __name__ == '__main__':
    Base.metadata.create_all(bind=db)
    app.run(debug=True)