from flask import render_template, flash, redirect, url_for, request, session
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.utils import login_required
from app.database.db import get_session
from app.refeicao_contagem.models import RegistroRefeicao
from app.models import Refeicao

from . import registro_refeicao_bp


@registro_refeicao_bp.route('/registro-refeicao', methods=['POST', 'GET'])
@login_required
def registro_refeicao():

    data = request.form.get('data')
    if not data:
        data = date.today().isoformat()

    refeicoes_cadastradas = []
    total_dia = 0
    qntd_p_publico = {'aluno': 0, 'servidor': 0, 'terceirizado': 0, 'outros': 0}
    try:
        with get_session() as session_db:
            registros = session_db.query(RegistroRefeicao).filter_by(data=data).order_by(RegistroRefeicao.refeicao_id.asc()).all()

            # Calcula o total da refeição
            for registro in registros:
                registro.total = registro.qntd_aluno + registro.qntd_servidores + registro.qntd_terceirizados + registro.qntd_outros
                total_dia += registro.total

                # Calcula o total por publico
                qntd_p_publico['aluno'] += registro.qntd_aluno
                qntd_p_publico['servidor'] += registro.qntd_servidores
                qntd_p_publico['terceirizado'] += registro.qntd_terceirizados
                qntd_p_publico['outros'] += registro.qntd_outros

                refeicoes_cadastradas.append(
                    session_db.query(Refeicao).filter_by(id=registro.refeicao_id).first()
                )

            refeicoes = session_db.query(Refeicao).all()
    except:
        flash(f'Erro ao recuperar os registros da refeição', 'danger')
        return redirect('/')
    
    data = datetime.strptime(data, '%Y-%m-%d').date()
    return render_template('refeicao_contagem/refeicao_contagem.html', registros=registros, data=data, refeicoes_cadastradas=refeicoes_cadastradas, refeicoes=refeicoes, total_dia=total_dia, qntd_p_publico=qntd_p_publico)


@registro_refeicao_bp.route('/cadastro/registro-refeicao/', methods=['POST'])
@login_required
def cadastro_registro_refeicao():
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('/'))

    try:
        refeicao_id = int(request.form.get('refeicao_id', 0))
        qntd_aluno = int(request.form.get('qntd_alunos', 0))
        qntd_servidores = int(request.form.get('qntd_servidores', 0))
        qntd_terceirizados = int(request.form.get('qntd_terceirizados', 0))
        qntd_outros = int(request.form.get('qntd_outros', 0))
        data = request.form.get('data', '').strip()
    except (TypeError, ValueError):
        flash('Dados invalidos!', 'danger')
        return redirect(url_for('refeicoes.refeicoes_lista'))

    nova_refeicao = RegistroRefeicao(
        refeicao_id=refeicao_id,
        qntd_aluno=qntd_aluno,
        qntd_servidores=qntd_servidores,
        qntd_terceirizados=qntd_terceirizados,
        qntd_outros=qntd_outros,
        data=data
    )

    if not validar_dados_refeicao(nova_refeicao):
        flash('Insira dados válidos para o registro da refeição.', 'danger')
        return redirect(url_for('registro_refeicao.registro_refeicao', data=data))

    try:
        with get_session() as session_db:
            session_db.add(nova_refeicao)
    except:
        flash(f'Falha ao cadastrar registro', 'danger')
    else:
        flash('Registro de refeição cadastrado com sucesso!', 'success')

    return redirect(url_for('registro_refeicao.registro_refeicao', data=data))

@registro_refeicao_bp.route('/editar/registro-refeicao/<int:registro_id>', methods=['POST'])
@login_required
def editar_registro_refeicao(registro_id):
    if session.get('nivel_acesso') not in ['Superusuario', 'Admin', 'Editor']:
        flash('Permissão negada', 'warning')
        return redirect(url_for('refeicoes.refeicoes_lista'))
    
    try:
        with get_session() as session_db:
            registro = session_db.query(RegistroRefeicao).filter_by(id=registro_id).first()
            if not registro:
                flash('Registro de refeição não encontrado', 'danger')
                return redirect(url_for('refeicoes.refeicoes_lista'))
            
            data = registro.data
            try:
                registro.qntd_aluno = int(request.form.get('edit_qntd_alunos', 0))
                registro.qntd_servidores = int(request.form.get('edit_qntd_servidores', 0))
                registro.qntd_terceirizados = int(request.form.get('edit_qntd_terceirizados', 0))
                registro.qntd_outros = int(request.form.get('edit_qntd_outros', 0))
            except (TypeError, ValueError):
                flash('Dados inválidos!', 'danger')
                return redirect(url_for('refeicoes.refeicoes_lista'))
            
            # Validação customizada
            if not validar_dados_refeicao(registro):
                raise Exception('Dados inválidos. Por favor, verifique os campos e tente novamente.')
            
    except IntegrityError as e:
        msg = str(e.orig).lower()
        if 'uix_refeicao_id_data' in msg:
            flash('Já existe um registro de refeição para esta data e refeição!', 'danger')
        else:
            flash('Erro de integridade no banco de dados!', 'danger')
    except:
        flash('Falha ao editar registro de refeição', 'danger')
    else:
        flash('Registro de refeição editado com sucesso!', 'success')

    return redirect(url_for('registro_refeicao.registro_refeicao', data=data))

