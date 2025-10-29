from flask import Blueprint, flash, render_template, request, redirect, url_for, session
from sqlalchemy.exc import IntegrityError, DataError
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.database.db import get_session
from app.empenho.models import Ata, Empenho, ItemAta, ItemEmpenho
from app.estoque.models import Marca
from app.models import Fornecedor, Produto, NotaFiscal, ItemNF
from app.utils import login_required, role_required

atas_bp = Blueprint('atas', __name__, template_folder='templates')

@atas_bp.route('/atas')
@login_required
@role_required('admin', 'nutricionista', 'financeiro', 'diretoria')
def listar_atas():

    try:
        fornecedor_id = int(request.values.get('fornecedor_select'))
    except (ValueError, TypeError):
        fornecedor_id = None
    tipo = request.values.get('tipo_select')
    ano = request.values.get('ano_input')

    try:
        with get_session() as session_db:
            query = session_db.query(Ata).order_by(Ata.ano).order_by(Ata.numero)

            if fornecedor_id and fornecedor_id != 1:
                query = query.filter_by(fornecedor_id=fornecedor_id).order_by(Ata.numero)
                fornecedor = session_db.query(Fornecedor).filter_by(id=fornecedor_id).first()
            else:
                fornecedor = session_db.query(Fornecedor).filter_by(id=1).first()
            if tipo:
                query = query.filter_by(tipo=tipo).order_by(Ata.numero)
            if ano:
                query = query.filter_by(ano=ano).order_by(Ata.numero)
            else:
                ano = str(datetime.today().date().year)
            
            atas = query.all()
            fornecedores = {fornecedor.id: fornecedor for fornecedor in session_db.query(Fornecedor).all()}

    except:
        flash('Erro ao listar atas!', 'danger')
        return redirect('/')


    return render_template('empenho/atas.html', atas=atas, fornecedores=fornecedores, fornecedor=fornecedor, tipo=tipo, ano=ano)


