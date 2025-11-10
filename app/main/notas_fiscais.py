from flask import Blueprint, request, session, render_template, redirect, flash, url_for
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime

from app.utils import login_required, role_required
from app.models import *
from app.empenho.models import Empenho, ItemEmpenho, Ata, ItemAta
from app.database.db import get_session
from app.database.utils import call_procedure

notas_fiscais_bp = Blueprint('notas_fiscais', __name__, template_folder='templates')

@notas_fiscais_bp.route('/notas/')
@login_required
def notas_lista():
    page = request.args.get('page', default=1, type=int)
    p_page = 10
    offset = (page - 1) * p_page

    numero = session.pop('numero', None)
    fornecedor_id = session.pop('fornecedor_id', None)
    empenho_id = session.pop('empenho_id', None)

    try:
        with get_session() as session_db:
            query = session_db.query(NotaFiscal).order_by(NotaFiscal.empenho_id)
            if numero:
                query = query.filter_by(numero=numero)
            else:
                numero = 0

            if fornecedor_id and fornecedor_id != 1:
                query = query.filter_by(fornecedor_id=fornecedor_id)
                fornecedor = session_db.query(Fornecedor).filter_by(id=fornecedor_id).first()
            else:
                fornecedor = session_db.query(Fornecedor).filter_by(id=1).first()

            if empenho_id and empenho_id != 1:
                query = query.filter_by(empenho_id=empenho_id)
                empenho = session_db.query(Empenho).filter_by(id=empenho_id).first()
            else:
                empenho = session_db.query(Empenho).filter_by(id=1).first()

            total = query.count()
            notas = query.offset(offset).limit(p_page).all()

            for nota in notas:
                rows = call_procedure(session_db, 'SP_GetNFValor', [nota.id])
                for row in rows:
                    if row.get('nota_id') == nota.id:
                        nota.valor = row.get('total', 0)

            empenhos = {e.id: e for e in session_db.query(Empenho).order_by(Empenho.ano).order_by(Empenho.numero).all()}
            fornecedores = {f.id: f for f in session_db.query(Fornecedor).order_by(Fornecedor.nome).all()}
            atas = {a.id: a for a in session_db.query(Ata).all()}
            
            total_pages = (total + p_page - 1) // p_page
    except Exception as e:
        flash('Erro ao recuperar notas fiscais', 'danger')
        print(e)
        return redirect('/')

    return render_template('main/notas_fiscais.html', notas=notas, fornecedores=fornecedores, empenhos=empenhos, atas=atas, page=page, total_pages=total_pages, fornecedor=fornecedor, empenho=empenho, numero=numero)

@notas_fiscais_bp.route('/form/notas-lista', methods=['POST'])
@login_required
def form_notas_lista():
    numero = request.form.get('numero_search', '')
    fornecedor_id = request.form.get('fornecedor_select')
    empenho_id = request.form.get('empenho_select')
    page = request.form.get('page', default=1, type=int)

    if fornecedor_id == None or empenho_id == None or numero == None:
        flash('Informe valores válidos', 'danger')
        return redirect(url_for('main.atas_menu'))
    
    try:
        if fornecedor_id != '':
            f_id = int(fornecedor_id)
        else:
            f_id = 1
        if empenho_id != '':
            e_id = int(empenho_id)
        else:
            e_id = 1
        if numero != '':
            n = int(numero)
        else:
            n = 0
    except:
        flash('Informe valores válidos', 'danger')
        return redirect(url_for('main.atas_menu'))
    
    session['fornecedor_id'] = int(f_id)
    session['empenho_id'] = int(e_id)
    session['numero'] = int(n)
    return redirect(url_for('notas_fiscais.notas_lista', page=page))
        

