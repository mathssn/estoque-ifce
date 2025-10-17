from flask import Blueprint, request, session, render_template, redirect, flash, url_for
from datetime import date, datetime
from sqlalchemy.orm import Session as S

from app.utils import login_required, role_required
from app.database.db import *
from app.database.utils import *
from app.utils import somar_dia
from app.estoque.models import *
from app.models import *
from app.empenho.models import *
from app.usuarios.models import Usuario

estoque_bp = Blueprint('estoque', __name__, template_folder='templates')


@estoque_bp.route('/movimentacoes-diarias', methods=['POST', 'GET'])
@login_required
def movimentacoes_diarias():
    tipo_movimentacao = request.values.get('tipo_movimentacao')
    if not tipo_movimentacao:
        tipo_movimentacao = session.pop('tipo_movimentacao', None)
    if not tipo_movimentacao:
        tipo_movimentacao = 'saida'

    data = request.form.get('date')
    if data == None:
        data = session.pop('date', None)
    if data == None:
        data = date.today().isoformat()

    with get_session() as session_db:
        entradas_diarias = session_db.query(Entrada).filter_by(data_entrada=data).order_by(Entrada.produto_id).all()
        saidas_diarias = session_db.query(Saida).filter_by(data_saida=data).order_by(Saida.refeicao_id).order_by(Saida.produto_id).all()

        produtos_dict, fornecedores_dict, marcas_dict, refeicoes = get_additional_info(session_db)
        saldos_diarios = session_db.query(SaldoDiario).filter_by(data=data).all()
        nfs_1 = session_db.query(
            NotaFiscal
        ).join(
            Empenho, Empenho.id == NotaFiscal.empenho_id
        ).join(
            Ata, Ata.id == Empenho.ata_id
        ).filter(
            Ata.tipo == 'nao_perecivel'
        ).group_by(
            NotaFiscal.id
        ).all()
        nfs_2 = session_db.query(NotaFiscal).filter_by(id=1).all()
        nota_fiscal_dict = {nf.id: nf for nf in nfs_2 + nfs_1}

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
        'estoque/movimentacoes_diarias.html',
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
        refeicoes=refeicoes,
        tipo_movimentacao=tipo_movimentacao
    )

@estoque_bp.route('/fechar/dia/<data>')
@login_required
@role_required('admin', 'nutricionista')
def fechar_dia(data: str):
    cod = verificar_dias_abertos()
    if cod == 1:
        flash('Não há dia aberto', 'danger')
        return
    
    try:
        with get_session() as session_db:
            saldos_ = session_db.query(SaldoDiario).filter_by(data=data).all()

            if not check_saldo(data, session_db):
                return redirect(url_for('estoque.movimentacoes_diarias', date=data))

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
        flash(f'Falha ao fechar dia: {data}', 'danger')
    else:
        try:
            data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            flash(f"Dia {data_formatada} fechado com sucesso", 'success')
        except Exception as e:
            flash(f'Dia {data} fechado com sucesso', 'success')
    
    session['date'] = data
    return redirect(url_for('estoque.movimentacoes_diarias'))




def get_additional_info(session_db: S):
    produtos_dict = {p.id: p for p in session_db.query(Produto).all()}
    fornecedores_dict = {f.id: f for f in session_db.query(Fornecedor).all()}
    marcas_dict = {m.id: m for m in session_db.query(Marca).order_by(Marca.nome).all()}
    refeicoes = {d.id: d for d in session_db.query(Refeicao).all()}

    return produtos_dict, fornecedores_dict, marcas_dict, refeicoes



@estoque_bp.route('/movimentacao/<int:produto_id>/')
@login_required
def movimentacao_por_produto(produto_id):
    page = request.args.get('page', default=1, type=int)
    p_page = 20
    offset = (page - 1) * p_page
    movimentacoes: list[dict] = []
    logs_saidas = {}
    logs_entradas = {}
    total = 0
    
    try:
        movimentacoes, total = list_movementation_by_product(produto_id, p_page, offset)
        with get_session() as session_db:
            produto = session_db.query(Produto).filter_by(id=produto_id).first()
            refeicoes = {d.id: d for d in session_db.query(Refeicao).all()}
            usuarios = {u.id: u for u in session_db.query(Usuario).all()}
            
            for movimentacao in movimentacoes:
                log = session_db.query(Log).filter_by(operacao_id=movimentacao.get('id')).filter_by(tipo_operacao_2='inserção').filter_by(tipo_operacao=movimentacao.get('tipo')).first()
                if log:
                    if movimentacao.get('tipo') == 'saida':
                        logs_saidas[movimentacao['id']] = log
                    elif movimentacao.get('tipo') == 'entrada':
                        logs_entradas[movimentacao['id']] = log

    except Exception as e:
        flash(f'{e}', 'danger')
        return redirect('/')
    
    if produto == None:
        flash('Produto não encontrado', 'danger')
        return redirect('/')
    
    produto.nome = produto.nome.replace('\n', ' ')
    total_pages = (total + p_page - 1) // p_page

    return render_template('estoque/movimentacao_por_produto.html', movimentacoes=movimentacoes, produto=produto, refeicoes=refeicoes, page=page, total_pages=total_pages, usuarios=usuarios, logs_saidas=logs_saidas, logs_entradas=logs_entradas)


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
        flash(f'Não foi possivel verificar os dias: {e}', 'danger')
        return 3
    
    return 0
