-- ============================================================================
-- TRABALHO T3 - PROGRAMAÇÃO PARA CIÊNCIA DE DADOS
-- ETAPA 1: CONSTRUÇÃO, CARGA E PREPARAÇÃO DO BANCO DE DADOS (SIASUS / IJUÍ-RS)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS dbsia
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE dbsia;

-- ----------------------------------------------------------------------------
-- 1. TABELA PRINCIPAL DE PRODUÇÃO AMBULATORIAL (PARS)
-- ----------------------------------------------------------------------------
-- Criada a partir da estrutura do DATASUS (layout PAUFAAMM.DBF)
-- Carga realizada em lote via LOAD DATA INFILE com o arquivo convertido em CSV.

CREATE TABLE IF NOT EXISTS pars (
  pa_coduni    CHAR(7),
  pa_gestao    CHAR(6),
  pa_condic    CHAR(2),
  pa_ufmun     CHAR(6),
  pa_regct     CHAR(4),
  pa_incout    CHAR(4),
  pa_incurg    CHAR(4),
  pa_tpups     CHAR(2),
  pa_tippre    CHAR(2),
  pa_mn_ind    CHAR(1),
  pa_cnpjcpf   CHAR(14),
  pa_cnpjmnt   CHAR(14),
  pa_cnpj_cc   CHAR(14),
  pa_mvm       CHAR(6),
  pa_cmp       CHAR(6),
  pa_proc_id   CHAR(10),
  pa_tpfin     CHAR(2),
  pa_subfin    CHAR(4),
  pa_nivcpl    CHAR(1),
  pa_docorig   CHAR(1),
  pa_autoriz   CHAR(13),
  pa_cnsmed    CHAR(15),
  pa_cbocod    CHAR(6),
  pa_motsai    CHAR(2),
  pa_obito     CHAR(1),
  pa_encerr    CHAR(1),
  pa_perman    CHAR(1),
  pa_alta      CHAR(1),
  pa_transf    CHAR(1),
  pa_cidpri    CHAR(4),
  pa_cidsec    CHAR(4),
  pa_cidcas    CHAR(4),
  pa_catend    CHAR(2),
  pa_idade     CHAR(3),
  idademin     CHAR(3),
  idademax     CHAR(3),
  pa_flidade   CHAR(1),
  pa_sexo      CHAR(1),
  pa_racacor   CHAR(2),
  pa_munpcn    CHAR(6),
  pa_qtdpro    DECIMAL(11,0),
  pa_qtdapr    DECIMAL(11,0),
  pa_valpro    DECIMAL(20,2),
  pa_valapr    DECIMAL(20,2),
  pa_ufdif     CHAR(1),
  pa_mndif     CHAR(1),
  pa_dif_val   DECIMAL(20,2),
  nu_vpa_tot   DECIMAL(20,2),
  nu_pa_tot    DECIMAL(20,2),
  pa_indica    CHAR(1),
  pa_codoco    CHAR(1),
  pa_flqt      CHAR(1),
  pa_fler      CHAR(1),
  pa_etnia     CHAR(4),
  pa_vl_cf     DECIMAL(20,2),
  pa_vl_cl     DECIMAL(20,2),
  pa_vl_inc    DECIMAL(20,2),
  pa_srv_c     CHAR(6),
  pa_ine       CHAR(10),
  pa_nat_jur   CHAR(4),
  pa_fntorc    CHAR(2),
  pa_vl_crd    DECIMAL(20,2)
);

-- Exemplo da instrução LOAD DATA INFILE utilizada para importar os 4,4 milhões de registros:
-- LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/PARS2607.csv'
-- INTO TABLE pars
-- CHARACTER SET latin1
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\r\n'
-- IGNORE 1 ROWS;

-- Índice para otimização extrema das consultas filtradas pelo município
CREATE INDEX IF NOT EXISTS idx_pars_ufmun ON pars(pa_ufmun);

-- ----------------------------------------------------------------------------
-- 2. TABELAS AUXILIARES E DIMENSÕES
-- ----------------------------------------------------------------------------

-- 2.1 DIMENSÃO TEMPORAL (DIMTEMPO)
-- Gerada pelo script 04-gera-dimtempo-mysql.sql
-- Contém atributos de Ano, Mês, Bimestre, Trimestre e Semestre.

-- 2.2 CADASTRO GERAL DE ESTABELECIMENTOS DE SAÚDE DO RS (CADGERRS)
-- Vinculado por pa.pa_coduni = cadgerrs.cnes

