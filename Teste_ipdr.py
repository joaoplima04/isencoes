from functions import extrair_texto, extrair_imposto_de_renda, julga_imposto_de_renda, rotula_imposto_de_renda
from tqdm import tqdm
import pandas as pd

dados = pd.read_excel("C:\\Users\\João Lucas\\Downloads\\Teste imposto de renda.xlsx")

total_linhas = len(dados)
for indice, linha in tqdm(dados.iterrows(), total=dados.shape[0]):
    url_imposto_de_renda = linha['C) Declaração do imposto de renda do examinando']
    decisao = ""
    texto_ipr = ""
    count = 0
    try:
        texto_ipr = extrair_texto(url_imposto_de_renda)
    except Exception as erro:
        print(f"Não foi possível analizar o contracheque pelo seguinte erro: {erro}")
    if rotula_imposto_de_renda(texto_ipr) == "Inválido":
        decisao = "alínea \"c\";"
    if rotula_imposto_de_renda(texto_ipr) != "Contracheque" and rotula_imposto_de_renda(texto_ipr) != "Inválido":
        decisao = ""
    if rotula_imposto_de_renda(texto_ipr) == "Imposto de Renda":
        imposto_de_renda = extrair_imposto_de_renda(texto_ipr)
        if julga_imposto_de_renda(imposto_de_renda):
            decisao = "2.6.1, alínea \"b\";"
    if decisao == "" and rotula_imposto_de_renda(texto_ipr) == "Imposto de Renda":
        decisao = "DEFERIDO"

    dados.loc[indice, 'Análise programa'] = decisao

dados.to_excel('Teste imposto de renda (saída).xlsx', index=False)