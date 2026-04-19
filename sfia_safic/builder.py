import sqlite3
import pandas as pd
import os
from pathlib import Path

def construir_banco_sia(db_osf, db_sia, excel_file):
    # 1. Validação Defensiva (Garante que o Excel está na pasta certa)
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"❌ ERRO: Planilha de parâmetros não encontrada em: {excel_file}")

    if os.path.exists(db_sia):
        os.remove(db_sia)

    # 2. Sanitização de Caminhos (Evita erros de escape no ATTACH do SQLite)
    safe_db_osf = Path(db_osf).as_posix()

    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()

    # 3. Turbinando a Performance do SQLite para o Build
    # Desliga a gravação de segurança no disco para acelerar os INSERTs/CREATEs massivos
    cursor.execute("PRAGMA journal_mode = OFF;")
    cursor.execute("PRAGMA synchronous = 0;")
    cursor.execute("PRAGMA cache_size = -1000000;") # Aloca ~1GB de RAM para o cache do SQLite

    # Anexa o banco OSF usando o caminho seguro
    cursor.execute(f"ATTACH DATABASE '{safe_db_osf}' AS osf;")

    print(f" ➔ Importando abas do Excel ({Path(excel_file).name})...")
    df_cfopd = pd.read_excel(excel_file, sheet_name="cfopd")
    df_regorig = pd.read_excel(excel_file, sheet_name="regOrig")
    df_cfopentsai = pd.read_excel(excel_file, sheet_name="cfopEntSai")

    df_cfopd.to_sql("cfopd", conn, if_exists="replace", index=False)
    df_regorig.to_sql("regOrig", conn, if_exists="replace", index=False)
    df_cfopentsai.to_sql("cfopEntSai", conn, if_exists="replace", index=False)

    print(" ➔ Criando Views no banco OSF...")
    SQL_VIEWS = """
    DROP VIEW IF EXISTS osf.EfdC100_EfdC100Detalhe_Efd0150;
    CREATE VIEW IF NOT EXISTS osf.EfdC100_EfdC100Detalhe_Efd0150 AS
    SELECT CASE WHEN A.IND_EMIT = 0 THEN CASE WHEN A.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS tp_oper,
    CASE WHEN A.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN A.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
    '[EfdC100]' AS tA, A.*, '[EfdC100Detalhe]' AS tB, B.*, '[Efd0150]' AS tG, G.* FROM dfe_fiscal_EfdC100 AS A
    LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS B ON B.idEfdC100 = A.idEfdC100 LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = A.idEfd0150;

    DROP VIEW IF EXISTS osf.EfdC170_Efd0200_Efd0190_EfdC100_EfdC100Detalhe_Efd0150;
    CREATE VIEW IF NOT EXISTS osf.EfdC170_Efd0200_Efd0190_EfdC100_EfdC100Detalhe_Efd0150 AS
    SELECT CASE WHEN B.IND_EMIT = 0 THEN CASE WHEN B.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN B.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS tp_oper,
    CASE WHEN B.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN B.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN B.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN B.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
    '[EfdC170]' AS tA, A.*, '[Efd0200]' AS tD, D.*, '[Efd0190]' AS tE, E.*, '[EfdC100]' AS tB, B.*, '[EfdC100Detalhe]' AS tC, C.*, '[Efd0150]' AS tG, G.*
    FROM dfe_fiscal_EfdC170 AS A LEFT OUTER JOIN _fiscal_efd0200 AS D ON D.COD_ITEM = A.COD_ITEM AND D.idArquivo = A.idArquivo
    LEFT OUTER JOIN _fiscal_efd0190 AS E ON E.UNID = D.UNID_INV AND E.idArquivo = A.idArquivo LEFT OUTER JOIN dfe_fiscal_EfdC100 AS B ON B.idEfdC100 = A.idEfdC100
    LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS C ON C.idEfdC100 = A.idEfdC100 LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = B.idEfd0150;

    DROP VIEW IF EXISTS osf.EfdC100_EfdC100Detalhe_Efd0150_EfdC190;
    CREATE VIEW IF NOT EXISTS osf.EfdC100_EfdC100Detalhe_Efd0150_EfdC190 AS
    SELECT CASE WHEN A.IND_EMIT = 0 THEN CASE WHEN A.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS tp_oper,
    CASE WHEN A.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN A.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
    '[EfdC100]' AS tA, A.*, '[EfdC100Detalhe]' AS tB, '[Efd0150]' AS tG, G.*, B.*, '[EfdC190]' AS tD, D.* FROM dfe_fiscal_EfdC190 AS D
    LEFT OUTER JOIN dfe_fiscal_EfdC100 AS A ON A.idEfdC100 = D.idEfdC100 LEFT OUTER JOIN dfe_fiscal_EfdC100Detalhe AS B ON B.idEfdC100 = A.idEfdC100
    LEFT OUTER JOIN dfe_fiscal_Efd0150 AS G ON G.idEfd0150 = A.idEfd0150;

    DROP VIEW IF EXISTS osf.EfdD100_EfdD100Detalhe_EfdD190;
    CREATE VIEW IF NOT EXISTS osf.EfdD100_EfdD100Detalhe_EfdD190 AS
    SELECT CASE WHEN A.IND_EMIT = 0 THEN CASE WHEN A.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS tp_oper,
    CASE WHEN A.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN A.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
    '[EfdD100]' AS tA, A.*, '[EfdD100Detalhe]' AS tB, B.*, '[EfdD190]' AS tC, C.* FROM dfe_fiscal_EfdD100 AS A
    LEFT OUTER JOIN dfe_fiscal_EfdD100Detalhe AS B ON B.idEfdD100 = A.idEfdD100 LEFT OUTER JOIN dfe_fiscal_EfdD190 AS C ON C.idEfdD100 = A.idEfdD100;
    
    DROP VIEW IF EXISTS osf.EfdG110_EfdG125_EfdG126;
    CREATE VIEW IF NOT EXISTS osf.EfdG110_EfdG125_EfdG126 AS
    SELECT '[EfdG110]' AS tA, A.*, '[EfdG125]' AS tB, B.*, '[EfdG126]' AS tC, C.* FROM Dfe_fiscal_EfdG110 AS A
    LEFT OUTER JOIN Dfe_fiscal_EfdG125 AS B ON B.idEfdG110 = A.idEfdG110 LEFT OUTER JOIN Dfe_fiscal_EfdG126 AS C ON C.idEfdG125 = B.idEfdG125;
    
    DROP VIEW IF EXISTS osf.NFes_Itens_C100_C170_C176_C182_C183;
    CREATE VIEW IF NOT EXISTS osf.NFes_Itens_C100_C170_C176_C182_C183 AS
    SELECT CASE WHEN A.IND_EMIT = 0 THEN CASE WHEN A.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.IND_OPER = 1 THEN 'ET' ELSE 'D' END END AS tp_oper,
    CASE WHEN A.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN A.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
    '[NfeC100]' AS tA, A.*, CASE WHEN A.IND_EMIT = 0 THEN A.CnpjDest || '_' || D102.UF || '_' || D102.NOME ELSE A.CnpjEmit || '_' || C101.UF || '_' || C101.NOME END AS Part,
    '[NfeC170]' AS tB, B.*, '[NfeC170InfProd]' AS tC, C.*, '[NfeC170IpiNaoTrib]' AS tD, D.*, '[NfeC170IpiTrib]' AS tE, E.*, '[NfeC170Resumo]' AS tF, F.*,
    '[NfeC170Tributos]' AS tG, G.*, '[NfeC176]' AS tH, H.*, '[NfeC182]' AS tI, I.*, '[NfeC183]' AS tJ, J.* FROM dfe_fiscal_NfeC100 AS A
    LEFT OUTER JOIN dfe_fiscal_NfeC101 AS C101 ON C101.idNfeC100 = A.idNfeC100 LEFT OUTER JOIN dfe_fiscal_NfeC102 AS D102 ON D102.idNfeC100 = A.idNfeC100
    LEFT OUTER JOIN dfe_fiscal_NfeC170 AS B ON B.idNfeC100 = A.idNfeC100 LEFT OUTER JOIN dfe_fiscal_NfeC170InfProd AS C ON C.idNFeC170 = B.idNFeC170
    LEFT OUTER JOIN dfe_fiscal_NfeC170IpiNaoTrib AS D ON D.idNFeC170 = B.idNFeC170 LEFT OUTER JOIN dfe_fiscal_NfeC170IpiTrib AS E ON E.idNFeC170 = B.idNFeC170
    LEFT OUTER JOIN dfe_fiscal_NfeC170Resumo AS F ON F.idNFeC170 = B.idNFeC170 LEFT OUTER JOIN dfe_fiscal_NfeC170Tributos AS G ON G.idNFeC170 = B.idNFeC170
    LEFT OUTER JOIN dfe_fiscal_NfeC176 AS H ON H.idNFeC170 = B.idNFeC170 LEFT OUTER JOIN dfe_fiscal_NfeC182 AS I ON I.idNFeC170 = B.idNFeC170
    LEFT OUTER JOIN dfe_fiscal_NfeC183 AS J ON J.idNFeC182 = I.idNFeC182;
    """
    cursor.executescript(SQL_VIEWS)

    print("Executando DDLs e montando tabelas auxiliares...")
    
    # Todos os comandos SQL extraídos do cookbook de construção do SIA
    sql_script = """
    CREATE INDEX IF NOT EXISTS main.cfopd_cfop ON cfopd (cfop);
    CREATE INDEX IF NOT EXISTS regOrig_idRegistroDeOrigem ON regOrig (idRegistroDeOrigem);
    CREATE INDEX IF NOT EXISTS main.cfopEntSai_cfop_dfe ON cfopEntSai (cfop_dfe);

    CREATE TABLE main.cfopd_es AS
    SELECT 
       A.cfop, B.cfop_efd, A.dfi, A.st, A.classe, A.g1, A.c3, A.g2, A.g3, A.descri_simplif, A.descri, A.pod_creditar 
       FROM cfopd AS A
       LEFT OUTER JOIN cfopEntSai AS B ON B.cfop_dfe = A.cfop;

    CREATE INDEX main.cfopd_es_cfop ON cfopd_es (cfop);
    CREATE INDEX main.cfopd_es_cfop_efd ON cfopd_es (cfop_efd);

    CREATE TABLE main.madf AS
    SELECT g1, g2, classe, cfopi, descri_simplif, dfi, aaaamm,
      sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd, sum(valconDif) AS valconDif,
      sum(icmsGia) AS icmsGia, sum(icmsEfd) AS icmsEfd, sum(icmsDif) AS icmsDif,
      sum(icmsstGia) AS icmsstGia, sum(icmsstEfd) AS icmsstEfd, sum(icmsstDif) AS icmsstDif
      FROM (
      SELECT sqA.cfopi, CAST(sqA.g1 AS VARCHAR) AS g1, CAST(sqA.g2 AS VARCHAR) AS g2, CAST(sqA.classe AS VARCHAR) AS classe,
          CAST(sqA.descri_simplif AS VARCHAR) AS descri_simplif, CAST(sqA.dfi AS VARCHAR) AS dfi,
          SUBSTR(sqA.referencia, 1, 4) || SUBSTR(sqA.referencia, 6, 2) AS aaaamm,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.valconGia ELSE sqA.valconGia END AS valconGia,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.valconEfd ELSE sqA.valconEfd END AS valconEfd,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.valconDif ELSE sqA.valconDif END AS valconDif,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsGia ELSE sqA.icmsGia END AS icmsGia,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsEfd ELSE sqA.icmsEfd END AS icmsEfd,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsDif ELSE sqA.icmsDif END AS icmsDif,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsstGia ELSE sqA.icmsstGia END AS icmsstGia,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsstEfd ELSE sqA.icmsstEfd END AS icmsstEfd,
          CASE WHEN sqA.cfopi<5000 THEN -sqA.icmsstDif ELSE sqA.icmsstDif END AS icmsstDif
       FROM (
        SELECT CAST(A.CFOP AS INT) AS cfopi, A.referencia,
          A.totalOperacoesGia AS valconGia, A.totalOperacoesEfd AS valconEfd, A.totalOperacoesDifGiaEfd AS valconDif,
          A.totalIcmsOpPropriaGia AS icmsGia, A.totalIcmsOpPropriaEfd AS icmsEfd, A.totalIcmsOpPropriaDifGiaEfd AS icmsDif,
          A.totalIcmsStGia AS icmsstGia, A.totalIcmsStEfd AS icmsstEfd, A.totalIcmsStDifGiaEfd AS icmsstDif, B.*
          FROM osf._fiscal_ComparacaoGiaEfdPorCfop AS A
          LEFT OUTER JOIN cfopd AS B ON B.cfop = CAST(A.CFOP AS INT)
        ) AS sqA
      ) AS sqB
      GROUP BY g1, g2, classe, cfopi, descri_simplif, dfi, aaaamm;

    CREATE INDEX IF NOT EXISTS osf.Docatrib_Fiscal_DocAtributosPart_idDocAtributos ON Docatrib_Fiscal_DocAtributosPart (idDocAtributos);
    CREATE INDEX IF NOT EXISTS osf._fiscal_ParticipanteDeclarado_idParticipanteDeclarado ON _fiscal_ParticipanteDeclarado (idParticipanteDeclarado);
    CREATE INDEX IF NOT EXISTS osf._fiscal_NatOp_idNatOp ON _fiscal_NatOp (idNatOp);
    CREATE INDEX IF NOT EXISTS osf.Dfe_fiscal_NfeC100_idNfeC100 ON Dfe_fiscal_NfeC100 (idNfeC100);
    CREATE INDEX IF NOT EXISTS osf.Dfe_fiscal_DocNum_idRegistro_idRegistroDeOrigem ON Dfe_fiscal_DocNum (idRegistro, idRegistroDeOrigem);

    CREATE TABLE main.idDocAtributos_compl AS
    SELECT A.idDocAtributos,
      B.tp_origem AS tp_origem, B.origem AS origem,
      CASE WHEN A.indEmit = 0 THEN
          CASE WHEN A.indOper = 0 THEN 'EP' ELSE 'S' END
      ELSE
          CASE WHEN A.indOper = 0 THEN 'ET' ELSE 'D' END
       END AS tp_oper,
      CASE WHEN A.codSit = 2 THEN 'cancelado' ELSE
        CASE WHEN A.codSit = 3 THEN 'cancelado' ELSE
          CASE WHEN A.codSit = 4 THEN 'denegado' ELSE
            CASE WHEN A.codSit = 5 THEN 'inutilizado' ELSE
              CASE WHEN A.codSit = 8 THEN 'válido' ELSE 'válido' END
            END
          END
        END
      END AS tp_codSit,
      CASE WHEN A.indEmit = 0 THEN A.ufDest ELSE A.ufOrg END AS uf,
      CASE WHEN A.indEmit = 0 THEN G.cnpj ELSE F.cnpj END AS cnpj_part,
      CASE WHEN A.indEmit = 0 THEN G.uf ELSE F.uf END AS uf_part,
      CASE WHEN A.indEmit = 0 THEN G.nome ELSE F.nome END AS nome_part,
      Q.chave, Q.numero,
      CASE WHEN origem = 'NFe' THEN H1.NaturezaOperacao ELSE '##TODO## captar Natop' END AS NatOp
    FROM osf.docatrib_fiscal_DocAtributos AS A
    LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = A.idRegistroDeOrigem
    LEFT OUTER JOIN osf.docatrib_fiscal_DocAtributosPart AS C ON C.idDocAtributos = A.idDocAtributos
    LEFT OUTER JOIN osf._fiscal_ParticipanteDeclarado AS F ON F.idParticipanteDeclarado = C.idEmit
    LEFT OUTER JOIN osf._fiscal_ParticipanteDeclarado AS G ON G.idParticipanteDeclarado = C.idDest
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC100 AS H1 ON H1.idNFeC100 = A.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_DocNum AS Q ON Q.idRegistro = A.idRegistro AND Q.idRegistroDeOrigem = A.idRegistroDeOrigem;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_compl_idDocAtributos ON idDocAtributos_compl (idDocAtributos);
    CREATE INDEX IF NOT EXISTS main.idDocAtributos_compl_chave ON idDocAtributos_compl (chave);

    CREATE INDEX IF NOT EXISTS osf.Dfe_fiscal_NfeC110_idNfeC100 ON Dfe_fiscal_NfeC110 (idNfeC100);
    CREATE INDEX IF NOT EXISTS osf.Dfe_fiscal_NfeC200_idNfeC200 ON Dfe_fiscal_NfeC200 (idNfeC200);
    CREATE INDEX IF NOT EXISTS osf.Dfe_fiscal_Sat100_idSat100 ON Dfe_fiscal_Sat100 (idSat100);

    CREATE TABLE IF NOT EXISTS main.idDocAtributos_chaveObs AS
    SELECT A.idDocAtributos, Q.chave,
    B.tp_origem AS tp_origem, B.origem AS origem,
    CASE WHEN origem = 'NFe' THEN H2.INF_AD_FISCO || ' - ' || H2.INF_COMPL
      ELSE '##TODO## captar Obs'
    END AS obs
    FROM osf.docatrib_fiscal_DocAtributos AS A
    LEFT OUTER JOIN osf.dfe_fiscal_DocNum AS Q ON Q.idRegistro = A.idRegistro AND Q.idRegistroDeOrigem = A.idRegistroDeOrigem
    LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = A.idRegistroDeOrigem
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC100 AS H1 ON H1.idNFeC100 = A.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC110 AS H2 ON H2.idNfeC100 = H1.idNfeC100
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC200 AS J1 ON J1.idNfeC200 = A.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_Sat100 AS L1 ON L1.idSat100 = A.idRegistro
    WHERE B.tp_origem = 'DFe' AND length(Q.chave) = 44;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_chaveObs_idDocAtributos ON idDocAtributos_chaveObs (idDocAtributos);
    CREATE INDEX IF NOT EXISTS main.idDocAtributos_chaveObs_chave ON idDocAtributos_chaveObs (chave);

    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_NfeC170_idNfeC170 ON dfe_fiscal_NfeC170 (idNfeC170);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_EfdC170_idEfdC170 ON dfe_fiscal_EfdC170 (idEfdC170);

    CREATE TABLE main.idDocAtributos_compl_item AS
    SELECT AI.idDocAtributosItem AS idDocAtributosItem,
      A.idDocAtributos AS idDocAtributos, B.tp_origem AS tp_origem, B.origem AS origem,
      AI.idRegistroItem AS idRegistroItem,
      CASE WHEN B.origem = 'EfdC100' THEN I.NUM_ITEM ELSE H.NUM_ITEM END AS NUM_ITEM
      FROM osf.docatrib_fiscal_DocAtributosItem AS AI
      LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AI.idDocAtributos
      LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
      LEFT OUTER JOIN osf.dfe_fiscal_EfdC170 AS I ON I.idEfdC170 = AI.idRegistroItem AND A.indEmit = 1 AND B.origem = 'EfdC100'
      LEFT OUTER JOIN osf.dfe_fiscal_NfeC170 AS H ON H.idNfeC170 = AI.idRegistroItem AND B.origem = 'NFe';

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_compl_item_idDocAtributosItem ON idDocAtributos_compl_item (idDocAtributosItem);
    CREATE INDEX IF NOT EXISTS main.idDocAtributos_compl_item_idDocAtributosItem_NUM_ITEM ON idDocAtributos_compl_item (idDocAtributosItem, NUM_ITEM);

    CREATE TEMP TABLE AG1Temp AS
    SELECT idDocAtributos, GROUP_CONCAT(g1, '|') AS g1s, GROUP_CONCAT(valorDaOperacao, '|') AS valoresDaOperacao
      FROM
      (SELECT idDocAtributos, g1, REPLACE(CAST(sqA.valorDaOperacao AS VARCHAR), '.', ',') AS valorDaOperacao
      FROM
      (SELECT AO.idDocAtributos, AO.cfop,
        CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN null ELSE CAST(AO.cfop AS INT) END AS cfopcv,
        EI.g1, sum(AO.valorDaOperacao) AS valorDaOperacao
        FROM osf.DocAtrib_fiscal_DocAtributosDeApuracao AS AO
        LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AO.idDocAtributos
        LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = AO.idRegistroDeOrigem
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN null ELSE CAST(AO.cfop AS INT) END
        GROUP BY AO.idDocAtributos, EI.g1) AS sqA
      GROUP BY idDocAtributos, g1, CAST(sqA.valorDaOperacao AS VARCHAR)) AS sqB
    GROUP BY idDocAtributos;

    CREATE INDEX IF NOT EXISTS temp.AG1Temp_idDocAtributos ON AG1Temp (idDocAtributos ASC);
    CREATE INDEX IF NOT EXISTS osf.DocAtrib_fiscal_DocAtributosDeApuracao_idDocAtributos_cfop ON DocAtrib_fiscal_DocAtributosDeApuracao (idDocAtributos, cfop);

    CREATE TABLE main.idDocAtributos_cfops(
        idDocAtributos int NOT NULL,
        cfops text,
        cfopcvs text,
        g1s text,
        valoresDaOperacao text NOT NULL
    );

    INSERT INTO idDocAtributos_cfops
    SELECT sqB.idDocAtributos, GROUP_CONCAT(sqB.cfop, '|') AS cfops, GROUP_CONCAT(sqB.cfopcv, '|') AS cfopcvs,
      AG1Temp.g1s, GROUP_CONCAT(sqB.valorDaOperacao, '|') AS valoresDaOperacao
      FROM
      (SELECT idDocAtributos, cfop, cfopcv, REPLACE(CAST(sqA.valorDaOperacao AS VARCHAR), '.', ',') AS valorDaOperacao
      FROM
      (SELECT AO.idDocAtributos, AO.cfop,
        CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN null ELSE CAST(AO.cfop AS INT) END AS cfopcv,
        sum(AO.valorDaOperacao) AS valorDaOperacao
        FROM osf.DocAtrib_fiscal_DocAtributosDeApuracao AS AO
        LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AO.idDocAtributos
        LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = AO.idRegistroDeOrigem
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN null ELSE CAST(AO.cfop AS INT) END
        GROUP BY AO.idDocAtributos, cfopcv) AS sqA
      GROUP BY idDocAtributos, cfop, CAST(sqA.valorDaOperacao AS VARCHAR)) AS sqB
    LEFT OUTER JOIN AG1Temp ON AG1Temp.idDocAtributos = sqB.idDocAtributos
    GROUP BY sqB.idDocAtributos;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_cfops_idDocAtributos ON idDocAtributos_cfops (idDocAtributos);

    CREATE TABLE idDocAtributos_classif(
        idDocAtributos int NOT NULL,
        classifs text NOT NULL
    );

    CREATE INDEX IF NOT EXISTS osf.docatrib_fiscal_DocClassificado_idDocAtributos_idClassificacao ON docatrib_fiscal_DocClassificado (idDocAtributos, idClassificacao);

    INSERT INTO idDocAtributos_classif 
    SELECT idDocAtributos, GROUP_CONCAT(classif, '') AS classifs
      FROM
      (SELECT idDocAtributos, '[' || CAST(idClassificacao AS VARCHAR) || ']' AS classif
        FROM osf.docatrib_fiscal_DocClassificado
        GROUP BY idDocAtributos, idClassificacao) AS sqA
    GROUP BY idDocAtributos;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_classif_idDocAtributos ON idDocAtributos_classif (idDocAtributos);

    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_Evt191_idNfeC100 ON dfe_fiscal_Evt191 (idNfeC100);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_Evt192_idEvt191 ON dfe_fiscal_Evt192 (idEvt191);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_Evt291_idNfeC200 ON dfe_fiscal_Evt291 (idNfeC200);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_Evt292_idEvt291 ON dfe_fiscal_Evt292 (idEvt291);

    CREATE TABLE main.docAtribBaseEfdPart AS
    SELECT A.idDocAtributos, A.idRegistroDeOrigem, A.idRegistro,
    '[EvtX91]' AS tHJ, H.ind_tipo_emit, H.ind_tipo_oper, H.cod_sit_doc_fiscal, H.ref_ano_mes, H.data_emissao_doc_fiscal,
    H.data_entrada_saida, H.valor_icms AS icmsX91, H.valor_icms_st AS icmsstX91, H.cod_uf_dest_icms_st, H.valor_ipi AS ipiX91,
    H.num_cnpj, H.cod_uf, H.num_isuframa, H.ind_perfil_arq_fiscal, H.nome_entidade,
    '[EvtX92]' AS tIK, I.cod_sit_trib, I.cod_cfop_agrup_itens, I.valor_per_aliq_icms, I.valor_bc_icms, I.valor_icms AS icmsX92, I.valor_bc_icms_st, I.valor_icms_st AS icmsstX92,
    I.valor_reduc_base_calc, I.valor_ipi AS ipiX92, I.valor_operacao
    FROM osf.DocAtrib_fiscal_DocAtributos AS A
    INNER JOIN osf.dfe_fiscal_Evt191 AS H ON H.idNFeC100 = A.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_Evt192 AS I ON I.idEvt191 = H.idEvt191
    WHERE A.idRegistroDeOrigem = 11
    UNION ALL
    SELECT A.idDocAtributos, A.idRegistroDeOrigem, A.idRegistro,
    '[EvtX91]' AS tHJ, J.ind_emit_docto_fiscal, J.ind_tipo_oper, J.cod_sit_doc_fiscal, J.ref_ano_mes, J.data_emissao_doc_fiscal,
    J.data_aquisicao, J.valor_icms AS icmsX91, 0 AS icmsstX91, Null AS cod_uf_dest_icms_st, 0 AS ipiX91,
    J.num_cnpj, J.cod_uf, J.num_isuframa, J.ind_perfil_arq_fiscal, J.nome_entidade,
    '[EvtX92]' AS tIK, K.cod_sit_trib, K.cod_cfop, K.valor_aliq_icms, K.valor_bc_icms, K.valor_icms AS icmsX92, 0 AS valor_bc_icms_st, 0 AS icmsstX92,
    0 AS valor_reduc_base_calc, 0 AS ipiX92, K.valor_operacao
    FROM osf.DocAtrib_fiscal_DocAtributos AS A
    INNER JOIN osf.dfe_fiscal_Evt291 AS J ON J.idNfeC200 = A.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_Evt292 AS K ON K.idEvt291 = J.idEvt291
    WHERE A.idRegistroDeOrigem = 12;

    CREATE INDEX IF NOT EXISTS main.docAtribBaseEfdPart_idDocAtributos ON docAtribBaseEfdPart (idDocAtributos);

    CREATE TABLE idDocAtributos_efdPart(
        idDocAtributos int NOT NULL,
        cod_sit_doc_fiscal int NOT NULL,
        cfops text NULL,
        valoresDaOperacao text NULL,
        valorDaOperacao real NULL,
        icmss text NULL,
        icms real NULL
    );

    INSERT INTO idDocAtributos_efdPart
    SELECT sqB.idDocAtributos, GROUP_CONCAT(sqB.cod_sit_doc_fiscal, '|') AS cod_sit_doc_fiscal, GROUP_CONCAT(sqB.cfops, '|') AS cfops,
      REPLACE(GROUP_CONCAT(CAST(sqB.valorDaOperacao AS VARCHAR), '|'), '.', ',') AS valoresDaOperacao, sum(sqB.valorDaOperacao) AS valorDaOperacao,
      REPLACE(GROUP_CONCAT(CAST(sqB.icms AS VARCHAR), '|'), '.', ',') AS icmss, sum(sqB.icms) AS icms
      FROM
    (SELECT idDocAtributos, cod_sit_doc_fiscal, GROUP_CONCAT(cfop, '|') AS cfops,
      REPLACE(GROUP_CONCAT(CAST(sqA.valorDaOperacao AS VARCHAR), '|'), '.', ',') AS valoresDaOperacao, sum(valorDaOperacao) AS valorDaOperacao,
      REPLACE(GROUP_CONCAT(CAST(sqA.icms AS VARCHAR), '|'), '.', ',') AS icmss, sum(icms) AS icms
      FROM
      (SELECT idDocAtributos, cod_sit_doc_fiscal, cod_cfop_agrup_itens AS cfop, sum(valor_operacao) AS valorDaOperacao, sum(icmsX92) AS icms
        FROM docAtribBaseEfdPart
        GROUP BY idDocAtributos, cod_sit_doc_fiscal, cod_cfop_agrup_itens) AS sqA
      GROUP BY sqA.idDocAtributos, sqA.cod_sit_doc_fiscal) AS sqB
    GROUP BY sqB.idDocAtributos;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_efdPart_idDocAtributos ON idDocAtributos_efdPart (idDocAtributos);

    CREATE TABLE idDocAtributos_itens(
        idDocAtributos int NOT NULL,
        descris text NOT NULL
    );

    CREATE INDEX IF NOT EXISTS osf.docatrib_fiscal_DocAtributosItem_idDocAtributos ON docatrib_fiscal_DocAtributosItem (idDocAtributos);
    CREATE INDEX IF NOT EXISTS osf._fiscal_ItemServicoDeclarado_idItemServicoDeclarado ON _fiscal_ItemServicoDeclarado (idItemServicoDeclarado);

    INSERT INTO idDocAtributos_itens
    SELECT sqD.idDocAtributos, CASE WHEN sqD.descris IS NULL THEN '#DescrisNull#' ELSE sqD.descris END AS descris FROM
      (SELECT sqC.idDocAtributos AS idDocAtributos, CASE WHEN sqC.cidDA <= 3 THEN descrisBig ELSE descrisShort END AS descris FROM
        (SELECT idDocAtributos, count(idDocAtributos) AS cidDA,
          GROUP_CONCAT(descriBig, '|') AS descrisBig, GROUP_CONCAT(descriShort, '|') AS descrisShort FROM
        (SELECT * FROM
          (SELECT A.idDocAtributos, SUBSTR(B.descricao, 1, 50) AS descriBig, SUBSTR(B.descricao, 1, 25) AS descriShort
            FROM osf.docatrib_fiscal_DocAtributosItem AS A
            LEFT OUTER JOIN osf._fiscal_ItemServicoDeclarado AS B ON B.idItemServicoDeclarado = A.idItemServicoDeclarado) AS sqA
          GROUP BY sqA.idDocAtributos, descriBig, descriShort) AS sqB
        GROUP BY idDocAtributos) AS sqC) AS sqD;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_itens_idDocAtributos ON idDocAtributos_itens (idDocAtributos);

    CREATE TABLE idDocAtributos_ncms(
        idDocAtributos int NOT NULL,
        codncms text
    );

    INSERT INTO idDocAtributos_ncms 
    SELECT idDocAtributos, GROUP_CONCAT(COD_NCM, '|') AS codncms FROM
      (SELECT * FROM
        (SELECT A.idDocAtributos, A.COD_NCM
          FROM osf.docatrib_fiscal_DocAtributosItem AS A) AS sqA
        GROUP BY sqA.idDocAtributos, sqA.COD_NCM) AS sqB
      GROUP BY idDocAtributos;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_ncms_idDocAtributos ON idDocAtributos_ncms (idDocAtributos);

    CREATE TABLE idDocAtributos_aliqs(
        idDocAtributos int NOT NULL,
        aliqs text
    );

    INSERT INTO idDocAtributos_aliqs
    SELECT idDocAtributos, GROUP_CONCAT(aliqIcms, '|') AS aliqs FROM
      (SELECT * FROM
        (SELECT A.idDocAtributos, A.aliqIcms
          FROM osf.DocAtrib_fiscal_DocAtributosDeApuracao AS A) AS sqA
        GROUP BY sqA.idDocAtributos, sqA.aliqIcms) AS sqB
      GROUP BY idDocAtributos;

    CREATE INDEX IF NOT EXISTS main.idDocAtributos_aliqs_idDocAtributos ON idDocAtributos_aliqs (idDocAtributos);

    CREATE INDEX IF NOT EXISTS osf._fiscalCadesp_HistoricoRegimeDeApuracao_cnpj ON _fiscalCadesp_HistoricoRegimeDeApuracao (cnpj);

    CREATE TABLE main.cnpjRegs AS 
    SELECT cnpj, GROUP_CONCAT(reg, ',') AS regs, GROUP_CONCAT(dtinifim, ',') AS dtinifim FROM
    (SELECT A.cnpj, A.sgRegime AS reg,
      SUBSTR(CAST(A.dtInicio AS VARCHAR), 3, 2) || SUBSTR(CAST(A.dtInicio AS VARCHAR), 6, 2) || '-' ||
      SUBSTR(IFNULL(CAST(A.dtFim AS VARCHAR), ''), 3, 2) || SUBSTR(IFNULL(CAST(A.dtFim AS VARCHAR), ''), 6, 2) AS dtinifim
    FROM osf._fiscalCadesp_HistoricoRegimeDeApuracao AS A
    WHERE (dtFim IS NULL OR dtFim = '' OR dtFim > '2010-01-01')) AS sqA
    GROUP BY cnpj;

    CREATE INDEX IF NOT EXISTS cnpjRegs_cnpj ON cnpjRegs (cnpj);

    CREATE INDEX IF NOT EXISTS osf._fiscal_OcorrenciaCadesp_cdOcorrenciaCadastral ON _fiscal_OcorrenciaCadesp (cdOcorrenciaCadastral);

    CREATE TABLE main.cnpjSit AS
    SELECT A.cnpj AS cnpj,
      replace(replace(replace(replace(
      A.cdOcorrenciaCadastral || '-' || B.dsSituacao || CASE WHEN B.dsSituacao <> 'Ativo' THEN '-' || B.dsOcorrenciaCadastral ELSE '' END
      , 'Inapto', '##Inapto##') , 'Nulo', '##Nulo##') , 'Suspenso', '#Suspenso#') , 'Baixado', '#Baixado#') AS Situacao,
      SUBSTR(CAST(A.dtInicioAtividade AS VARCHAR), 3, 2) || SUBSTR(CAST(A.dtInicioAtividade  AS VARCHAR), 6, 2) || '-' ||
      SUBSTR(IFNULL(CAST(A.dtInatividade AS VARCHAR), ''), 3, 2) || SUBSTR(IFNULL(CAST(A.dtInatividade AS VARCHAR), ''), 6, 2) AS dtinifim
    FROM osf._fiscalCadesp_Cadastro AS A
    LEFT OUTER JOIN osf._fiscal_OcorrenciaCadesp AS B ON B.cdOcorrenciaCadastral = A.cdOcorrenciaCadastral;

    CREATE INDEX IF NOT EXISTS cnpjSit_cnpj ON cnpjSit (cnpj);

    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_EfdC100_idEfdC100 ON dfe_fiscal_EfdC100 (idEfdC100);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_EfdD100_idEfdD100 ON dfe_fiscal_EfdD100 (idEfdD100);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_NfeC211Resumo_idNfeC200 ON dfe_fiscal_NfeC211Resumo (idNfeC200);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_EfdC800_idEfdC800 ON dfe_fiscal_EfdC800 (idEfdC800);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_Sat104_idSat100 ON dfe_fiscal_Sat104 (idSat100);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_NfceC100_idNFCeC100 ON dfe_fiscal_NfceC100 (idNFCeC100);

    CREATE TABLE main.docAtribTudao AS
    SELECT
      B.idDocAtributos,
      Class.classifs,
      substr(B.referencia, 1, 7) AS ref, Compl.tp_origem, Compl.origem, Compl.tp_codSit, B.indEmit, B.indOper,
      Compl.cnpj_part || '_' || Compl.uf_part || '_' || Compl.nome_part AS Part,
      cnpjSit.Situacao AS SituacaoPart, cnpjSit.dtinifim AS dtinifimSitPart,
      cnpjRegs.regs AS regPart, cnpjRegs.dtinifim AS dtinifimRegPart,
      Compl.chave, Compl.numero, Compl.uf, B.dtEmissao, B.dtEntSd, Cfops.cfops, Cfops.cfopcvs, Cfops.g1s,
      B.vlTotalDoc, B.vlBcIcmsProprio, B.vlIcmsProprio, B.vlBcIcmsSt, B.vlIcmsSt,
      Efd_Part.cod_sit_doc_fiscal AS EfdPartCodSit, Efd_Part.cfops AS EfdPartCfops, Efd_Part.valorDaOperacao AS EfdPartVal, Efd_Part.icms AS EfdPartIcms,
      Compl.NatOp, itens.descris AS descris, ncms.codncms AS codncms, aliqs.aliqs AS aliqs,
      '[ConcDFeEfd]' AS tFinal,
      CASE WHEN Compl.origem = 'NFe' THEN H.CHV_NFE ELSE CASE WHEN Compl.origem = 'EfdC100' THEN I.CHV_NFE ELSE
        CASE WHEN Compl.origem = 'CTe' THEN J1.Id ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN K.CHV_CTE ELSE
        CASE WHEN Compl.origem = 'SAT' THEN L1.CHV_SAT ELSE CASE WHEN Compl.origem = 'EfdC800' THEN M.CHV_CFE ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN N.CHV_NFE ELSE '#TODO#' END END END END END END END AS CHV_DFE,
      CASE WHEN Compl.origem = 'NFe' THEN H.NUM_DOC ELSE CASE WHEN Compl.origem = 'EfdC100' THEN I.NUM_DOC ELSE
        CASE WHEN Compl.origem = 'CTe' THEN J1.nCT ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN K.NUM_DOC ELSE
        CASE WHEN Compl.origem = 'SAT' THEN L1.nserieSAT ELSE CASE WHEN Compl.origem = 'EfdC800' THEN M.NR_SAT ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN N.NUM_DOC ELSE -1 END END END END END END END AS NUM_DOC,
      CASE WHEN Compl.origem = 'NFe' THEN H.VL_DOC ELSE CASE WHEN Compl.origem = 'EfdC100' THEN -I.VL_DOC ELSE
        CASE WHEN Compl.origem = 'CTe' THEN J2.valorOperacao ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN -K.VL_DOC ELSE
        CASE WHEN Compl.origem = 'SAT' THEN L2.vCFe ELSE CASE WHEN Compl.origem = 'EfdC800' THEN -M.VL_CFE ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN -N.VL_DOC ELSE -1 END END END END END END END AS VL_DOC,
      CASE WHEN Compl.origem = 'NFe' THEN H.VL_ICMS ELSE CASE WHEN Compl.origem = 'EfdC100' THEN -I.VL_ICMS ELSE
        CASE WHEN Compl.origem = 'CTe' THEN J2.valorIcms ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN -K.VL_ICMS ELSE
        CASE WHEN Compl.origem = 'SAT' THEN L2.vICMS ELSE CASE WHEN Compl.origem = 'EfdC800' THEN -M.VL_ICMS ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN -N.VL_ICMS ELSE -1 END END END END END END END AS VL_ICMS,
      CASE WHEN Compl.origem = 'NFe' THEN H.VL_ICMS_ST ELSE CASE WHEN Compl.origem = 'EfdC100' THEN -I.VL_ICMS_ST ELSE
        CASE WHEN Compl.origem = 'CTe' THEN J2.valorIcmsSt ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN 0 ELSE
        CASE WHEN Compl.origem = 'SAT' THEN 0 ELSE CASE WHEN Compl.origem = 'EfdC800' THEN 0 ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN -N.VL_ICMS_ST ELSE -1 END END END END END END END AS VL_ICMS_ST,
      CASE WHEN Compl.origem = 'NFe' THEN H.VL_IPI ELSE CASE WHEN Compl.origem = 'EfdC100' THEN -I.VL_IPI ELSE
        CASE WHEN Compl.origem = 'CTe' THEN 0 ELSE CASE WHEN Compl.origem = 'EfdD100Cte' THEN 0 ELSE
        CASE WHEN Compl.origem = 'SAT' THEN 0 ELSE CASE WHEN Compl.origem = 'EfdC800' THEN 0 ELSE
        CASE WHEN Compl.origem = 'NFCe' THEN 0 ELSE -1 END END END END END END END AS VL_IPI
    FROM osf.DocAtrib_fiscal_DocAtributos AS B
    LEFT OUTER JOIN idDocAtributos_compl AS Compl ON Compl.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_classif AS Class ON Class.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_cfops AS Cfops ON Cfops.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_efdPart AS Efd_Part  ON Efd_Part.idDocAtributos  = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_itens AS itens ON itens.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_ncms AS ncms ON ncms.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_aliqs AS aliqs ON aliqs.idDocAtributos = B.idDocAtributos
    LEFT OUTER JOIN cnpjSit AS cnpjSit ON cnpjSit.cnpj =  Compl.cnpj_part
    LEFT OUTER JOIN cnpjRegs AS cnpjRegs ON cnpjRegs.cnpj = Compl.cnpj_part
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC100 AS H ON H.idNFeC100 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_EfdC100 AS I ON I.idEfdC100 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC200 AS J1 ON J1.idNfeC200 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_NfeC211Resumo AS J2 ON J2.idNfeC200 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_EfdD100 AS K ON K.idEfdD100 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_Sat100 AS L1 ON L1.idSat100 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_Sat104 AS L2 ON L2.idSat100 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_EfdC800 AS M ON M.idEfdC800 = B.idRegistro
    LEFT OUTER JOIN osf.dfe_fiscal_NfceC100 AS N ON N.idNFCeC100 = B.idRegistro;

    CREATE INDEX IF NOT EXISTS docAtribTudao_idDocAtributos ON docAtribTudao (idDocAtributos);

    CREATE INDEX IF NOT EXISTS osf.DocAtrib_fiscal_DocAtributos_idDocAtributos ON DocAtrib_fiscal_DocAtributos (idDocAtributos);

    CREATE TABLE main.chaveNroTudao AS
    SELECT SqB.tp_codSit, SqB.indEmit, SqB.indOper,
       CASE WHEN CAST(SqB.indEmit AS INT) = 0 THEN
           CASE WHEN CAST(SqB.indOper AS INT) = 0 THEN 'EP' ELSE 'S' END
       ELSE
           CASE WHEN CAST(SqB.indOper AS INT) = 0 THEN 'ET' ELSE 'D' END
       END AS tp_oper,
       SqB.ref, SqB.chave, SqB.numero, SqB.uf,
       round(SqB.vl_docDFe - SqB.vl_docEFD, 2) AS dif_vl_doc,
       round(SqB.vl_icmsDFe - SqB.vl_icmsEFD, 2) AS dif_icms,
       round(SqB.vl_icmsstSP_DFe - SqB.vl_icmsstSP_EFD, 2) AS dif_icmsstSP,
    SqB.vl_docDFe, SqB.vl_docEFD, SqB.vl_icmsDFe, SqB.vl_icmsEFD, SqB.vl_icmsstSP_DFe, SqB.vl_icmsstSP_EFD, SqB.vl_icmsstUFs_DFe, SqB.vl_icmsstUFs_EFD,
    SqB.DFe_idDocAtributos, SqB.EFD_idDocAtributos,
    '[DFe - Efd]' AS tChNr,
      CASE WHEN SqB.DFe_idDocAtributos >= 0 THEN
          coalesce(DA_DFeT.Part, '') || ' ' || coalesce(DA_DFeT.SituacaoPart, '') || ' ' || coalesce(DA_DFeT.dtinifimSitPart, '') || ' ' || coalesce(DA_DFeT.regPart, '') || ' ' || coalesce(DA_DFeT.dtinifimRegPart, '')
      ELSE
          coalesce(DA_EfdT.Part, '') || ' ' || coalesce(DA_EfdT.SituacaoPart, '') || ' ' || coalesce(DA_EfdT.dtinifimSitPart, '') || ' ' || coalesce(DA_EfdT.regPart, '') || ' ' || coalesce(DA_EfdT.dtinifimRegPart, '')
      END AS Part,
      coalesce(DA_DFeT.classifs, '') || ' - ' || coalesce(DA_EfdT.classifs, '') AS 'ChNrClassifs',
      coalesce(substr(DA_DFe.referencia, 1, 7), '') || ' - ' || coalesce(substr(DA_Efd.referencia, 1, 7), '') AS 'ChNrRef',
      '[' || coalesce(DA_DFeT.origem,  '') || '-' || coalesce(DA_EfdT.origem,  '') || ']' AS 'ChNrOrigem',
      '[' || coalesce(DA_DFe.codSit,  '') || '-' || coalesce(DA_Efd.codSit,  '') || ']' AS 'ChNrCodSit',
      '[' || coalesce(DA_DFe.indEmit, '') || '-' || coalesce(DA_Efd.indEmit, '') || ']' AS 'ChNrIndEmit',
      '[' || coalesce(DA_DFe.indOper, '') || '-' || coalesce(DA_Efd.indOper, '') || ']' AS 'ChNrIndOper',
      '[' || coalesce(DA_DFeT.cfops, '') || '-' || coalesce(DA_EfdT.cfops, '') || ']' AS 'ChNrCfops',
      '[' || coalesce(DA_DFeT.cfopcvs, '') || '-' || coalesce(DA_EfdT.cfopcvs, '') || ']' AS 'ChNrCfopcvs',
      '[' || coalesce(DA_DFeT.g1s, '') || '-' || coalesce(DA_EfdT.g1s, '') || ']' AS 'ChNrG1s',
      '[ValsNFe]' AS tDA_DFe, DA_DFe.dtEmissao AS DFeDtEmi, DA_DFe.dtEntSd AS DFeDtEntSd, DA_DFeT.cfops AS DFeCfops, DA_DFeT.cfopcvs AS DFeCfopcvs,
      DA_DFeT.g1s AS DFeG1s, DA_DFe.vlTotalDoc AS DFeValCon, DA_DFe.vlBcIcmsProprio AS DFeBCIcms, DA_DFe.vlIcmsProprio AS DFeIcms,
      DA_DFe.vlBcIcmsSt AS DFeBCIcmsST, DA_DFe.vlIcmsSt AS DFeIcmsSt, abs(DA_DFeT.VL_IPI) AS DFeIpi,
      '[ValsEfd]' AS tDA_Efd, DA_Efd.dtEmissao AS EfdDtEmi, DA_Efd.dtEntSd AS EfdDtEntSd, DA_EfdT.cfopcvs AS EfdCfopcvs,
      DA_EfdT.g1s AS EfdG1s, DA_Efd.vlTotalDoc AS EfdValCon, DA_Efd.vlBcIcmsProprio AS EfdBCIcms, DA_Efd.vlIcmsProprio AS EfdIcms,
      DA_Efd.vlBcIcmsSt AS EfdBCIcmsST, DA_Efd.vlIcmsSt AS EfdIcmsSt, abs(DA_EfdT.VL_IPI) AS EfdIpi,
      '[Efd_Part]' AS tEfd_Part, Efd_Part.cod_sit_doc_fiscal AS EfdPartCodSit, Efd_Part.cfops AS EfdPartCfops,
      Efd_Part.valoresDaOperacao AS EfdPartValsCons, Efd_Part.valorDaOperacao AS EfdPartValCon, Efd_Part.icmss AS EfdPartIcmss, Efd_Part.icms AS EfdPartIcms,
      DA_DFeT.NatOp AS DFeNatOp, DA_DFeT.codncms AS DFeCodncms, DA_EfdT.codncms AS EfdCodncms, DA_DFeT.aliqs AS DFeAliqs, DA_EfdT.aliqs AS EfdAliqs,
      DA_DFeT.descris AS DFeDescris, DA_EfdT.descris AS EfdDescris,
      CO_NFe.obs
    FROM
    (SELECT  SqA.tp_codSit, SqA.indEmit, SqA.indOper, substr(SqA.referencia, 1, 7) AS ref,
       SqA.chave, SqA.numero, SqA.uf,
       max(DFe_idDocAtributos) AS DFe_idDocAtributos, max(EFD_idDocAtributos) AS EFD_idDocAtributos,
       sum(SqA.vl_docDFe) AS vl_docDFe, sum(SqA.vl_docEFD) AS vl_docEFD,
       sum(SqA.vl_icmsDFe) AS vl_icmsDFe, sum(SqA.vl_icmsEFD) AS vl_icmsEFD,
       sum(SqA.vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(SqA.vl_icmsstSP_EFD) AS vl_icmsstSP_EFD,
       sum(SqA.vl_icmsstUFs_DFe) AS vl_icmsstUFs_DFe, sum(SqA.vl_icmsstUFs_EFD) AS vl_icmsstUFs_EFD
       FROM
    (SELECT
      B.tp_codSit,
      A.indEmit, A.indOper, A.referencia, B.tp_origem, B.chave, B.numero, B.uf,
      CASE WHEN B.tp_origem = 'DFe' THEN A.idDocAtributos ELSE -2 END AS DFe_idDocAtributos,
      CASE WHEN B.tp_origem = 'EFD' THEN A.idDocAtributos ELSE -2 END AS EFD_idDocAtributos,
      CASE WHEN B.tp_origem = 'DFe' THEN A.vlTotalDoc ELSE 0 END AS vl_docDFe,
      CASE WHEN B.tp_origem = 'EFD' THEN A.vlTotalDoc ELSE 0 END AS vl_docEFD,
      CASE WHEN B.tp_origem = 'DFe' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsDFe,
      CASE WHEN B.tp_origem = 'EFD' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsEFD,
      CASE WHEN B.tp_origem = 'DFe' THEN
        CASE WHEN (A.indEmit = 0 AND A.ufDest = 'SP') OR (A.indEmit = 1 AND A.ufOrg = 'SP') THEN A.vlIcmsSt ELSE 0 END
      ELSE 0 END AS vl_icmsstSP_DFe,
      CASE WHEN B.tp_origem = 'EFD' THEN
        CASE WHEN (A.indEmit = 0 AND A.ufDest = 'SP') OR (A.indEmit = 1 AND A.ufOrg = 'SP') THEN A.vlIcmsSt ELSE 0 END
      ELSE 0 END AS vl_icmsstSP_EFD,
      CASE WHEN B.tp_origem = 'DFe' THEN
        CASE WHEN (A.indEmit = 0 AND A.ufDest <> 'SP') OR (A.indEmit = 1 AND A.ufOrg <> 'SP') THEN A.vlIcmsSt ELSE 0 END
      ELSE 0 END AS vl_icmsstUFs_DFe,
      CASE WHEN B.tp_origem = 'EFD' THEN
        CASE WHEN (A.indEmit = 0 AND A.ufDest <> 'SP') OR (A.indEmit = 1 AND A.ufOrg <> 'SP') THEN A.vlIcmsSt ELSE 0 END
      ELSE 0 END AS vl_icmsstUFs_EFD
      FROM osf.DocAtrib_fiscal_DocAtributos AS A
      LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos) AS SqA
    GROUP BY SqA.chave, SqA.numero) AS SqB
    LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS DA_Efd ON DA_Efd.idDocAtributos = SqB.EFD_idDocAtributos
    LEFT OUTER JOIN docAtribTudao AS DA_EfdT ON DA_EfdT.idDocAtributos = DA_Efd.idDocAtributos
    LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS DA_DFe ON DA_DFe.idDocAtributos = SqB.DFe_idDocAtributos
    LEFT OUTER JOIN docAtribTudao AS DA_DFeT ON DA_DFeT.idDocAtributos = DA_DFe.idDocAtributos
    LEFT OUTER JOIN idDocAtributos_efdPart AS Efd_Part  ON Efd_Part.idDocAtributos  = SqB.DFe_idDocAtributos
    LEFT OUTER JOIN idDocAtributos_chaveObs AS CO_NFe   ON CO_NFe.idDocAtributos    = SqB.DFe_idDocAtributos
    ORDER BY SqB.tp_codSit, SqB.indEmit, dif_vl_doc DESC;

    CREATE INDEX IF NOT EXISTS chaveNroTudao_chave ON chaveNroTudao (chave);

    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_NfeC209_idNfeC200 ON dfe_fiscal_NfeC209 (idNfeC200);
    CREATE INDEX IF NOT EXISTS osf.dfe_fiscal_NfeC211_idNfeC200 ON dfe_fiscal_NfeC211 (idNfeC200);
    CREATE INDEX IF NOT EXISTS osf._fiscal_EfdSat_idEfdSat ON _fiscal_EfdSat (idEfdC800);

    CREATE TABLE main.entsaicnpj AS
    SELECT substr(B.Part, 1, 14) AS cnpjPart,  sum(AO.valorDaOperacao) AS valorDaOperacao
      FROM osf.DocAtrib_fiscal_DocAtributosDeApuracao AS AO
      LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AO.idDocAtributos
      LEFT OUTER JOIN docAtribTudao AS B ON B.idDocAtributos = A.idDocAtributos
      LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CAST(AO.cfop AS INT)
      WHERE B.tp_origem = 'EFD' AND A.codSit NOT IN (2, 4, 5) AND g1 = '5-Entradas/Saídas' AND g2 = '01z - Produção - Outros'
      GROUP BY cnpjPart
      ORDER BY valorDaOperacao DESC;

    CREATE INDEX IF NOT EXISTS entsaicnpj_cnpjPart ON entsaicnpj (cnpjPart);

    CREATE TABLE main.an_econ_base AS
    SELECT
      B.tp_origem, A.codSit, A.indEmit, A.indOper,
      substr(B.Part, 1, 14) AS cnpjPart14, ESCT.rowid AS cnpjOrder,
      coalesce(B.Part, '') || ' ' || coalesce(B.SituacaoPart, '') || ' ' || coalesce(B.dtinifimSitPart, '') || ' ' || coalesce(B.regPart, '') || ' ' || coalesce(B.dtinifimRegPart, '') AS Part,
      CASE WHEN B.tp_origem = 'EFD' THEN A.dtEntSd ELSE '0000-00-00' END AS dtaEFD,
      CASE WHEN B.tp_origem = 'DFe' THEN A.dtEmissao ELSE '0000-00-00' END AS dtaDFe,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'EFD' THEN -AO.valorDaOperacao WHEN B.tp_origem = 'EFD' THEN AO.valorDaOperacao ELSE 0 END AS es_valconEFD,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'EFD' THEN -AO.bcIcmsOpPropria WHEN B.tp_origem = 'EFD' THEN AO.bcIcmsOpPropria ELSE 0 END AS es_bcicmsEFD,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'EFD' THEN -AO.icmsProprio WHEN B.tp_origem = 'EFD' THEN AO.icmsProprio ELSE 0 END AS es_icmsEFD,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'EFD' THEN -AO.bcIcmsSt WHEN B.tp_origem = 'EFD' THEN AO.bcIcmsSt ELSE 0 END AS es_bcicmsstEFD,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'EFD' THEN -AO.icmsSt WHEN B.tp_origem = 'EFD' THEN AO.icmsSt ELSE 0 END AS es_icmsstEFD,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'DFe' THEN -AO.valorDaOperacao WHEN B.tp_origem = 'DFe' THEN AO.valorDaOperacao ELSE 0 END AS es_valconDFe,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'DFe' THEN -AO.bcIcmsOpPropria WHEN B.tp_origem = 'DFe' THEN AO.bcIcmsOpPropria ELSE 0 END AS es_bcicmsDFe,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'DFe' THEN -AO.icmsProprio WHEN B.tp_origem = 'DFe' THEN AO.icmsProprio ELSE 0 END AS es_icmsDFe,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'DFe' THEN -AO.bcIcmsSt WHEN B.tp_origem = 'DFe' THEN AO.bcIcmsSt ELSE 0 END AS es_bcicmsstDFe,
      CASE WHEN EI.cfop < 5000 AND B.tp_origem = 'DFe' THEN -AO.icmsSt WHEN B.tp_origem = 'DFe' THEN AO.icmsSt ELSE 0 END AS es_icmsstDFe,
      EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif
    FROM osf.DocAtrib_fiscal_DocAtributosDeApuracao AS AO
      LEFT OUTER JOIN osf.DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AO.idDocAtributos
      LEFT OUTER JOIN docAtribTudao AS B ON B.idDocAtributos = A.idDocAtributos
      LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AO.cfop AS INT)
      LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AO.cfop AS INT) END
      LEFT OUTER JOIN entsaicnpj AS ESCT ON ESCT.cnpjPart = cnpjPart14
    WHERE A.codSit NOT IN (2, 3, 4, 5);

    CREATE INDEX IF NOT EXISTS osf._fiscal_Classificacao_idClassificacao ON _fiscal_Classificacao (idClassificacao ASC);
    CREATE INDEX IF NOT EXISTS osf._fiscal_ParamConsultaDocClassificacao_idClassificacao ON _fiscal_ParamConsultaDocClassificacao (idClassificacao ASC);
    CREATE INDEX IF NOT EXISTS osf._fiscal_ParamConsultaDoc_idParamConsultaDoc ON _fiscal_ParamConsultaDoc (idParamConsultaDoc ASC);
    """
    
    cursor.executescript(sql_script)

    print(" ➔ Criando Índices Complementares (Aceleração)...")
    SQL_INDEXES = """
    CREATE INDEX IF NOT EXISTS osf.idx_EfdC100_idEfd0150 ON dfe_fiscal_EfdC100(idEfd0150);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdC100_idEfdC100 ON dfe_fiscal_EfdC100(idEfdC100);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdC100Detalhe_idEfdC100 ON dfe_fiscal_EfdC100Detalhe(idEfdC100);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdC170_idEfdC100 ON dfe_fiscal_EfdC170(idEfdC100);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdC170_COD_ITEM_idArquivo ON _fiscal_efd0200(COD_ITEM, idArquivo);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdD100Detalhe_idEfdD100 ON dfe_fiscal_EfdD100Detalhe(idEfdD100);
    CREATE INDEX IF NOT EXISTS osf.idx_EfdG125_idEfdG110 ON Dfe_fiscal_EfdG125(idEfdG110);
    CREATE INDEX IF NOT EXISTS osf.idx_NfeC100_idNfeC100 ON dfe_fiscal_NfeC100(idNfeC100);
    CREATE INDEX IF NOT EXISTS osf.idx_NfeC100Dest_CHV ON dfe_fiscal_NfeC100(CHV_NFE);
    CREATE INDEX IF NOT EXISTS osf.idx_NfeC170_idNfeC100 ON dfe_fiscal_NfeC170(idNfeC100);
    CREATE INDEX IF NOT EXISTS osf.idx_NfeC170InfProd_idC170 ON dfe_fiscal_NfeC170InfProd(idNFeC170);
    CREATE INDEX IF NOT EXISTS osf.idx_NfeC200_idNfeC200 ON dfe_fiscal_NfeC200(idNfeC200);
    CREATE INDEX IF NOT EXISTS osf.idx_DocAtributos_idDocAtributos ON DocAtrib_fiscal_DocAtributos(idDocAtributos);
    CREATE INDEX IF NOT EXISTS osf.idx_DocAtributosItem_idDocAtributos ON DocAtrib_fiscal_DocAtributosItem(idDocAtributos);
    """
    cursor.executescript(SQL_INDEXES)


    conn.commit()
    conn.close()