-- 2.3 CLASSIFICAÇÃO BRASILEIRA DE OCUPAÇÕES (CBO)
-- Vinculado por pa.pa_cbocod = cbo.cbo

-- 2.4 TABELA UNIFICADA DE PROCEDIMENTOS (TB_SIGTAW)
CREATE OR REPLACE VIEW procedimentos AS 
SELECT * FROM TB_SIGTAW;

-- 2.5 CLASSIFICAÇÃO INTERNACIONAL DE DOENÇAS (S_CID)
CREATE OR REPLACE VIEW cid AS 
SELECT * FROM S_CID;

-- 2.6 TABELA DE MUNICÍPIOS (tb_municip)
-- Gerada a partir dos dados do IBGE/DATASUS (código de 6 dígitos + nome)
-- Vinculada em pa.pa_ufmun (estabelecimento) e pa.pa_munpcn (paciente)

-- ----------------------------------------------------------------------------
-- 3. CRIAÇÃO DA VIEW pa_ijui (RECORTE ESTRATÉGICO PARA GESTÃO DE SAÚDE)
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS pa_ijui;

CREATE OR REPLACE VIEW pa_ijui AS
SELECT
    -- 1. DIMENSÃO TEMPORAL
    dt.ano AS Ano,
    dt.mes AS Mes,
    dt.anobi AS AnoBimestre,
    dt.anotri AS AnoTrimestre,

    -- 2. ESTABELECIMENTO DE SAÚDE
    ca.fantasia AS Estabelecimento,

    -- 3. PROCEDIMENTO AMBULATORIAL
    pro.ip_dscr AS Procedimento,

    -- 4. OCUPAÇÃO PROFISSIONAL
    cb.ds_cbo AS Ocupacao,

    -- 5. PERFIL DEMOGRÁFICO
    pa.pa_sexo,
    pa.pa_idade,

    -- 6. DIAGNÓSTICO PRINCIPAL
    pa.pa_cidpri,
    cid.cd_descr AS Diagnostico,

    -- 7. MUNICÍPIO DO ESTABELECIMENTO
    mun_est.ds_nome AS MunicipioEstabelecimento,

    -- 8. MUNICÍPIO DO PACIENTE
    mun_pac.ds_nome AS MunicipioPaciente,

    -- 9. PRODUÇÃO AMBULATORIAL
    pa.pa_qtdpro,
    pa.pa_qtdapr,

    -- 10. VALORES FINANCEIROS
    pa.pa_valpro,
    pa.pa_valapr

FROM pars AS pa

-- Estabelecimento de saúde
LEFT JOIN cadgerrs AS ca
    ON pa.pa_coduni = ca.cnes

-- Procedimento ambulatorial
LEFT JOIN procedimentos AS pro
    ON pa.pa_proc_id = pro.ip_cod

-- Ocupação profissional
LEFT JOIN cbo AS cb
    ON pa.pa_cbocod = cb.cbo

-- Diagnóstico principal
LEFT JOIN cid
    ON pa.pa_cidpri = cid.cd_cod

-- Município do estabelecimento
LEFT JOIN tb_municip AS mun_est
    ON pa.pa_ufmun = mun_est.co_municip

-- Município do paciente
LEFT JOIN tb_municip AS mun_pac
    ON pa.pa_munpcn = mun_pac.co_municip

-- Dimensão temporal (mês de movimento)
LEFT JOIN DIMTEMPO AS dt
    ON pa.pa_mvm = dt.anomes

-- Produção realizada nos estabelecimentos de Ijuí (Código IBGE 431020)
WHERE pa.pa_ufmun = '431020';

-- ----------------------------------------------------------------------------
-- 4. CONSULTAS DE VALIDAÇÃO (ENTREGA DA AULA 1)
-- ----------------------------------------------------------------------------

-- Contagem total de registros na base central e na VIEW
SELECT count(*) AS total_pars_rs FROM pars;
SELECT count(*) AS total_registros_ijui FROM pa_ijui;

-- Resumo financeiro e volumétrico inicial
SELECT 
    sum(pa_qtdpro) AS qtd_apresentada,
    sum(pa_qtdapr) AS qtd_aprovada,
    sum(pa_valpro) AS valor_apresentado_total,
    sum(pa_valapr) AS valor_aprovado_total,
    sum(pa_valpro) - sum(pa_valapr) AS glosa_financeira
FROM pa_ijui;

-- Amostra de validação dos primeiros 5 registros
SELECT * FROM pa_ijui LIMIT 5;
