
CREATE TABLE IF NOT EXISTS usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    data_nascimento DATE NOT NULL,
    nivel_acesso ENUM('Superusuario', 'Admin', 'Editor', 'Leitor') NOT NULL,
    status ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS destino (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS produto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo INT NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(100),
    unidade VARCHAR(10) NOT NULL,
    quantidade_minima INT NOT NULL,
    status ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS marca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    produto_id INT,
    FOREIGN KEY(produto_id) REFERENCES produto(id) ON DELETE CASCADE,
);

CREATE TABLE IF NOT EXISTS fornecedor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    status ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS nota_fiscal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(100) NOT NULL UNIQUE,
    data_emissao DATE NOT NULL,
    valor DECIMAL (10,2),
    fornecedor_id INT NOT NULL,
    FOREIGN KEY(fornecedor_id) REFERENCES fornecedor(id)
);

CREATE TABLE IF NOT EXISTS saidas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    destino_id INT NOT NULL,
    data_saida DATE NOT NULL,
    quantidade INT NOT NULL,
    observacao TEXT,
    usuario_id INT NOT NULL,
    marca_id INT NOT NULL,
    data_validade DATE NOT NULL,
    fornecedor_id INT NOT NULL,
    nota_fiscal_id INT NOT NULL,
    FOREIGN KEY(produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    FOREIGN KEY(usuario_id) REFERENCES usuario(id),
    FOREIGN KEY(destino_id) REFERENCES destino(id),
    FOREIGN KEY(marca_id) REFERENCES marca(id),
    FOREIGN KEY(fornecedor_id) REFERENCES fornecedor(id),
    FOREIGN KEY(nota_fiscal_id) REFERENCES nota_fiscal(id)
);

CREATE TABLE IF NOT EXISTS entradas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    data_entrada DATE NOT NULL,
    quantidade INT NOT NULL,
    observacao TEXT,
    usuario_id INT NOT NULL,
    marca_id INT NOT NULL,
    data_validade DATE NOT NULL,
    fornecedor_id INT NOT NULL,
    nota_fiscal_id INT NOT NULL,
    FOREIGN KEY(produto_id) REFERENCES produto(id) ON DELETE CASCADE,
    FOREIGN KEY(usuario_id) REFERENCES usuario(id),
    FOREIGN KEY(marca_id) REFERENCES marca(id),
    FOREIGN KEY(fornecedor_id) REFERENCES fornecedor(id),
    FOREIGN KEY(nota_fiscal_id) REFERENCES nota_fiscal(id)
);

CREATE TABLE IF NOT EXISTS saldo_diario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    data DATE NOT NULL,
    quantidade_inicial INT NOT NULL,
    quantidade_entrada INT NOT NULL,
    quantidade_saida INT NOT NULL,
    quantidade_final INT NOT NULL,
    FOREIGN KEY(produto_id) REFERENCES produto(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dias_fechados (
    data DATE PRIMARY KEY,
    fechado TINYINT(1) NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    usuario_id INT NOT NULL,
    operacao_id INT NOT NULL,
    tipo_operacao ENUM('entrada', 'saida') NOT NULL,
    tipo_operacao_2 ENUM('inserção', 'edição', 'exclusão') NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(produto_id) REFERENCES produto(id),
    FOREIGN KEY(usuario_id) REFERENCES usuario(id)
);