@atas_bp.route('/cadastro/ata', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def cadastro_ata():
    try:
        numero = int(request.form.get('numero', 0))
        ano = int(request.form.get('ano', 0))
        fornecedor_id = int(request.form.get('fornecedor_id', None))
        tipo = request.form.get('tipo')
        status = 'ativo' # Status padrão
    except (TypeError, ValueError):
        flash('Dados inválidos. Por favor, verifique os campos e tente novamente.', 'danger')
        return redirect(url_for('atas.listar_atas'))

    nova_ata = Ata(numero=numero, ano=ano, fornecedor_id=fornecedor_id, tipo=tipo, status=status)
    if not validar_dados(nova_ata):
        flash('Dados inválidos. Por favor, verifique os campos e tente novamente.', 'danger')
        return redirect(url_for('atas.listar_atas'))

    try:
        with get_session() as session_db:
            session_db.add(nova_ata)
            session_db.flush()
            ata_id = nova_ata.id
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if e.orig.args[0] == 1452:
            flash('Fornecedor inexistente!', 'danger')
        elif 'uix_numero_ano' in msg:
            flash(f'Não é possivel cadastrar ata com número: {numero} para o {ano}!', 'danger')
    except DataError as e:
        if e.orig.args[0] == 1265:
            flash('Tipo ou Status inválidos!', 'danger')
    except:
        flash(f'Erro ao cadastrar ata', 'danger')
    else:
        flash(f'Ata cadastrada com sucesso!', 'success')

    return redirect(url_for('atas.ata_info', ata_id=ata_id))

@atas_bp.route('/editar/ata/<int:ata_id>', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def editar_ata(ata_id):    
    try:
        with get_session() as session_db:
            ata = session_db.query(Ata).filter_by(id=ata_id).first()
            if not ata:
                flash('Ata não encontrada', 'danger')
                return redirect(url_for('atas.listar_atas'))
            
            ata.numero = int(request.form.get('edit_numero'))
            ata.ano = int(request.form.get('edit_ano'))
            ata.fornecedor_id = int(request.form.get('edit_fornecedor_id'))
            ata.tipo = request.form.get('edit_tipo')
            ata.status = request.form.get('edit_status')

            if not validar_dados(ata):
                raise Exception('Dados inválidos. Por favor, verifique os campos e tente novamente.')
            
            empenhos = session_db.query(Empenho).filter_by(ata_id=ata_id).all()
            for empenho in empenhos:
                empenho.fornecedor_id = ata.fornecedor_id

                nfs = session_db.query(NotaFiscal).filter_by(empenho_id=empenho.id)
                for nf in nfs:
                    nf.fornecedor_id = ata.fornecedor_id
                    
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if e.orig.args[0] == 1452:
            flash('Fornecedor inexistente!', 'danger')
        elif 'uix_numero_ano' in msg:
            flash(f'O número inserido já existe para o ano!', 'danger')
    except DataError as e:
        if e.orig.args[0] == 1265:
            flash('Tipo ou Status inválidos!', 'danger')
    except:
        flash(f'Falha ao editar ata', 'danger')
    else:
        flash(f'Ata editada com sucesso!', 'success')

    return redirect(url_for('atas.listar_atas'))


@atas_bp.route('/atas/<int:ata_id>')
@login_required
@role_required('admin', 'nutricionista', 'financeiro', 'diretoria')
def ata_info(ata_id):
    try:
        with get_session() as session_db:
            ata = session_db.query(Ata).filter_by(id=ata_id).first()
            if not ata:
                return redirect(url_for('atas.listar_atas'))
            
            itens = session_db.query(ItemAta).filter_by(ata_id=ata_id).order_by(ItemAta.produto_id).all()
            for item in itens:
                item.quantidade_empenhada = 0
            empenhos = session_db.query(Empenho).filter_by(ata_id=ata_id).order_by(Empenho.numero).all()
            fornecedor = session_db.query(Fornecedor).filter_by(id=ata.fornecedor_id).first()
            produtos = {p.id: p for p in session_db.query(Produto).all()}
            marcas = {m.id: m for m in session_db.query(Marca).order_by(Marca.nome).all()}

            empenho_itens = {}
            for empenho in empenhos:
                itens_empenho = session_db.query(ItemEmpenho).filter_by(empenho_id=empenho.id).all()
                for it_empenho in itens_empenho:
                    for it in itens:
                        if it.id == it_empenho.item_ata_id:
                            it.quantidade_empenhada += it_empenho.quantidade_empenhada

                empenho_itens[empenho.id] = itens_empenho
    except:
        flash('Não foi possivel recuperar a ata!', 'danger')
        return redirect(url_for('atas.listar_atas'))
    
    total = 0
    total_restante = 0
    for item in itens:
        item.total = (item.valor_unitario * item.quantidade_maxima).quantize(Decimal('0.01'))
        total += item.total

        item.saldo = item.quantidade_maxima - item.quantidade_empenhada
        item.valor_restante = (item.valor_unitario * item.saldo).quantize(Decimal('0.01'))
        total_restante += item.valor_restante    

    return render_template('empenho/ata.html', ata=ata, itens=itens, produtos=produtos, fornecedor=fornecedor, total=total, empenhos=empenhos, empenho_itens=empenho_itens, total_restante=total_restante, marcas=marcas)

@atas_bp.route('/cadastro/item-ata/<int:ata_id>', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def cadastro_item_ata(ata_id):
    try:
        produto_id = int(request.form.get('produto_id'))
        marca_id = int(request.form.get('marca_id'))
        qntd_maxima = int(request.form.get('quantidade_maxima', 0))
        valor_unit = request.form.get('valor_unitario').strip()
        valor_unit = valor_unit.replace('.', '')
        valor_unit = valor_unit.replace(',', '.')
    except (TypeError, ValueError):
        flash('Insira dados válidos!', 'danger')
        return redirect(url_for('atas.listar_atas'))

    try:
        valor_unit = Decimal(valor_unit)
    except InvalidOperation:
        flash('Valor unitário invalido!', 'danger')
        return redirect(url_for('atas.ata_info', ata_id=ata_id))
    
    novo_item = ItemAta(ata_id=ata_id, produto_id=produto_id, quantidade_maxima=qntd_maxima, marca_id=marca_id, valor_unitario=valor_unit)

    try:
        with get_session() as session_db:
            ata = session_db.query(Ata).filter_by(id=ata_id).first()
            if not ata:
                flash('Ata não encontrada', 'danger')
                return redirect(url_for('atas.listar_atas'))
            
            itens = session_db.query(ItemAta).filter_by(ata_id=ata_id).all()
            if any(produto_id == item.produto_id for item in itens):
                flash('Produto já cadastrado na ata', 'danger')
                return redirect(url_for('atas.ata_info', ata_id=ata_id))
            
            session_db.add(novo_item)
            session_db.flush()
            empenhos = session_db.query(Empenho).filter_by(ata_id=ata_id).all()
            for empenho in empenhos:
                novo_item_empenho = ItemEmpenho(empenho_id=empenho.id, quantidade_empenhada=0, item_ata_id=novo_item.id)
                session_db.add(novo_item_empenho)
                session_db.flush()

                nfs = session_db.query(NotaFiscal).filter_by(empenho_id=empenho.id).all()
                for nf in nfs:
                    novo_item_nf = ItemNF(nota_fiscal_id=nf.id, quantidade=0, item_empenho_id=novo_item_empenho.id)
                    session_db.add(novo_item_nf)

    except:
        flash('Falha ao cadastrar item!', 'danger')
    else:
        flash('Item cadastrado com sucesso!', 'success')
    
    return redirect(url_for('atas.ata_info', ata_id=ata_id))

@atas_bp.route('/editar/item-ata/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def editar_item_ata(item_id):
    ata_id = None
    try:
        with get_session() as session_db:
            item = session_db.query(ItemAta).filter_by(id=item_id).first()
            if not item:
                flash('Item da ata não encontrado', 'danger')
                return redirect(url_for('atas.listar_atas'))
            ata_id = item.ata_id

            try:
                qntd_maxima = int(request.form.get('edit_quantidade_maxima', 0))
                marca_id = int(request.form.get('edit_marca_id'))
                valor_unit = request.form.get('edit_valor_unitario').strip()
                valor_unit = valor_unit.replace('.', '')
                valor_unit = valor_unit.replace(',', '.')
            except (ValueError, TypeError):
                flash('Insira dados válidos!', 'danger')

            try:
                valor_unit = Decimal(valor_unit)
            except InvalidOperation:
                flash('Valor unitário inválido!', 'danger')
                return redirect(url_for('atas.ata_info', ata_id=item.ata_id))

            item.quantidade_maxima = qntd_maxima
            item.valor_unitario = valor_unit
            item.marca_id = marca_id
    except:
        flash('Falha ao editar item!', 'danger')
    else:
        flash('Item da ata editado com sucesso!', 'success')

    if ata_id:
        return redirect(url_for('atas.ata_info', ata_id=ata_id))
    return redirect(url_for('atas.listar_atas'))


@atas_bp.route('/excluir/item-ata/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin', 'nutricionista', 'financeiro')
def excluir_item_ata(item_id):
    try:
        with get_session() as session_db:
            item = session_db.query(ItemAta).filter_by(id=item_id).first()
            if not item:
                flash('Item da ata não encontrado', 'danger')
                return redirect(url_for('atas.listar_atas'))

            ata_id = item.ata_id
            
            session_db.delete(item)

            empenhos = session_db.query(Empenho).filter_by(ata_id=item.ata_id).all()
            for empenho in empenhos:
                item_emp = session_db.query(ItemEmpenho).filter_by(empenho_id=empenho.id).filter_by(produto_id=item.produto_id).first()
                session_db.delete(item_emp)

                notas_fiscais = session_db.query(NotaFiscal).filter_by(empenho_id=empenho.id).all()
                for nota in notas_fiscais:
                    item_nf = session_db.query(ItemNF).filter_by(nota_fiscal_id=nota.id).filter_by(produto_id=item.produto_id).first()
                    session_db.delete(item_nf)
    except:
        flash('Falha ao deletar item da ata', 'danger')
    else:
        flash('Item deletado com sucesso', 'success')
    
    return redirect(url_for('atas.ata_info', ata_id=ata_id))


def validar_dados(ata: Ata):
    if not ata.numero or not ata.ano or not ata.fornecedor_id or not ata.status or not ata.tipo:
        return False
    
    if ata.numero < 0 or ata.ano < 0:
        return False

    return True