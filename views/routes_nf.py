from flask import Blueprint, request, session, render_template, redirect, flash, url_for

from utils.utils import login_required
from database.models import *
from database.db import get_session

notas_fiscais_bp = Blueprint('notas_fiscais', __name__)

@notas_fiscais_bp.route('/notas/')
@login_required
def notas_lista():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect('/')

    with get_session() as session_db:
        notas = session_db.query(NotaFiscal).all()
        fornecedores = {f.id: f for f in session_db.query(Fornecedor).all()}

    return render_template('notas_fiscais.html', notas=notas, fornecedores=fornecedores)

@notas_fiscais_bp.route('/cadastro/nota/', methods=['POST'])
@login_required
def cadastro_nota():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('notas_fiscais.notas_lista'))

    numero = request.form.get('numero')
    data_emissao = request.form.get('data_emissao')
    valor = request.form.get('valor')
    fornecedor_id = request.form.get('fornecedor_id')

    try:
        valor = float(valor) if valor else None
        fornecedor_id = int(fornecedor_id)
    except ValueError:
        flash('Valor ou Fornecedor inválido')
        return redirect(url_for('notas_fiscais.notas_lista'))

    nova_nota = NotaFiscal(numero=numero, data_emissao=data_emissao, valor=valor, fornecedor_id=fornecedor_id)

    if not validar_dados_nota(nova_nota):
        flash('Insira dados válidos para a nota fiscal')
        return redirect(url_for('notas_fiscais.notas_lista'))

    try:
        with get_session() as session_db:
            session_db.add(nova_nota)
    except Exception as e:
        flash(f'Erro ao cadastrar nota fiscal: {e}')
    else:
        flash('Nota fiscal cadastrada com sucesso!')

    return redirect(url_for('notas_fiscais.notas_lista'))

@notas_fiscais_bp.route('/editar/nota/<int:nota_id>/', methods=['POST'])
@login_required
def editar_nota(nota_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin']:
        flash('Permissão negada')
        return redirect(url_for('notas_fiscais.notas_lista'))

    try:
        with get_session() as session_db:
            nota = session_db.query(NotaFiscal).filter_by(id=nota_id).first()
            if not nota:
                flash('Nota fiscal não encontrada')
                return redirect(url_for('notas_fiscais.notas_lista'))

            nota.numero = request.form.get('edit_numero')
            nota.data_emissao = request.form.get('edit_data_emissao')
            valor = request.form.get('edit_valor')
            nota.valor = float(valor) if valor else None
            nota.fornecedor_id = int(request.form.get('edit_fornecedor_id'))

            if not validar_dados_nota(nota):
                flash('Insira dados válidos')
                return redirect(url_for('notas_fiscais.notas_lista'))
            
    except Exception as e:
        flash(f'Erro ao atualizar nota fiscal: {e}')
    else:
        flash('Nota fiscal atualizada com sucesso!')

    return redirect(url_for('notas_fiscais.notas_lista'))

def validar_dados_nota(nota: NotaFiscal):
    if not nota.numero or not nota.data_emissao or nota.fornecedor_id <= 0:
        return False

    if nota.valor is not None and nota.valor < 0:
        return False

    return True
