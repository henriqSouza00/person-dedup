-- ======================================================================
-- 02 — APLICAR (só depois de conferir o 01)
-- Tabela: pessoa · 15 cópias a unificar
-- Gerado pelo person-dedup. Conferir antes de rodar.
-- ======================================================================

START TRANSACTION;

-- 1) Mapa cópia -> quem fica
CREATE TABLE IF NOT EXISTS dedup_mapa_20261021 (
  id_copia INT PRIMARY KEY, id_fica INT NOT NULL, motivo VARCHAR(60)
);
INSERT IGNORE INTO dedup_mapa_20261021 (id_copia, id_fica, motivo) VALUES
  (1001, 1, 'mesmo CPF'),
  (1002, 2, 'mesmo CPF'),
  (1003, 3, 'mesmo CPF'),
  (1004, 4, 'mesmo CPF'),
  (1005, 8, 'mesmo nascimento'),
  (1006, 12, 'mesmo nascimento'),
  (1007, 16, 'mesmo nascimento'),
  (1014, 41, 'mesma família'),
  (1015, 42, 'mesma família'),
  (1016, 43, 'mesma família'),
  (1020, 60, 'cópia sem vínculo'),
  (1021, 64, 'cópia sem vínculo'),
  (1022, 68, 'cópia sem vínculo'),
  (1026, 71, 'mesmo nascimento'),
  (1027, 72, 'mesmo nascimento');

-- 2) Backup das pessoas envolvidas (cópias e quem fica)
CREATE TABLE IF NOT EXISTS bkp_pessoa_20261021 LIKE pessoa;
INSERT IGNORE INTO bkp_pessoa_20261021
SELECT * FROM pessoa WHERE id IN (SELECT id_copia FROM dedup_mapa_20261021)
   OR id IN (SELECT id_fica FROM dedup_mapa_20261021);

-- 3) matricula.id_responsavel: backup e reponte
CREATE TABLE IF NOT EXISTS bkp_matricula_20261021 (pk BIGINT PRIMARY KEY, valor_antigo BIGINT);
INSERT IGNORE INTO bkp_matricula_20261021 (pk, valor_antigo)
SELECT id_matricula, id_responsavel FROM matricula
WHERE id_responsavel IN (SELECT id_copia FROM dedup_mapa_20261021);
UPDATE matricula x JOIN dedup_mapa_20261021 m ON m.id_copia = x.id_responsavel
SET x.id_responsavel = m.id_fica;

-- 3) filiacao.id_pessoa: backup e reponte
CREATE TABLE IF NOT EXISTS bkp_filiacao_20261021 (pk BIGINT PRIMARY KEY, valor_antigo BIGINT);
INSERT IGNORE INTO bkp_filiacao_20261021 (pk, valor_antigo)
SELECT id_filiacao, id_pessoa FROM filiacao
WHERE id_pessoa IN (SELECT id_copia FROM dedup_mapa_20261021);
UPDATE filiacao x JOIN dedup_mapa_20261021 m ON m.id_copia = x.id_pessoa
SET x.id_pessoa = m.id_fica;

-- 3) contato.id_pessoa: backup e reponte
CREATE TABLE IF NOT EXISTS bkp_contato_20261021 (pk BIGINT PRIMARY KEY, valor_antigo BIGINT);
INSERT IGNORE INTO bkp_contato_20261021 (pk, valor_antigo)
SELECT id_contato, id_pessoa FROM contato
WHERE id_pessoa IN (SELECT id_copia FROM dedup_mapa_20261021);
UPDATE contato x JOIN dedup_mapa_20261021 m ON m.id_copia = x.id_pessoa
SET x.id_pessoa = m.id_fica;

-- 4) Quem fica recebe os campos que estavam vazios (nunca sobrescreve)
UPDATE pessoa SET telefone = '11988880000' WHERE id = 1 AND (telefone IS NULL OR telefone = '');  -- veio do 1001
UPDATE pessoa SET telefone = '11988880000' WHERE id = 3 AND (telefone IS NULL OR telefone = '');  -- veio do 1003
UPDATE pessoa SET email = 'copia8@exemplo.com' WHERE id = 8 AND (email IS NULL OR email = '');  -- veio do 1005
UPDATE pessoa SET email = 'copia12@exemplo.com' WHERE id = 12 AND (email IS NULL OR email = '');  -- veio do 1006
UPDATE pessoa SET email = 'copia16@exemplo.com' WHERE id = 16 AND (email IS NULL OR email = '');  -- veio do 1007

-- 5) Apaga as cópias
DELETE p FROM pessoa p JOIN dedup_mapa_20261021 m ON m.id_copia = p.id;

-- 6) Conferência — ESPERADO: tudo 0
SELECT COUNT(*) AS copias_restantes FROM pessoa WHERE id IN (SELECT id_copia FROM dedup_mapa_20261021);
SELECT COUNT(*) AS matricula_apontando_para_copia FROM matricula WHERE id_responsavel IN (SELECT id_copia FROM dedup_mapa_20261021);
SELECT COUNT(*) AS matricula_orfaos FROM matricula x LEFT JOIN pessoa p ON p.id = x.id_responsavel WHERE x.id_responsavel IS NOT NULL AND p.id IS NULL;
SELECT COUNT(*) AS filiacao_apontando_para_copia FROM filiacao WHERE id_pessoa IN (SELECT id_copia FROM dedup_mapa_20261021);
SELECT COUNT(*) AS filiacao_orfaos FROM filiacao x LEFT JOIN pessoa p ON p.id = x.id_pessoa WHERE x.id_pessoa IS NOT NULL AND p.id IS NULL;
SELECT COUNT(*) AS contato_apontando_para_copia FROM contato WHERE id_pessoa IN (SELECT id_copia FROM dedup_mapa_20261021);
SELECT COUNT(*) AS contato_orfaos FROM contato x LEFT JOIN pessoa p ON p.id = x.id_pessoa WHERE x.id_pessoa IS NOT NULL AND p.id IS NULL;

-- Se os números baterem:
-- COMMIT;
-- Se algo estiver errado:
-- ROLLBACK;