@registro_refeicao_bp.route('/registro-refeicao-periodo', methods=['GET', 'POST'])
@login_required
def registro_refeicao_periodo():
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    if not data_inicio or not data_fim:
        data_inicio = date.today().isoformat()
        data_fim = date.today().isoformat()

    refeicoes_cadastradas = []
    total = 0
    refeicoes_dict = {}
    qntd_p_publico = {'aluno': 0, 'servidores': 0, 'terceirizados': 0, 'outros': 0, 'total': 0}

    try:
        with get_session() as session_db:
            registros = (
                session_db.query(RegistroRefeicao)
                .filter(RegistroRefeicao.data.between(data_inicio, data_fim))
                .order_by(RegistroRefeicao.data.asc(), RegistroRefeicao.refeicao_id.asc())
                .all()
            )

            for registro in registros:
                registro.total = (registro.qntd_aluno + registro.qntd_servidores + registro.qntd_terceirizados + registro.qntd_outros)
                total += registro.total

                # Pega refeição vinculada
                refeicao = session_db.query(Refeicao).filter_by(id=registro.refeicao_id).first()
                if refeicao and refeicao not in refeicoes_cadastradas:
                    refeicoes_cadastradas.append(refeicao)

                # Monta dicionário por refeição
                if refeicao:
                    nome_refeicao = refeicao.nome  # ou use refeicao.id se preferir
                    if nome_refeicao not in refeicoes_dict:
                        refeicoes_dict[nome_refeicao] = {
                            "qntd_aluno": 0,
                            "qntd_servidores": 0,
                            "qntd_terceirizados": 0,
                            "qntd_outros": 0,
                            "total": 0
                        }
                    refeicoes_dict[nome_refeicao]["qntd_aluno"] += registro.qntd_aluno
                    refeicoes_dict[nome_refeicao]["qntd_servidores"] += registro.qntd_servidores
                    refeicoes_dict[nome_refeicao]["qntd_terceirizados"] += registro.qntd_terceirizados
                    refeicoes_dict[nome_refeicao]["qntd_outros"] += registro.qntd_outros
                    refeicoes_dict[nome_refeicao]["total"] += registro.qntd_aluno + registro.qntd_servidores + registro.qntd_terceirizados + registro.qntd_outros

                    qntd_p_publico['aluno'] += registro.qntd_aluno
                    qntd_p_publico['servidores'] += registro.qntd_servidores
                    qntd_p_publico['terceirizados'] += registro.qntd_terceirizados
                    qntd_p_publico['outros'] += registro.qntd_outros
                    qntd_p_publico['total'] += registro.qntd_aluno + registro.qntd_servidores + registro.qntd_terceirizados + registro.qntd_outros

            refeicoes = session_db.query(Refeicao).all()

    except:
        flash(f'Erro ao recuperar os registros da refeição', 'danger')
        return redirect('/')
    
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

    return render_template('refeicao_contagem/refeicao_p_periodo.html', registros=registros, data_inicio=data_inicio, data_fim=data_fim, refeicoes_cadastradas=refeicoes_cadastradas, refeicoes=refeicoes, total=total, refeicoes_dict=refeicoes_dict, qntd_p_publico=qntd_p_publico)

def validar_dados_refeicao(refeicao: RegistroRefeicao):
    if refeicao.qntd_aluno < 0 or refeicao.qntd_servidores < 0 or refeicao.qntd_terceirizados < 0 or refeicao.qntd_outros < 0:
        return False
    
    try:
        if isinstance(refeicao.data, str):
            datetime.strptime(refeicao.data, "%Y-%m-%d")
        elif not isinstance(refeicao.data, date):
            return False
    except ValueError:
        return False
    
    return True