@notas_fiscais_bp.route('/cadastro/nota/', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def cadastro_nota():
    try:
        numero = int(request.form.get('numero', 0))
        data_emissao = request.form.get('data_emissao', '').strip()
        fornecedor_id = int(request.form.get('fornecedor_id', 0))
        empenho_id = int(request.form.get('empenho_id', 0))
        origem = request.form.get('origem', '').strip()
        serie = int(request.form.get('serie', 0))
        status = request.form.get('status', '').strip()
        observacao = request.form.get('observacao', '').strip()
    except (ValueError, TypeError):
        flash('Valores invalidos', 'danger')
        return redirect(url_for('notas_fiscais.notas_lista'))

    nova_nota = NotaFiscal(numero=numero, data_emissao=data_emissao, fornecedor_id=fornecedor_id, empenho_id=empenho_id, serie=serie, status=status, observacao=observacao)

    if not validar_dados_nota(nova_nota):
        flash('Insira dados válidos para a nota fiscal', 'danger')
        if origem == 'empenho':
            return redirect(url_for('empenhos.empenho_info', empenho_id=empenho_id))

        return redirect(url_for('notas_fiscais.notas_lista'))

    try:
        with get_session() as session_db:
            empenho = session_db.query(Empenho).filter_by(id=empenho_id).first()
            if not empenho:
                flash('Empenho inexistente!', 'danger')
                return redirect(url_for('notas_fiscais.notas_lista'))
            
            session_db.add(nova_nota)
            session_db.flush()
            nf_id = nova_nota.id

            itens_empenho = session_db.query(ItemEmpenho).filter_by(empenho_id=empenho_id).all()
            for item in itens_empenho:
                item_nf = ItemNF(nota_fiscal_id=nova_nota.id, quantidade=0, item_empenho_id=item.id)
                session_db.add(item_nf)
    except IntegrityError as e:
        msg = str(e.orig)
        if 'uix_numero_fornecedor_id_serie' in msg:
            flash('Nota fiscal ja cadastrada para esse fornecedor!', 'danger')
        else:
            flash('Erro de integridade ao cadastrar a nota', 'danger')
        return redirect(url_for('notas_fiscais.notas_lista'))
    except:
        flash(f'Erro ao cadastrar nota fiscal!', 'danger')
        return redirect(url_for('notas_fiscais.notas_lista'))
    else:
        flash('Nota fiscal cadastrada com sucesso!', 'success')

    if origem == 'empenho':
        return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id, origem='empenho'))
    return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id))
    

