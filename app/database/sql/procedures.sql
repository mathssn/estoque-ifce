DROP PROCEDURE IF EXISTS SP_GetAtaSaldo;
DROP PROCEDURE IF EXISTS SP_GetEmpenhoSaldo;
DROP PROCEDURE IF EXISTS SP_GetEmpenhoSaldoPorAno;
DROP PROCEDURE IF EXISTS SP_GetNFValor;
DROP PROCEDURE IF EXISTS SP_GetEmpenhoValor;

DELIMITER $$

CREATE PROCEDURE SP_GetAtaSaldo (
    IN p_ata_id INT
)
BEGIN
    SELECT 
        ia.id AS item_ata_id,
        ia.quantidade_maxima,
        COALESCE(SUM(ie.quantidade_empenhada), 0) AS total_empenhado,
        ia.quantidade_maxima - COALESCE(SUM(ie.quantidade_empenhada), 0) AS saldo
    FROM item_ata ia
    LEFT JOIN item_empenho ie 
        ON ie.item_ata_id = ia.id
    WHERE ia.ata_id = p_ata_id
    GROUP BY ia.id, ia.quantidade_maxima;
END$$


CREATE PROCEDURE SP_GetEmpenhoSaldo (
    IN p_empenho_id INT
)
BEGIN
    SELECT 
        ie.id AS item_empenho_id,
        ie.quantidade_empenhada,
        COALESCE(SUM(inf.quantidade), 0) AS recebido,
        ie.quantidade_empenhada - COALESCE(SUM(inf.quantidade), 0) AS saldo
    FROM item_empenho ie
    LEFT JOIN item_nf inf
        ON inf.item_empenho_id = ie.id
    WHERE ie.empenho_id = p_empenho_id
    GROUP BY ie.id, ie.quantidade_empenhada;
END$$

-- Obtem saldo dos empenhos por ano (somente NF não canceladas)
CREATE PROCEDURE SP_GetEmpenhoSaldoPorAno(
    IN ano INT
)
BEGIN
    SELECT 
        e.id AS empenho_id,
        COALESCE(
            (SELECT SUM(ie.quantidade_empenhada * ia.valor_unitario)
             FROM item_empenho ie
             JOIN item_ata ia ON ia.id = ie.item_ata_id
             WHERE ie.empenho_id = e.id),
            0
        ) AS total_empenhado,
        COALESCE(
            (SELECT SUM(inf.quantidade * ia.valor_unitario)
             FROM item_empenho ie
             JOIN item_ata ia ON ia.id = ie.item_ata_id
             JOIN item_nf inf ON inf.item_empenho_id = ie.id
             JOIN nota_fiscal nf ON nf.id = inf.nota_fiscal_id
             WHERE ie.empenho_id = e.id
               AND nf.status <> 'cancelada'),
            0
        ) AS debitado,
        (
            COALESCE(
                (SELECT SUM(ie.quantidade_empenhada * ia.valor_unitario)
                 FROM item_empenho ie
                 JOIN item_ata ia ON ia.id = ie.item_ata_id
                 WHERE ie.empenho_id = e.id),
                0
            )
            -
            COALESCE(
                (SELECT SUM(inf.quantidade * ia.valor_unitario)
                 FROM item_empenho ie
                 JOIN item_ata ia ON ia.id = ie.item_ata_id
                 JOIN item_nf inf ON inf.item_empenho_id = ie.id
                 JOIN nota_fiscal nf ON nf.id = inf.nota_fiscal_id
                 WHERE ie.empenho_id = e.id
                   AND nf.status <> 'cancelada'),
                0
            )
        ) AS saldo
    FROM empenho e
    WHERE e.ano = ano
      AND e.status = 'ativo'
    GROUP BY e.id;
END$$

CREATE PROCEDURE SP_GetNFValor(
    IN nf_id INT
)

BEGIN
    SELECT
        nf.id AS nota_id,
        SUM(inf.quantidade * ia.valor_unitario) as total
    FROM nota_fiscal nf
    JOIN item_nf inf ON inf.nota_fiscal_id = nf.id
    JOIN item_empenho ie ON inf.item_empenho_id = ie.id
    JOIN item_ata ia ON ia.id = ie.item_ata_id
    WHERE nf.id = nf_id
    GROUP BY nf.id;
END$$

CREATE PROCEDURE SP_GetEmpenhoValor(
    IN e_id INT
)

BEGIN
    SELECT
        e.id AS empenho_id,
        COALESCE(
            (SUM(ie.quantidade_empenhada * ia.valor_unitario)),
            0
        ) as total
    FROM empenho e
    LEFT JOIN item_empenho ie ON ie.empenho_id = e.id
    LEFT JOIN item_ata ia ON ia.id = ie.item_ata_id
    WHERE e.id = e_id
    GROUP BY e.id;
END$$

DELIMITER ;
