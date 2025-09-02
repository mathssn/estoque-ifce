from database.models import *
from sqlalchemy import event
from werkzeug.security import generate_password_hash
import datetime as dt

produtos = [    
    {"codigo": 1, "nome": "Açucar", "descricao": "Tipo cristal", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 2, "nome": "Achocolatado em pó", "descricao": "---", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 3, "nome": "Adoçante", "descricao": "---", "unidade": "tb", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 4, "nome": "Alimento a base de farinha e aveia", "descricao": "Preparo de mingau", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 5, "nome": "Ameixa em calda", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 6, "nome": "Amido de milho", "descricao": "Embalagem com 1kg", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 7, "nome": "Aromatizante artificial", "descricao": "Sabor baunilha; frasco com 30ml", "unidade": "fr", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 8, "nome": "Arroz parboilizado integral", "descricao": "Classe longo fino tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 9, "nome": "Arroz parboilizado polido", "descricao": "Classe longo fino tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 10, "nome": "Azeite de oliva puro extra virgem", "descricao": "Acidez menor que 1; Embalagem com 500ml", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 11, "nome": "Azeitona verde", "descricao": "Sem caroço", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 12, "nome": "Azeitona preta", "descricao": "Sem caroço", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 13, "nome": "Biscoito recheado sabor chocolate", "descricao": "Tipo waffer; Embalagem com 30g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 14, "nome": "Biscoito recheado sabor morango", "descricao": "Tipo waffer; Embalagem com 30g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 15, "nome": "Bolacha Cream Cracker", "descricao": "Embalagem entre 350g a 400g; Contém 3 pacotes de bolacha", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 16, "nome": "Bolacha Maisena", "descricao": "Embalagem entre 350g a 400g; Contém 3 pacotes de bolacha", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 17, "nome": "Bolacha Maisena sem lactose", "descricao": "Pacotes com peso entre 100 a 150g; ou 200g a 300g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 18, "nome": "Café torrado e moído", "descricao": "Pacote com 250g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 19, "nome": "Coco ralado", "descricao": "Sem adição de açucar; Pacote com 1kg", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 20, "nome": "Colorau(Colorífico)", "descricao": "Embalagem com 100g de produto", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 21, "nome": "Cravo da Índia", "descricao": "Embalagem com 50g de produto", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 22, "nome": "Creme de leite - 200g", "descricao": "Embalagem com 200g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 23, "nome": "Creme de leite - 1000g", "descricao": "Embalagem com 1000g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 24, "nome": "Doce tipo cocada de leite condensado", "descricao": "Peso aproximado individual de 20g; Pote com 50 unidades, peso de 1000g", "unidade": "pote", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 25, "nome": "Doce tipo mariola; Sabor banana", "descricao": "Pote com 20 unidades, peso de 300g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 26, "nome": "Doce tipo mariola; Sabor goiaba", "descricao": "Pote com 20 unidades, peso de 300g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 27, "nome": "Ervilha", "descricao": "Pacote com 170g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 28, "nome": "Extrato de tomate", "descricao": "Embalagem com 1.7kg", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 29, "nome": "Farinha Láctea", "descricao": "Peso entre 200g e 250g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 30, "nome": "Farinha de mandioca", "descricao": "Tipo fina e peneirada", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 31, "nome": "Farinha de milho flocada", "descricao": "Pacote com 400g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 32, "nome": "Farinha de trigo com fermento", "descricao": "---", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 33, "nome": "Farinha de trigo sem fermento", "descricao": "---", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 34, "nome": "Feijão branco", "descricao": "Tipo 1, Classe branco, grupo I, grão de cor branca uniforme", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 35, "nome": "Feijão carioquinha", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 36, "nome": "Feijão de corda", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 37, "nome": "Feijão preto", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 38, "nome": "Fermento em pó", "descricao": "Pote com 100g", "unidade": "pt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 39, "nome": "Grão-de-bico", "descricao": "Pacote com 500g de produto", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 40, "nome": "Leite condensado", "descricao": "Embalagem com 395g", "unidade": "cx", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 41, "nome": "Leite de coco tradicional", "descricao": "Garrafa com 500ml", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 42, "nome": "Leite de soja em pó", "descricao": "Lata com 300g", "unidade": "lt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 43, "nome": "Leite em pó desnatado", "descricao": "Embalagem com 300g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 44, "nome": "Leite em pó integral", "descricao": "Embalagem com 200g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 45, "nome": "Macarrão para lasanha", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 46, "nome": "Macarrão tipo argola", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 47, "nome": "Macarrão tipo espaguete", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 48, "nome": "Macarrão tipo parafuso", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 49, "nome": "Macarrão tipo penne", "descricao": "A base de farinha; Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 50, "nome": "Margarina vegetal", "descricao": "Balde com 15kg", "unidade": "bd", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 51, "nome": "Milho p/ Mucunzá", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 52, "nome": "Milho p/ Pipoca", "descricao": "---", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 53, "nome": "Milho verde", "descricao": "Pacote com 170g", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 54, "nome": "Molho inglês", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 55, "nome": "Molho Shoyu", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 56, "nome": "Óleo vegetal", "descricao": "Garrafa com 900ml", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 57, "nome": "Pó para preparo de gelatina Sabor abacaxi", "descricao": "Embalagem com 1kg de produto", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 58, "nome": "Pó para preparo de gelatina Sabor cereja", "descricao": "Embalagem com 1kg de produto", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 59, "nome": "Proteína texturizada de soja", "descricao": "Pacotes com 1kg ou 400g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 60, "nome": "Rapadura", "descricao": "Em tijolinhos de 20 a 25g; Pacote com 1kg", "unidade": "un", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 61, "nome": "Sal", "descricao": "Refinado e iodado", "unidade": "kg", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 62, "nome": "Sardinha", "descricao": "Lata contendo 125g liquido e 80g a 85g drenado", "unidade": "lt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 63, "nome": "Suco concentrado de maracujá integral", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 64, "nome": "Suco concentrado de uva integral", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 65, "nome": "Suplemento nutricional a base de leite; Sabor banana", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 66, "nome": "Suplemento nutricional a base de leite; Sabor baunilha", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 67, "nome": "Tempero pronto tipo caseiro", "descricao": "Garrafa com 500ml de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"},
    {"codigo": 68, "nome": "Vinagre", "descricao": "Garrafa com 500ml de produto", "unidade": "gf", "quantidade_minima": 30, "status": "ativo"}
]   


