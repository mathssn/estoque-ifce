from flask import Blueprint, request, render_template, flash
from datetime import datetime
import matplotlib.pyplot as plt
import base64
import io
from sqlalchemy import extract, func

from app.utils import login_required
from app.models import *
from app.estoque.models import *
from app.database.db import get_session

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
    return render_template('estoque/relatorios.html')


@relatorios_bp.route('/relatorio-periodo', methods=['POST', 'GET'])
@login_required
def relatorios_periodo():

    # Pega as datas dos parâmetros GET
    data_inicio_str = request.form.get("data_inicio")
    data_fim_str = request.form.get("data_fim")

    hoje = datetime.today().date()

    # Se não vier nada, usa o dia atual
    if not data_inicio_str or not data_fim_str:
        data_inicio = hoje
        data_fim = hoje
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            # fallback se vier formato errado
            data_inicio = hoje
            data_fim = hoje

    saidas_periodo = {}
    entradas_periodo = {}

    with get_session() as session_db:
        produtos = session_db.query(Produto).filter_by(tipo='nao_perecivel').all()
        refeicoes = session_db.query(Refeicao).all()

        for p in produtos:
            saidas_periodo[p.id] = {d.id: 0 for d in refeicoes}
            entradas_periodo[p.id] = 0

        # Saídas no intervalo
        saidas = (
            session_db.query(Saida)
            .filter(Saida.data_saida >= data_inicio, Saida.data_saida <= data_fim)
            .all()
        )
        for s in saidas:
            if s.produto_id not in saidas_periodo:
                continue
            saidas_periodo[s.produto_id][s.refeicao_id] += s.quantidade

        # Entradas no intervalo
        entradas = (
            session_db.query(Entrada)
            .filter(Entrada.data_entrada >= data_inicio, Entrada.data_entrada <= data_fim)
            .all()
        )
        for e in entradas:
            if e.produto_id not in entradas_periodo:
                continue
            entradas_periodo[e.produto_id] += e.quantidade

    return render_template(
        "estoque/relatorios_periodo.html",
        saidas_mensais=saidas_periodo,
        entradas_mensais=entradas_periodo,
        produtos=produtos,
        refeicoes=refeicoes,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@relatorios_bp.route('/relatorio-produto', methods=['POST', 'GET'])
@login_required
def relatorio_produto():

    produto_id = request.form.get('produto_select')
    if not produto_id:
        produto_id = 1
    else:
        try:
            produto_id = int(produto_id)
        except (ValueError, TypeError):
            flash('Produto inválido', 'danger')
            produto_id = 1

    saidas_anuais = [0 for n in range(1, 13)]
    year = str(datetime.now().year)
    with get_session() as session_db:
        # Consumo anual
        saidas_anuais_query = (
            session_db.query(
                extract('month', Saida.data_saida).label('mes'),
                func.sum(Saida.quantidade).label('total')
            )
            .filter(
                extract('year', Saida.data_saida) == year,
                Saida.produto_id == produto_id
            )
            .group_by('mes')
            .order_by('mes')
            .all()
        )

        # Criar vetor de 12 meses preenchendo com 0 onde não há dados
        saidas_anuais = [0] * 12
        for row in saidas_anuais_query:
            mes_idx = int(row.mes) - 1
            saidas_anuais[mes_idx] = int(row.total or 0)

        produtos = session_db.query(Produto).all()

        # Consumo por refeição
        consumo_p_refeicao = session_db.query(
            Refeicao.nome,
            func.avg(Saida.quantidade).label("media_quantidade")
        ).join(
            Refeicao, Refeicao.id == Saida.refeicao_id
        ).filter(
            Saida.produto_id == produto_id
        ).group_by(
            Refeicao.nome
        ).all()

        consumo_p_refeicao = {nome: media for nome, media in consumo_p_refeicao}

        refeicoes = session_db.query(Refeicao).all()
        categorias = []
        valores = []
        for refeicao in refeicoes:
            categorias.append(refeicao.nome.replace(' ', '\n'))
            v = consumo_p_refeicao.get(refeicao.nome, None)
            if not v:
                valores.append(0)
            elif v:
                valores.append(int(v))

    plt.figure(dpi=150)
    plt.plot(
        list(map(lambda x: x[0:3], meses.values())),
        saidas_anuais
    )
    plt.ylabel('Quantidade')

    img1 = io.BytesIO()
    plt.savefig(img1, format="png")
    img1.seek(0)

    plt.figure(dpi=150)
    plt.bar(categorias, valores)
    plt.ylabel('Média')

    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)

    plt.close()

    # Converter para base64
    grafico_base64_1 = base64.b64encode(img1.getvalue()).decode("utf-8")
    grafico_base64_2 = base64.b64encode(img2.getvalue()).decode('utf-8')

    return render_template('estoque/relatorios_produto.html', produtos=produtos, produto_id=produto_id, grafico_1=grafico_base64_1, grafico_2=grafico_base64_2, meses=meses)

