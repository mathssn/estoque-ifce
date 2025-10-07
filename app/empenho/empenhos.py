from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, session
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.utils import login_required
from app.empenho.models import Empenho, Ata, ItemAta, ItemEmpenho
from app.database.base import StatusEnum
from app.models import Produto, Fornecedor, NotaFiscal, ItemNF
from app.database.db import get_session

empenhos_bp = Blueprint('empenhos', __name__, template_folder='templates')

@empenhos_bp.route('/empenhos/')
@login_required
def empenhos_lista():
    page = request.args.get('page', default=1, type=int)
    p_page = 10
    offset = (page - 1) * p_page

    fornecedor_id = session.pop('fornecedor_id', None)
    ano = session.pop('ano', None)

    try:
        with get_session() as session_db:
            query = session_db.query(Empenho).order_by(Empenho.ano).order_by(Empenho.numero)

            # filtro fornecedor
            if fornecedor_id and fornecedor_id != 1:
                query = query.filter(Empenho.fornecedor_id == fornecedor_id)
                fornecedor = session_db.query(Fornecedor).filter_by(id=fornecedor_id).first()
            else:
                fornecedor = session_db.query(Fornecedor).filter_by(id=1).first()

            # filtro ano
            if ano and ano != "0":
                query = query.filter(Empenho.ano == ano)
            else:
                ano = str(datetime.today().date().year)

            total = query.count()
            empenhos = query.offset(offset).limit(p_page).all()

            fornecedores = {f.id: f for f in session_db.query(Fornecedor).order_by(Fornecedor.nome).all()}
            atas = {a.id: a for a in session_db.query(Ata).all()}
            
            total_pages = (total + p_page - 1) // p_page
    except:
        flash('Erro ao recuperar empenhos', 'danger')
        return redirect('/')

    return render_template(
        'empenho/empenhos.html', empenhos=empenhos, fornecedores=fornecedores, atas=atas, page=page, total_pages=total_pages, fornecedor=fornecedor, ano=ano
    )

@empenhos_bp.route('/form/empenhos-lista', methods=['POST'])
@login_required
def form_empenhos_lista():
    fornecedor_id = request.form.get('fornecedor_select')
    ano = request.form.get('ano_input', '')

    if fornecedor_id is None or ano is None:
        flash('Informe valores válidos', 'danger')
        return redirect(url_for('main.atas_menu'))
    
    try:
        if fornecedor_id != '':
            f_id = int(fornecedor_id)
        else:
            f_id = 1
        if ano != '':
            a = int(ano)
        else:
            a = 0
    except:
        flash('Informe valores válidos', 'danger')
        return redirect(url_for('main.atas_menu'))
    
    session['fornecedor_id'] = int(f_id)
    session['ano'] = int(a)
    return redirect(url_for('empenhos.empenhos_lista'))


@empenhos_bp.route('/cadastro/empenho/<int:ata_id>', methods=['POST'])
@login_required
def cadastro_empenho(ata_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('atas.ata_info', ata_id=ata_id))
    
    try:
        numero = int(request.form.get('numero'))
        ano = str(request.form.get('ano'))
        fornecedor_id = int(request.form.get('fornecedor_id'))
        status = StatusEnum.ativo
    except (TypeError, ValueError):
        flash('Dados inválidos. Por favor, verifique os campos e tente novamente.', 'danger')
        return redirect(url_for('atas.ata_info', ata_id=ata_id))

    novo_empenho = Empenho(
        numero=numero,
        ano=ano,
        fornecedor_id=fornecedor_id,
        ata_id=ata_id,
        status=status
    )

    if not validar_dados(novo_empenho):
        flash('Dados inválidos. Por favor, verifique os campos e tente novamente.', 'danger')
        return redirect(url_for('atas.ata_info', ata_id=ata_id))

    try:
        with get_session() as session_db:
            ata = session_db.query(Ata).filter_by(id=ata_id).first()
            if not ata:
                flash('Ata não encontrada', 'danger')
                return redirect(url_for('atas.listar_atas'))
            
            itens_ata = session_db.query(ItemAta).filter_by(ata_id=ata_id).all()
            session_db.add(novo_empenho)
            session_db.flush()
            empenho_id = novo_empenho.id

            for item in itens_ata:
                item_empenho = ItemEmpenho(empenho_id=novo_empenho.id, produto_id=item.produto_id, quantidade_empenhada=0, valor_unitario=item.valor_unitario)
                session_db.add(item_empenho)
    except IntegrityError as e:
        if e.orig.args[0] == 1452:
            pass
    except:
        flash('Erro ao cadastrar empenho', 'danger')
    else:
        flash('Empenho cadastrado com sucesso!', 'success')

    return redirect(url_for('empenhos.empenho_info', empenho_id=empenho_id))