@notas_fiscais_bp.route('/editar/nota/<int:nota_id>/', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def editar_nota(nota_id):
    origem = request.values.get('origem')
    empenho_id = None
    try:
        numero = int(request.form.get('edit_numero', 0))
        data_emissao = request.form.get('edit_data_emissao', 0).strip()
        serie = int(request.form.get('edit_serie', 0))
        status = request.form.get('edit_status', '').strip()
        observacao = request.form.get('edit_observacao', '').strip()
    except (TypeError, ValueError) as e:
        flash('Insira valores válidos', 'danger')
        return redirect(url_for('notas_fiscais.notas_lista'))
    
    try:
        with get_session() as session_db:
            nota = session_db.query(NotaFiscal).filter_by(id=nota_id).first()
            if not nota:
                flash('Nota fiscal não encontrada', 'danger')
                return redirect(url_for('notas_fiscais.notas_lista'))

            nota.numero = numero
            nota.data_emissao = data_emissao
            nota.serie = serie
            nota.status = status
            nota.observacao = observacao

            empenho_id = nota.empenho_id

            if not validar_dados_nota(nota):
                raise Exception('Insira dados válidos')
    except IntegrityError as e:
        msg = str(e.orig)
        if 'uix_numero_fornecedor_id_serie' in msg:
            flash('Nota fiscal já existente para esse fornecedor!', 'danger')
        else:
            flash('Erro de integridade ao editar a nota', 'danger')
    except:
        flash(f'Erro ao atualizar nota fiscal!', 'danger')
    else:
        flash('Nota fiscal atualizada com sucesso!', 'success')
        if origem == 'empenho' and empenho_id:
            return redirect(url_for('empenhos.empenho_info', empenho_id=empenho_id))

    return redirect(url_for('notas_fiscais.notas_lista'))

@notas_fiscais_bp.route('/notas/<int:nota_id>')
@login_required
def nota_info(nota_id):
    origem = request.args.get('origem')

    try:
        with get_session() as session_db:
            nota_fiscal = session_db.query(NotaFiscal).filter_by(id=nota_id).first()
            if not nota_fiscal:
                flash('Nota fiscal não encontrada', 'danger')
                return redirect(url_for('notas_fiscais.notas_lista'))

            empenho = session_db.query(Empenho).filter_by(id=nota_fiscal.empenho_id).first()
            if not empenho:
                flash('Não foi possivel recuperar o empenho referente a nota')
                return redirect(url_for('notas_fiscais.notas_lista'))
            itens_empenho = {i.id: i for i in session_db.query(ItemEmpenho).filter_by(empenho_id=empenho.id).all()}
            itens_ata = {i.id: i for i in session_db.query(ItemAta).filter_by(ata_id=empenho.ata_id).all()}

            ata = session_db.query(Ata).filter_by(id=empenho.ata_id).first()
            if not ata:
                flash('Não foi possivel recuperar a ata referente a nota')
                return redirect(url_for('notas_fiscais.notas_lista'))

            itens = session_db.query(ItemNF).filter_by(nota_fiscal_id=nota_id).all()
            for item in itens:
                item.disponivel = False
                item_emp = itens_empenho.get(item.item_empenho_id)
                if item_emp:
                    item_ata = itens_ata.get(item_emp.item_ata_id)
                    if item_ata:
                        item.valor_unitario = item_ata.valor_unitario
                        item.produto_id = item_ata.produto_id
                    
                    if item_emp.quantidade_empenhada > 0:
                        item.disponivel = True

            fornecedor = session_db.query(Fornecedor).filter_by(id=nota_fiscal.fornecedor_id).first()
            produtos = {p.id: p for p in session_db.query(Produto).all()}
    except:
        flash('Falha ao recuperar nota fiscal', 'danger')
        return redirect(url_for('notas_fiscais.notas_lista'))
    
    total = 0
    for item in itens:
        item.total = (item.valor_unitario * item.quantidade).quantize(Decimal('0.01'))
        total += item.total
    
    return render_template('main/nota_fiscal.html', nota_fiscal=nota_fiscal, itens=itens, total=total, fornecedor=fornecedor, produtos=produtos, origem=origem, empenho=empenho, ata=ata)


@notas_fiscais_bp.route('/editar/item-nf/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def editar_item_nf(item_id):
    try:
        with get_session() as session_db:
            item = session_db.query(ItemNF).filter_by(id=item_id).first()
            if not item:
                flash('Item não encontrado', 'danger')
                return redirect(url_for('atas.listar_atas'))
            nf_id = item.nota_fiscal_id
            
            qntd = request.form.get('edit_quantidade')
            try:
                qntd = int(qntd)
            except (TypeError, ValueError):
                flash('Valor invalido!', 'danger')
                return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id))
            if qntd < 0:
                flash('Insira um valor positivo', 'danger')
                return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id))
            
            nota_fiscal = session_db.query(NotaFiscal).filter_by(id=nf_id).first()
            if not verificar_saldo_empenho(session_db, nota_fiscal.empenho_id, item.item_empenho_id, qntd, nf_id):
                flash('Esse valor ultrapassa a quantidade empenhada', 'danger')
                return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id))

            item.quantidade = qntd

    except:
        flash('Falha ao editar item!', 'danger')
    else:
        flash('Item editado com sucesso!', 'success')

    return redirect(url_for('notas_fiscais.nota_info', nota_id=nf_id, origem='empenho'))

def validar_dados_nota(nota: NotaFiscal):
    if not nota.numero or not nota.data_emissao or not nota.fornecedor_id:
        return False
    
    if nota.numero <= 0 or nota.serie <= 0:
        return False
    
    try:
        if isinstance(nota.data_emissao, str):
            datetime.strptime(nota.data_emissao, '%Y-%m-%d')
        elif not isinstance(nota.data_emissao, date):
            return False
    except ValueError:
        return False

    return True

def verificar_saldo_empenho(session_db: Session, empenho_id: int, item_id: int, quantidade, nf_id):
    empenho = session_db.query(Empenho).filter_by(id=empenho_id).first()
    if not empenho:
        return False
    
    item_empenho = session_db.query(ItemEmpenho).filter_by(id=item_id).first()
    
    total = quantidade
    notas = session_db.query(NotaFiscal).filter_by(empenho_id=empenho_id).all()
    for nota in notas:
        if nota.id == nf_id:
            continue
        item_ = session_db.query(ItemNF).filter_by(nota_fiscal_id=nota.id).filter_by(item_empenho_id=item_id).first()
        total += item_.quantidade
    
    if total > item_empenho.quantidade_empenhada:
        return False
    return True
