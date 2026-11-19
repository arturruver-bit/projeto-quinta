# -*- coding: utf-8 -*-
"""
Trabalho T3 - Ciência de Dados Aplicada à Saúde Pública
Análise de Dados do SIASUS para Apoio à Gestão Municipal de Saúde de Ijuí/RS
Autores: Equipe de Ciência de Dados
Disciplina: Programação para Ciência de Dados
"""

import os
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    print("=" * 70)
    print("  T3 - ANÁLISE DE DADOS DO SIASUS (IJUÍ / RS) - ETAPAS 2 E 3")
    print("=" * 70)

    # Diretório para salvar as imagens dos gráficos
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Conexão com o Banco de Dados MySQL
    print("\n[1/6] Conectando ao MySQL e carregando a VIEW 'pa_ijui'...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="dbsia"
    )

    query = "SELECT * FROM pa_ijui;"
    tabela = pd.read_sql(query, conn)
    conn.close()

    print(f" -> Sucesso: {len(tabela):,} registros e {tabela.shape[1]} colunas carregadas.")

    # 2. Preparação e Limpeza de Dados
    print("\n[2/6] Preparando tipos de dados e avaliando consistência...")
    colunas_numericas = ["pa_qtdpro", "pa_qtdapr", "pa_valpro", "pa_valapr"]
    for col in colunas_numericas:
        tabela[col] = pd.to_numeric(tabela[col], errors="coerce").fillna(0)

    tabela["pa_idade_num"] = pd.to_numeric(tabela["pa_idade"], errors="coerce")

    # Configuração de estilo dos gráficos
    sns.set_theme(style="darkgrid")
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'

    # Indicadores Gerais
    q_pro = tabela["pa_qtdpro"].sum()
    q_apr = tabela["pa_qtdapr"].sum()
    v_pro = tabela["pa_valpro"].sum()
    v_apr = tabela["pa_valapr"].sum()
    glosa_val = v_pro - v_apr

    print("\n" + "=" * 50)
    print("      INDICADORES GERAIS DA PRODUÇÃO AMBULATORIAL")
    print("=" * 50)
    print(f"Total de Registros:               {len(tabela):,}")
    print(f"Qtd. Procedimentos Apresentados:  {q_pro:,.0f}")
    print(f"Qtd. Procedimentos Aprovados:     {q_apr:,.0f} ({q_apr/q_pro*100:.2f}%)")
    print(f"Valor Apresentado:                R$ {v_pro:,.2f}")
    print(f"Valor Aprovado (SUS):             R$ {v_apr:,.2f} ({v_apr/v_pro*100:.2f}%)")
    print(f"Glosa Financeira (Diferença):     R$ {glosa_val:,.2f}")
    print(f"Custo Médio / Procedimento:       R$ {v_apr/q_apr:.2f}")

    # -------------------------------------------------------------
    # GRÁFICO 1: Avaliação da Qualidade dos Dados (Valores Ausentes)
    # -------------------------------------------------------------
    print("\n[3/6] Gerando visualizações descritivas e demográficas...")
    nulos = tabela.isna().sum().sort_values(ascending=False)
    dados_nulos = nulos[nulos > 0].sort_values()

    if len(dados_nulos) > 0:
        plt.figure(figsize=(10, 5))
        dados_nulos.plot(kind="barh", color="#4C72B0")
        plt.title("Valores Ausentes por Atributo - SIASUS Ijuí/RS", fontsize=14, fontweight="bold")
        plt.xlabel("Quantidade de Registros Ausentes", fontsize=11)
        plt.ylabel("Atributo", fontsize=11)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "01_valores_ausentes.png"), dpi=300)
        plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 2: Comparativo Apresentado x Aprovado (Qtd e Valor)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    df_qtd = pd.DataFrame({"Quantidade": [q_pro, q_apr]}, index=["Apresentada", "Aprovada"])
    df_qtd.plot(kind="bar", ax=axes[0], color=["#4C72B0", "#55A868"], legend=False)
    axes[0].set_title("Quantidade de Procedimentos", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("Quantidade", fontsize=11)
    for i, v in enumerate(df_qtd["Quantidade"]):
        axes[0].text(i, v * 1.01, f"{v:,.0f}".replace(",", "."), ha="center", fontweight="bold")

    df_val = pd.DataFrame({"Valor (R$)": [v_pro, v_apr]}, index=["Apresentado", "Aprovado"])
    df_val.plot(kind="bar", ax=axes[1], color=["#E24A33", "#348ABD"], legend=False)
    axes[1].set_title("Valores Financeiros (R$)", fontsize=13, fontweight="bold")
    axes[1].set_ylabel("Valor em R$", fontsize=11)
    for i, v in enumerate(df_val["Valor (R$)"]):
        axes[1].text(i, v * 1.01, f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ha="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "02_indicadores_gerais.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 3: Evolução Mensal
    # -------------------------------------------------------------
    mensal = tabela.groupby(["Ano", "Mes"], dropna=False, as_index=False).agg(
        Registros=("Procedimento", "size"),
        QuantidadeApresentada=("pa_qtdpro", "sum"),
        QuantidadeAprovada=("pa_qtdapr", "sum"),
        ValorApresentado=("pa_valpro", "sum"),
        ValorAprovado=("pa_valapr", "sum")
    ).sort_values(["Ano", "Mes"])

    plt.figure(figsize=(10, 5))
    plt.plot(mensal["Mes"].astype(str), mensal["QuantidadeApresentada"], marker="o", linestyle="--", color="#4C72B0", label="Apresentada", linewidth=2)
    plt.plot(mensal["Mes"].astype(str), mensal["QuantidadeAprovada"], marker="s", linestyle="-", color="#55A868", label="Aprovada", linewidth=2)
    plt.title("Evolução Mensal da Produção Ambulatorial", fontsize=14, fontweight="bold")
    plt.xlabel("Mês de Competência", fontsize=11)
    plt.ylabel("Quantidade de Procedimentos", fontsize=11)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "03_evolucao_mensal.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 4: Produção por Estabelecimento de Saúde
    # -------------------------------------------------------------
    print("\n[4/6] Gerando análises de estabelecimentos e procedimentos...")
    estab = tabela.groupby("Estabelecimento", dropna=False, as_index=False).agg(
        Registros=("Procedimento", "size"),
        QuantidadeApresentada=("pa_qtdpro", "sum"),
        QuantidadeAprovada=("pa_qtdapr", "sum"),
        ValorAprovado=("pa_valapr", "sum")
    )
    estab["Diferenca"] = estab["QuantidadeApresentada"] - estab["QuantidadeAprovada"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    top_estab_apr = estab.nlargest(10, "QuantidadeAprovada").sort_values("QuantidadeAprovada", ascending=True)
    top_estab_apr.plot(x="Estabelecimento", y="QuantidadeAprovada", kind="barh", ax=axes[0], color="#4C72B0", legend=False)
    axes[0].set_title("10 Maiores Estabelecimentos por Produção Aprovada", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Quantidade Aprovada", fontsize=11)

    top_estab_dif = estab.nlargest(10, "Diferenca").sort_values("Diferenca", ascending=True)
    top_estab_dif.plot(x="Estabelecimento", y="Diferenca", kind="barh", ax=axes[1], color="#C44E52", legend=False)
    axes[1].set_title("10 Maiores Diferenças (Apresentada - Aprovada)", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Diferença de Procedimentos", fontsize=11)
    axes[1].set_ylabel("")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "04_producao_estabelecimentos.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 5: Procedimentos e Ocupações Mais Frequentes
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    top_proc = tabela.groupby("Procedimento")["pa_qtdapr"].sum().nlargest(10).sort_values(ascending=True)
    top_proc.plot(kind="barh", ax=axes[0], color="#55A868")
    axes[0].set_title("Top 10 Procedimentos com Maior Produção Aprovada", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Quantidade Aprovada", fontsize=11)

    top_ocup = tabela.groupby("Ocupacao")["pa_qtdapr"].sum().nlargest(10).sort_values(ascending=True)
    top_ocup.plot(kind="barh", ax=axes[1], color="#8172B2")
    axes[1].set_title("Top 10 Ocupações Profissionais", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Quantidade Aprovada", fontsize=11)
    axes[1].set_ylabel("")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "05_procedimentos_ocupacoes.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 6: Perfil Demográfico (Sexo e Idade)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    tabela["pa_sexo"].value_counts().plot(kind="bar", ax=axes[0], color=["#4C72B0", "#DD8452"])
    axes[0].set_title("Distribuição dos Registros por Sexo", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Sexo", fontsize=11)
    axes[0].set_ylabel("Quantidade de Registros", fontsize=11)

    idades_validas = tabela["pa_idade_num"][tabela["pa_idade_num"].between(0, 120)]
    idades_validas.plot(kind="hist", bins=15, ax=axes[1], color="#55A868", edgecolor="black")
    axes[1].set_title("Distribuição da Idade dos Pacientes", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Idade (anos)", fontsize=11)
    axes[1].set_ylabel("Quantidade de Registros", fontsize=11)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "06_demografia_sexo_idade.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 7: Heatmap Faixa Etária x Sexo
    # -------------------------------------------------------------
    faixas = pd.cut(
        tabela["pa_idade_num"],
        bins=[-1, 17, 39, 59, 79, 120],
        labels=["0-17", "18-39", "40-59", "60-79", "80+"]
    )
    matriz_faixa_sexo = pd.crosstab(faixas, tabela["pa_sexo"])

    plt.figure(figsize=(8, 6))
    sns.heatmap(matriz_faixa_sexo, annot=True, fmt="d", cmap="Blues", cbar=True)
    plt.title("Distribuição de Registros: Faixa Etária × Sexo", fontsize=14, fontweight="bold")
    plt.xlabel("Sexo", fontsize=11)
    plt.ylabel("Faixa Etária", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "07_heatmap_faixa_sexo.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 8: Diagnósticos Mais Frequentes (CID-10)
    # -------------------------------------------------------------
    dados_cid = tabela[tabela["pa_cidpri"].notna() & ~tabela["pa_cidpri"].isin(["", "0000", "00000"])]
    top_cid = dados_cid["Diagnostico"].value_counts().head(10).sort_values(ascending=True)

    plt.figure(figsize=(11, 6))
    top_cid.plot(kind="barh", color="#64B5CD")
    plt.title("Top 10 Diagnósticos Principais (CID-10)", fontsize=14, fontweight="bold")
    plt.xlabel("Quantidade de Registros", fontsize=11)
    plt.ylabel("Diagnóstico", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "08_top_diagnosticos_cid.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 9: Fluxos Regionais (Município de Origem)
    # -------------------------------------------------------------
    print("\n[5/6] Gerando análises de fluxos regionais e áreas críticas...")
    mun_pac = tabela["MunicipioPaciente"].value_counts()
    top_mun = mun_pac.head(10).sort_values(ascending=True)

    plt.figure(figsize=(10, 6))
    top_mun.plot(kind="barh", color="#CCB974")
    plt.title("Top 10 Municípios de Residência dos Pacientes Atendidos em Ijuí", fontsize=14, fontweight="bold")
    plt.xlabel("Quantidade de Registros", fontsize=11)
    plt.ylabel("Município do Paciente", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "09_fluxos_regionais_municipios.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # GRÁFICO 10: Foco em Áreas Críticas (Oncologia, Saúde Mental, Atenção Básica)
    # -------------------------------------------------------------
    onco_mask = tabela["Procedimento"].str.contains("ONCO|QUIMIO|RADIO|TUMOR|NEOPLAS", case=False, na=False) | tabela["pa_cidpri"].str.startswith("C", na=False)
    sm_mask = tabela["Procedimento"].str.contains("PSIC|MENTAL|PSIQUIAT|CAPS", case=False, na=False) | tabela["pa_cidpri"].str.startswith("F", na=False)
    ab_mask = tabela["Procedimento"].str.contains("BASICA|CONSULTA EM ATENCAO BASICA|ACOLHIMENTO|DOMICILIAR|VISITA", case=False, na=False) | tabela["Estabelecimento"].str.contains("UBS|ESF|POSTO|CENTRO DE SAUDE|ESTRATEGIA", case=False, na=False)

    areas_criticas = pd.DataFrame({
        "Área": ["Oncologia", "Saúde Mental", "Atenção Básica"],
        "Registros": [onco_mask.sum(), sm_mask.sum(), ab_mask.sum()],
        "QtdApresentada": [tabela.loc[onco_mask, "pa_qtdpro"].sum(), tabela.loc[sm_mask, "pa_qtdpro"].sum(), tabela.loc[ab_mask, "pa_qtdpro"].sum()],
        "QtdAprovada": [tabela.loc[onco_mask, "pa_qtdapr"].sum(), tabela.loc[sm_mask, "pa_qtdapr"].sum(), tabela.loc[ab_mask, "pa_qtdapr"].sum()],
        "ValorAprovado": [tabela.loc[onco_mask, "pa_valapr"].sum(), tabela.loc[sm_mask, "pa_valapr"].sum(), tabela.loc[ab_mask, "pa_valapr"].sum()]
    })

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    areas_criticas.plot(x="Área", y=["QtdApresentada", "QtdAprovada"], kind="bar", ax=axes[0], color=["#4C72B0", "#55A868"])
    axes[0].set_title("Produção em Áreas Críticas (Procedimentos)", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("Quantidade", fontsize=11)
    axes[0].set_xticklabels(areas_criticas["Área"], rotation=0)

    areas_criticas.plot(x="Área", y="ValorAprovado", kind="bar", ax=axes[1], color="#C44E52", legend=False)
    axes[1].set_title("Recursos Financeiros Aprovados (R$)", fontsize=13, fontweight="bold")
    axes[1].set_ylabel("Valor em R$", fontsize=11)
    axes[1].set_xticklabels(areas_criticas["Área"], rotation=0)
    for i, v in enumerate(areas_criticas["ValorAprovado"]):
        axes[1].text(i, v * 1.01, f"R$ {v:,.0f}".replace(",", "."), ha="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "10_areas_criticas.png"), dpi=300)
    plt.close()

    print("\n[6/6] Finalizado com sucesso! Todos os 10 gráficos foram salvos em:")
    print(f" -> {output_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