@empenhos_bp.route('/editar/empenho/<int:empenho_id>', methods=['POST'])
@login_required
def editar_empenho(empenho_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('atas.listar_atas'))
    
    try:
        with get_session() as session_db:
            empenho = session_db.query(Empenho).filter_by(id=empenho_id).first()
            if not empenho:
                flash('Empenho não encontrado', 'danger')
                return redirect(url_for('atas.listar_atas'))
            
            # Coleta os dados do formulário
            empenho.numero = int(request.form.get('edit_numero'))
            empenho.ano = str(request.form.get('edit_ano'))
            empenho.status = request.form.get('edit_status')

            # Validação
            if not validar_dados(empenho):
                raise Exception('Dados inválidos. Por favor, verifique os campos e tente novamente.')

    except IntegrityError as e:
        msg = str(e.orig).lower()
        if e.orig.args[0] == 1452:
            flash('Fornecedor inexistente!', 'danger')
        elif 'uix_numero_ano' in msg:
            flash(f'O número inserido já existe para o ano!', 'danger')
    except:
        flash(f'Falha ao editar empenho', 'danger')
    else:
        flash(f'Empenho editado com sucesso!', 'success')

    return redirect(url_for('atas.ata_info', ata_id=empenho.ata_id))


@empenhos_bp.route('/empenho/<int:empenho_id>')
@login_required
def empenho_info(empenho_id):
    with get_session() as session_db:
        empenho = session_db.query(Empenho).filter_by(id=empenho_id).first()
        if not empenho:
            flash('Empenho não encontrado!', 'danger')
            return redirect(url_for('atas.listar_atas'))
        
        ata = session_db.query(Ata).filter_by(id=empenho.ata_id).first()
        if not ata:
            flash('Não foi possivel recuperar a ata referente ao empenho!')
            return redirect(url_for('atas.listar_atas'))
        
        itens = session_db.query(ItemEmpenho).filter_by(empenho_id=empenho_id).order_by(ItemEmpenho.produto_id).all()
        for it in itens:
            it.recebido = 0
            it.saldo = 0

        produtos = {p.id: p for p in session_db.query(Produto).all()}
        fornecedor = session_db.query(Fornecedor).filter_by(id=empenho.fornecedor_id).first()
        notas_fiscais = session_db.query(NotaFiscal).filter_by(empenho_id=empenho_id).filter_by(status='ativo').all()
        notas_itens = {}
        for nota in notas_fiscais:
            if nota.status == 'inativo':
                continue

            itens_nf = session_db.query(ItemNF).filter_by(nota_fiscal_id=nota.id).all()
            for item_nf in itens_nf:
                for it in itens:
                    if it.produto_id != item_nf.produto_id:
                        continue

                    it.recebido += item_nf.quantidade
            notas_itens[nota.id] = itens_nf

    total = 0
    total_restante = 0
    for item in itens:
        item.total = (item.valor_unitario * item.quantidade_empenhada).quantize(Decimal('0.01'))
        total += item.total

        item.saldo = item.quantidade_empenhada - item.recebido
        item.valor_restante = (item.valor_unitario * item.saldo).quantize(Decimal('0.01'))
        total_restante += item.valor_restante
        
    return render_template('empenho/empenho.html', empenho=empenho, itens=itens, produtos=produtos, total=total, fornecedor=fornecedor, notas_fiscais=notas_fiscais, notas_itens=notas_itens, total_restante=total_restante, ata=ata)


@empenhos_bp.route('/editar/item-empenho/<int:item_id>', methods=['POST'])
@login_required
def editar_item_empenho(item_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('atas.listar_atas'))
    
    try:
        with get_session() as session_db:
            item = session_db.query(ItemEmpenho).filter_by(id=item_id).first()
            if not item:
                flash('Item do empenho não encontrado', 'danger')
                return redirect(url_for('atas.listar_atas'))
            empenho_id = item.empenho_id

            qntd_empenhada = request.form.get('edit_quantidade_empenhada')
            try:
                qntd_empenhada = int(qntd_empenhada)
            except (TypeError, ValueError):
                raise Exception('Valor invalido!')
            empenho = session_db.query(Empenho).filter_by(id=item.empenho_id).first()
            if not verificar_saldo_ata(session_db, empenho.ata_id, item.produto_id, qntd_empenhada, empenho.id):
                flash('Esse valor ultrapassa a quantidade maxima da ata', 'danger')
                return redirect(url_for('empenhos.empenho_info', empenho_id=empenho.id))

            item.quantidade_empenhada = qntd_empenhada


    except Exception as e:
        flash(f'Falha ao editar item: {e}', 'danger')
    else:
        flash('Item editado com sucesso!', 'success')

    return redirect(url_for('empenhos.empenho_info', empenho_id=empenho_id))

def validar_dados(empenho: Empenho):
    return True


def verificar_saldo_ata(session_db: Session, ata_id: int, produto_id: int, quantidade, empenho_id):
    ata = session_db.query(Ata).filter_by(id=ata_id).first()
    if not ata:
        return False
    
    item_ata = session_db.query(ItemAta).filter_by(ata_id=ata_id).filter_by(produto_id=produto_id).first()
    
    total = quantidade
    empenhos = session_db.query(Empenho).filter_by(ata_id=ata_id).all()
    for empenho in empenhos:
        if empenho.id == empenho_id:
            continue
        item_ = session_db.query(ItemEmpenho).filter_by(empenho_id=empenho.id).filter_by(produto_id=produto_id).first()
        total += item_.quantidade_empenhada
    
    if total > item_ata.quantidade_maxima:
        return False
    return True