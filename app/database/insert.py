from app.estoque.models import *
from app.usuarios.models import Usuario
from app.models import *
from app.empenho.models import *
from sqlalchemy import event
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os
import datetime as dt

produtos = [    
    {"codigo": 1, "nome": "Açucar", "descricao": "Tipo cristal", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 2, "nome": "Achocolatado em pó", "descricao": "---", "unidade": "un", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 3, "nome": "Adoçante", "descricao": "---", "unidade": "tb", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 4, "nome": "Alimento a base de farinha e aveia", "descricao": "Preparo de mingau", "unidade": "un", "quantidade_minima": 15, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 5, "nome": "Ameixa em calda", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 6, "nome": "Amido de milho", "descricao": "Embalagem com 1kg", "unidade": "kg", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 7, "nome": "Aromatizante artificial", "descricao": "Sabor baunilha; frasco com 30ml", "unidade": "fr", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 8, "nome": "Arroz parboilizado integral", "descricao": "Classe longo fino tipo 1", "unidade": "kg", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 9, "nome": "Arroz parboilizado polido", "descricao": "Classe longo fino tipo 1", "unidade": "kg", "quantidade_minima": 40, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 10, "nome": "Azeite de oliva puro extra virgem", "descricao": "Acidez menor que 1; Embalagem com 500ml", "unidade": "un", "quantidade_minima": 3, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 11, "nome": "Azeitona verde", "descricao": "Sem caroço", "unidade": "un", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 12, "nome": "Azeitona preta", "descricao": "Sem caroço", "unidade": "un", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 13, "nome": "Biscoito recheado sabor chocolate", "descricao": "Tipo waffer; Embalagem com 30g", "unidade": "un", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 14, "nome": "Biscoito recheado sabor morango", "descricao": "Tipo waffer; Embalagem com 30g", "unidade": "un", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 15, "nome": "Bolacha Cream Cracker", "descricao": "Embalagem entre 350g a 400g; Contém 3 pacotes de bolacha", "unidade": "pct", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 16, "nome": "Bolacha Maisena", "descricao": "Embalagem entre 350g a 400g; Contém 3 pacotes de bolacha", "unidade": "pct", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 17, "nome": "Bolacha Maisena sem lactose", "descricao": "Pacotes com peso entre 100 a 150g; ou 200g a 300g", "unidade": "pct", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 18, "nome": "Café torrado e moído", "descricao": "Pacote com 250g", "unidade": "pct", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 19, "nome": "Coco ralado", "descricao": "Sem adição de açucar; Pacote com 1kg", "unidade": "kg", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 20, "nome": "Colorau(Colorífico)", "descricao": "Embalagem com 100g de produto", "unidade": "kg", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 21, "nome": "Cravo da Índia", "descricao": "Embalagem com 50g de produto", "unidade": "un", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 22, "nome": "Creme de leite - 200g", "descricao": "Embalagem com 200g", "unidade": "un", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 23, "nome": "Creme de leite - 1000g", "descricao": "Embalagem com 1000g", "unidade": "un", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 24, "nome": "Doce tipo cocada de leite condensado", "descricao": "Peso aproximado individual de 20g; Pote com 50 unidades, peso de 1000g", "unidade": "pote", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 25, "nome": "Doce tipo mariola; Sabor banana", "descricao": "Pote com 20 unidades, peso de 300g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 26, "nome": "Doce tipo mariola; Sabor goiaba", "descricao": "Pote com 20 unidades, peso de 300g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 27, "nome": "Ervilha", "descricao": "Pacote com 170g", "unidade": "un", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 28, "nome": "Extrato de tomate", "descricao": "Embalagem com 1.7kg", "unidade": "un", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 29, "nome": "Farinha Láctea", "descricao": "Peso entre 200g e 250g", "unidade": "un", "quantidade_minima": 15, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 30, "nome": "Farinha de mandioca", "descricao": "Tipo fina e peneirada", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 31, "nome": "Farinha de milho flocada", "descricao": "Pacote com 400g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 32, "nome": "Farinha de trigo com fermento", "descricao": "---", "unidade": "kg", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 33, "nome": "Farinha de trigo sem fermento", "descricao": "---", "unidade": "kg", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 34, "nome": "Feijão branco", "descricao": "Tipo 1, Classe branco; grupo I, grão de cor branca uniforme", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 35, "nome": "Feijão carioquinha", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 36, "nome": "Feijão de corda", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 37, "nome": "Feijão preto", "descricao": "Tipo 1", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 38, "nome": "Fermento em pó", "descricao": "Pote com 100g", "unidade": "pt", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 39, "nome": "Grão-de-bico", "descricao": "Pacote com 500g de produto", "unidade": "pct", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 40, "nome": "Leite condensado", "descricao": "Embalagem com 395g", "unidade": "cx", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 41, "nome": "Leite de coco tradicional", "descricao": "Garrafa com 500ml", "unidade": "gf", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 42, "nome": "Leite de soja em pó", "descricao": "Lata com 300g", "unidade": "lt", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 43, "nome": "Leite em pó desnatado", "descricao": "Embalagem com 300g", "unidade": "un", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 44, "nome": "Leite em pó integral", "descricao": "Embalagem com 200g", "unidade": "un", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 45, "nome": "Macarrão para lasanha", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 46, "nome": "Macarrão tipo argola", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 47, "nome": "Macarrão tipo espaguete", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 40, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 48, "nome": "Macarrão tipo parafuso", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 49, "nome": "Macarrão tipo penne", "descricao": "A base de farinha; Pacote com 500g", "unidade": "pct", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 50, "nome": "Margarina vegetal", "descricao": "Balde com 15kg", "unidade": "bd", "quantidade_minima": 2, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 51, "nome": "Milho p/ Mucunzá", "descricao": "Pacote com 500g", "unidade": "pct", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 52, "nome": "Milho p/ Pipoca", "descricao": "---", "unidade": "pct", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 53, "nome": "Milho verde", "descricao": "Pacote com 170g", "unidade": "un", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 54, "nome": "Molho inglês", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 3, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 55, "nome": "Molho Shoyu", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 3, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 56, "nome": "Óleo vegetal", "descricao": "Garrafa com 900ml", "unidade": "gf", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 57, "nome": "Pó para preparo de gelatina Sabor abacaxi", "descricao": "Embalagem com 1kg de produto", "unidade": "kg", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 58, "nome": "Pó para preparo de gelatina Sabor cereja", "descricao": "Embalagem com 1kg de produto", "unidade": "kg", "quantidade_minima": 1, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 59, "nome": "Proteína texturizada de soja", "descricao": "Pacotes com 1kg ou 400g", "unidade": "pct", "quantidade_minima": 15, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 60, "nome": "Rapadura", "descricao": "Em tijolinhos de 20 a 25g; Pacote com 1kg", "unidade": "un", "quantidade_minima": 20, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 61, "nome": "Sal", "descricao": "Refinado e iodado", "unidade": "kg", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 62, "nome": "Sardinha", "descricao": "Lata contendo 125g liquido; e 80g a 85g drenado", "unidade": "lt", "quantidade_minima": 30, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 63, "nome": "Suco concentrado de maracujá integral", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 64, "nome": "Suco concentrado de uva integral", "descricao": "Garrafa com 1 litro de produto", "unidade": "gf", "quantidade_minima": 10, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 65, "nome": "Suplemento nutricional a base de leite; Sabor banana", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 66, "nome": "Suplemento nutricional a base de leite; Sabor baunilha", "descricao": "Lata com 400g", "unidade": "lt", "quantidade_minima": 5, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 67, "nome": "Tempero pronto tipo caseiro", "descricao": "Garrafa com 500ml de produto", "unidade": "gf", "quantidade_minima": 15, "status": "ativo", 'tipo': 'nao_perecivel'},
    {"codigo": 68, "nome": "Vinagre", "descricao": "Garrafa com 500ml de produto", "unidade": "gf", "quantidade_minima": 20, "status": "ativo", "tipo": "nao_perecivel"}
]   

pereciveis = [
    {"codigo": 1, "nome": "Abacate", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 2, "nome": "Abacaxi", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 3, "nome": "Banana-prata", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 4, "nome": "Laranja", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 5, "nome": "Limão galego", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 6, "nome": "Maçã", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 7, "nome": "Mamão formosa", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 8, "nome": "Manga Tommy", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 9, "nome": "Maracujá", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 10, "nome": "Melancia", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 11, "nome": "Melão espanhol", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 12, "nome": "Melão japonês", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 13, "nome": "Milho verde", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 14, "nome": "Pequi (sem casca)", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 15, "nome": "Polpa de fruta sabor abacaxi", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 16, "nome": "Polpa de fruta sabor acerola", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 17, "nome": "Polpa de fruta sabor cajá", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 18, "nome": "Polpa de fruta sabor caju", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 19, "nome": "Polpa de fruta sabor goiaba", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 20, "nome": "Polpa de fruta sabor manga", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 21, "nome": "Polpa de fruta sabor tamarindo", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 22, "nome": "Abóbora", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 23, "nome": "Abobrinha italiana", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 24, "nome": "Alface", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 25, "nome": "Alho solto n° 05", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 26, "nome": "Batata-doce", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 27, "nome": "Batata-inglesa", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 28, "nome": "Beterraba", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 29, "nome": "Brócolis", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 30, "nome": "Cebola branca", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 31, "nome": "Cebola roxa", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 32, "nome": "Cebolinha", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 33, "nome": "Cenoura", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 34, "nome": "Chuchu", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 35, "nome": "Coentro verde", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 36, "nome": "Couve manteiga", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 37, "nome": "Macaxeira", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 38, "nome": "Maxixe", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 39, "nome": "Pepino", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 40, "nome": "Pimenta-de-cheiro", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 41, "nome": "Pimentão verde", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 42, "nome": "Quiabo", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 43, "nome": "Repolho verde", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 44, "nome": "Tomate", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 45, "nome": "Vagem", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 46, "nome": "Amendoim cru", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 47, "nome": "Alecrim", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 48, "nome": "Camomila", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 49, "nome": "Canela em casca", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 50, "nome": "Canela em pó", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 51, "nome": "Erva-doce", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 52, "nome": "Feijão-verde", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 53, "nome": "Massa de puba", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 54, "nome": "Uvas passas brancas sem sementes", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 55, "nome": "Uvas passas pretas sem sementes", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 56, "nome": "Bacon", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 57, "nome": "Bucho bovino", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 58, "nome": "Carne bovina sem osso: acém", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 59, "nome": "Carne bovina sem osso: alcatra em bifes", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 60, "nome": "Carne bovina sem osso: coxão mole", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 61, "nome": "Carne bovina moída (patinho)", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 62, "nome": "Carne de charque", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 63, "nome": "Carne de frango: coxa e sobrecoxa", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 64, "nome": "Carne de frango: filé de peito", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 65, "nome": "Carne de sol", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 66, "nome": "Carne suína: bisteca", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 67, "nome": "Carne suína: lombo suíno", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 68, "nome": "Carne suína: pernil suíno", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 69, "nome": "Fígado bovino", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 70, "nome": "Iogurte parcialmente desnatado com morango", "descricao": "", "unidade": "bandeja", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 71, "nome": "Leite de vaca integral", "descricao": "", "unidade": "l", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 72, "nome": "Linguiça calabresa", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 73, "nome": "Linguiça mista", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 74, "nome": "Ovos de galinha", "descricao": "", "unidade": "bandeja", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 75, "nome": "Peixe filé (polaca do Alasca)", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 76, "nome": "Peixe tilápia", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 77, "nome": "Presunto de peru", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 78, "nome": "Queijo coalho", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 79, "nome": "Queijo mussarela", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 80, "nome": "Tempero desidratado - Ervas Finas", "descricao": "", "unidade": "frasco", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 81, "nome": "Tempero desidratado - Folha de louro", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 82, "nome": "Tempero desidratado - Manjericão", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 83, "nome": "Tempero desidratado - Orégano", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 84, "nome": "Tempero em pó - Açafrão-da-terra (cúrcuma)", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 85, "nome": "Tempero em pó - Noz-moscada", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 86, "nome": "Tempero em pó - Páprica doce", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 87, "nome": "Tempero em pó - Coentro seco moído", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 88, "nome": "Tempero em pó - Cominho moído", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 89, "nome": "Tempero em pó - Pimenta-do-reino moída", "descricao": "", "unidade": "kg", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 90, "nome": "Tempero em pó - Pimenta-calabresa", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 91, "nome": "Tempero tipo mostarda", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"},
    {"codigo": 92, "nome": "Mel de abelha", "descricao": "", "unidade": "un", "quantidade_minima": 1, "status": "ativo"}
]


@event.listens_for(Usuario.__table__, "after_create")
def insert_usuario(target, connection, **kw):
    load_dotenv()
    nome = os.environ.get('ADMIN_USERNAME')
    email = os.environ.get('ADMIN_EMAIL')
    senha = os.environ.get('ADMIN_PASSWORD')
    senha_hash = generate_password_hash(senha)
    connection.execute(
        Usuario.__table__.insert(),
        ({"nome": nome, "email": email, "senha": senha_hash, "data_nascimento": "2000-01-01"})
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
            {"codigo": produto["codigo"], "nome": produto["nome"], "descricao": produto["descricao"], "unidade": produto["unidade"], "quantidade_minima": produto["quantidade_minima"], "status": produto["status"], 'tipo': produto['tipo']}
        )
    
    for produto in pereciveis:
        connection.execute(
            Produto.__table__.insert(),
            {"codigo": produto["codigo"], "nome": produto["nome"], "descricao": produto["descricao"], "unidade": produto["unidade"], "quantidade_minima": produto["quantidade_minima"], "status": produto["status"], 'tipo': 'perecivel'}
        )


@event.listens_for(SaldoDiario.__table__, "after_create")
def insert_saldos_diarios(target, connection, **kw):
    date = dt.date.today()

    for produto in produtos:
        connection.execute(
            SaldoDiario.__table__.insert(),
            {"data": date, "produto_id": produto["codigo"], "quantidade_inicial": 0, "quantidade_entrada": 0, "quantidade_saida": 0, "quantidade_final": 0}
        )


@event.listens_for(Refeicao.__table__, "after_create")
def insert_refeicoes(target, connection, **kw):
    refeicoes = ['Café da manhã', 'Lanche da manhã', 'Almoço', 'Lanche da tarde', 'Jantar', 'Ceia', 'Outros']
    for refeicao in refeicoes:
        connection.execute(
            Refeicao.__table__.insert(),
            {"nome": refeicao}
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


@event.listens_for(Ata.__table__, "after_create")
def insert_ata(target, connection, **kw):
    connection.execute(
        Ata.__table__.insert(),
        {"numero": "0", "ano": "0000", "fornecedor_id": 1, "tipo": "perecivel", "status": "ativo"}
    )


@event.listens_for(Empenho.__table__, "after_create")
def insert_empenho(target, connection, **kw):
    connection.execute(
        Empenho.__table__.insert(),
        {"numero": "0", "ano": "0000", "ata_id": 1, "fornecedor_id": 1, "status": "ativo"}
    )


@event.listens_for(NotaFiscal.__table__, "after_create")
def insert_nota_fiscal(target, connection, **kw):
    date = dt.date.today()

    connection.execute(
        NotaFiscal.__table__.insert(),
        {"numero": "-", "data_emissao": date, "empenho_id": 1, "fornecedor_id": 1, "serie": 0}
    )


@event.listens_for(Role.__table__, "after_create")
def insert_roles(target, connection, **kw):
    roles = ['admin', 'nutricionista', 'financeiro', 'assistencia', 'diretoria']

    for role in roles:
        connection.execute(
            Role.__table__.insert(),
            {"nome": role}
        )

@event.listens_for(RoleUser.__table__, "after_create")
def insert_roles_user(target, connection, **kw):
    connection.execute(
        RoleUser.__table__.insert(),
        {"usuario_id": 1, "role_id": 1, "ativado": True}
    )