@event.listens_for(Usuario.__table__, "after_create")
def insert_usuario(target, connection, **kw):
    senha_hash = generate_password_hash("1234")
    connection.execute(
        Usuario.__table__.insert(),
        ({"nome": "Matheus Soares", "email": "matheus.soares10@aluno.ifce.edu.br", "senha": senha_hash, "data_nascimento": "2004-10-02", "nivel_acesso": "Superusuario"})
    )
@event.listens_for(DiasFechados.__table__, "after_create")
def insert_dias_fechados(target, connection, **kw):
    date = dt.date.today()
    connection.execute(
        DiasFechados.__table__.insert(),
        ({"data": date, "fechado": False})
    )

@event.listens_for(Produto.__table__, "after_create")
def insert_produtos(target, connection, **kw):
    for produto in produtos:
        connection.execute(
            Produto.__table__.insert(),
            {"codigo": produto["codigo"], "nome": produto["nome"], "descricao": produto["descricao"], "unidade": produto["unidade"], "quantidade_minima": produto["quantidade_minima"], "status": produto["status"]}
        )


@event.listens_for(SaldoDiario.__table__, "after_create")
def insert_saldos_diarios(target, connection, **kw):
    date = dt.date.today()

    for produto in produtos:
        connection.execute(
            SaldoDiario.__table__.insert(),
            {"data": date, "produto_id": produto["codigo"], "quantidade_inicial": 0, "quantidade_entrada": 0, "quantidade_saida": 0, "quantidade_final": 0}
        )


@event.listens_for(Destino.__table__, "after_create")
def insert_destinos(target, connection, **kw):
    destinos = ['Café da manhã', 'Lanche da manhã', 'Almoço', 'Lanche da tarde', 'Jantar', 'Ceia', 'Outros']
    for destino in destinos:
        connection.execute(
            Destino.__table__.insert(),
            {"nome": destino}
        )

@event.listens_for(Fornecedor.__table__, "after_create")
def insert_fornecedor(target, connection, **kw):
    connection.execute(
        Fornecedor.__table__.insert(),
        {"nome": "-", "email": "-", "telefone": "-"}
    )


@event.listens_for(Marca.__table__, "after_create")
def insert_marca(target, connection, **kw):
    connection.execute(
        Marca.__table__.insert(),
        {"nome": "-"}
    )


@event.listens_for(NotaFiscal.__table__, "after_create")
def insert_nota_fiscal(target, connection, **kw):
    date = dt.date.today()

    connection.execute(
        NotaFiscal.__table__.insert(),
        {"numero": "-", "data_emissao": date, "valor": 0, "fornecedor_id": 1}
    )
