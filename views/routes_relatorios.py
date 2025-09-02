from flask import Blueprint, request, render_template
from datetime import datetime
import matplotlib.pyplot as plt
import base64
import io
from sqlalchemy import extract

from utils.utils import login_required
from database.models import *
from database.db import get_session

relatorios_bp = Blueprint('relatorios', __name__)

meses = {
    '1': 'Janeiro',
    '2': 'Fevereiro',
    '3': 'Março',
    '4': 'Abril',
    '5': 'Maio',
    '6': 'Junho',
    '7': 'Julho',
    '8': 'Agosto',
    '9': 'Setembro',
    '10': 'Outubro',
    '11': 'Novembro',
    '12': 'Dezembro'
}


@relatorios_bp.route('/relatorios-lista')
@login_required
def relatorios_lista():
    return render_template('relatorios.html')


@relatorios_bp.route('/relatorio-mensais')
@relatorios_bp.route('/relatorio-mensais/<int:ano>/<int:mes>')
@login_required
def relatorios_mensais(ano=None, mes=None):
    m = request.args.get('mes')
    a = request.args.get('ano')

    if m != None:
        mes = m
    elif mes == None:
        mes = str(datetime.today().date().month)
    if a != None:
        ano = a
    elif ano == None:
        ano = str(datetime.today().date().year)

    saidas_mensais = {}
    entradas_mensais = {}
    
    with get_session() as session_db:
        produtos = session_db.query(Produto).all()
        destinos = session_db.query(Destino).all()

        for p in produtos:
            saidas_mensais[p.id] = {d.id: 0 for d in destinos}
            entradas_mensais[p.id] = 0

        saidas = session_db.query(Saida).filter(
            extract('year', Saida.data_saida) == ano,
            extract('month', Saida.data_saida) == mes
        ).all()
        for s in saidas:
            if s.produto_id not in saidas_mensais.keys():
                continue

            saidas_mensais[s.produto_id][s.destino_id] += s.quantidade
        
        entradas = session_db.query(Entrada).filter(
            extract('year', Entrada.data_entrada) == ano,
            extract('month', Entrada.data_entrada) == mes
        ).all()
        for e in entradas:
            if e.produto_id not in entradas_mensais.keys():
                continue

            entradas_mensais[e.produto_id] += e.quantidade
        

    return render_template('relatorios_mensais.html', saidas_mensais=saidas_mensais, entradas_mensais=entradas_mensais, produtos=produtos, mes=mes, ano=ano, meses=meses, destinos=destinos)


@relatorios_bp.route('/relatorio-produto/')
@login_required
def relatorio_produto():

    produto_id = request.args.get('produto_select')
    if not produto_id:
        produto_id = 1
    else:
        produto_id = int(produto_id)

    saidas_anuais = [0 for n in range(1, 13)]
    year = str(datetime.now().year)
    with get_session() as session_db:
        for m in range(1, 13):
            saidas = session_db.query(Saida).filter(
                extract('year', Saida.data_saida) == year,
                extract('month', Saida.data_saida) == m
            ).all()
            for saida in saidas:
                if saida.produto_id != produto_id:
                    continue

                saidas_anuais[m-1] += saida.quantidade

        produtos = session_db.query(Produto).all()

    plt.figure(dpi=150)
    plt.plot(
        list(map(lambda x: x[0:3], meses.values())),
        saidas_anuais
    )
    plt.ylabel('Quantidade')

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    # Converter para base64
    grafico_base64 = base64.b64encode(img.getvalue()).decode("utf-8")

    return render_template('relatorios_produto.html', produtos=produtos, produto_id=produto_id, grafico=grafico_base64, meses=meses)

