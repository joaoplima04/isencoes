from functions import extrair_texto, extrai_numero_de_paginas, extrair_imposto_de_renda, extrair_salario_bruto, extrair_mes_ano, verifica_meses_iguais, rotula_imposto_de_renda,\
    rotula_contracheque, julga_imposto_de_renda, julga_salario_bruto
from tqdm import tqdm
import pandas as pd

dados = pd.read_excel("C:\\Users\\João Lucas\\Downloads\\Teste Uni analizáveis após alterações (entrada).xlsx")

total_linhas = len(dados)

for indice, linha in tqdm(dados.iterrows(), total=dados.shape[0]):
    contracheque_1 = linha['B.1) Contracheque 1 - Contracheque/comprovante de pagamento do examinando']
    contracheque_2 = linha['B.2) Contracheque 2 - Contracheque/comprovante de pagamento do examinando']
    contracheque_3 = linha['B.3) Contracheque 3 - Contracheque/comprovante de pagamento do examinando']
    contracheques = [contracheque_1, contracheque_2, contracheque_3]
    decisao_contracheque = ""
    texto_contracheque = ""
    count = 0
    datas = []
    for url_contracheque in contracheques:
        try:
            texto_contracheque = extrair_texto(url_contracheque)
            quantidade_pag = extrai_numero_de_paginas(url_contracheque)
            data = extrair_mes_ano(texto_contracheque)
            datas.append(data)
        except Exception as erro:
            print(f"Não foi possível analizar o contracheque pelo seguinte erro: {erro}")
        if rotula_contracheque(texto_contracheque, quantidade_pag) != "Contracheque" and rotula_contracheque(
                texto_contracheque, quantidade_pag) != "Inválido":
            break
        salario = extrair_salario_bruto(texto_contracheque)
        if rotula_contracheque(texto_contracheque, quantidade_pag) == "Inválido":
            decisao_contracheque = "alínea \"b\";"
            break
        if julga_salario_bruto(salario, texto_contracheque):
            decisao_contracheque = "2.6.1, alínea \"b\";"
            break
    if verifica_meses_iguais(datas):
        decisao_contracheque = "alínea \"b\";"
    if rotula_contracheque(texto_contracheque, quantidade_pag) == "Contracheque" and decisao_contracheque == "":
        decisao_contracheque = "DEFERIDO"

    dados.loc[indice, 'Análise Programa (Contracheque)'] = decisao_contracheque

    if decisao_contracheque == "" or decisao_contracheque == "DEFERIDO":
        url_imposto_de_renda = linha['C) Declaração do imposto de renda do examinando']
        decisao_ipr = ""
        texto_ipr = ""
        count = 0
        try:
            texto_ipr = extrair_texto(url_imposto_de_renda)
            quantidade_pag_ipdr = extrai_numero_de_paginas(url_imposto_de_renda)
        except Exception as erro:
            print(f"Não foi possível analizar o imposto de renda pelo seguinte erro: {erro}")
        if rotula_imposto_de_renda(texto_ipr, quantidade_pag_ipdr) == "Inválido":
            decisao_ipr = "alínea \"c\";"
        if rotula_imposto_de_renda(texto_ipr, quantidade_pag_ipdr) != "Imposto de Renda" and rotula_imposto_de_renda(texto_ipr, quantidade_pag_ipdr) != "Inválido":
            decisao_ipr = ""
        if rotula_imposto_de_renda(texto_ipr, quantidade_pag_ipdr) == "Imposto de Renda":
            imposto_de_renda = extrair_imposto_de_renda(texto_ipr)
            if julga_imposto_de_renda(imposto_de_renda):
                decisao_ipr = "2.6.1, alínea \"b\";"
        if decisao_ipr == "" and rotula_imposto_de_renda(texto_ipr, quantidade_pag_ipdr) == "Imposto de Renda":
            decisao_ipr = "DEFERIDO"
        dados.loc[indice, 'Análise Programa (Imposto de Renda)'] = decisao_ipr

dados.to_excel('Teste Uni (inteiro) analizáveis saída.xlsx', index=False)
