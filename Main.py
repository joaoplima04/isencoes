from functions import extrair_texto, extrair_salario_bruto, julga_salario_bruto, rotula_contracheque
from tqdm import tqdm
import pandas as pd

# Carrega a planilha
dados = pd.read_excel("C:\\Users\\João Lucas\\Downloads\\Teste isenções contracheche analisaveis"
                      ""
                      ".xlsx")

total_linhas = len(dados)

# Interage com cada linha da planilha atravéz de um for e insere uma barra de progresso para visualizar o andamento da anáise
for indice, linha in tqdm(dados.iterrows(), total=dados.shape[0]):
    contracheque_1 = linha['B.1) Contracheque 1 - Contracheque/comprovante de pagamento do examinando']
    contracheque_2 = linha['B.2) Contracheque 2 - Contracheque/comprovante de pagamento do examinando']
    contracheque_3 = linha['B.3) Contracheque 3 - Contracheque/comprovante de pagamento do examinando']
    contracheques = [contracheque_1, contracheque_2, contracheque_3]
    decisao = ""
    texto_contracheque = ""
    count = 0
    for contracheque in contracheques:
        try:
            texto_contracheque = extrair_texto(contracheque)
        except Exception as erro:
            print(f"Não foi possível analizar o contracheque pelo seguinte erro: {erro}")
        if rotula_contracheque(texto_contracheque) != "Contracheque" and rotula_contracheque(
                texto_contracheque) != "Inválido":
            break
        salario = extrair_salario_bruto(texto_contracheque)
        if rotula_contracheque(texto_contracheque) == "Inválido":
            decisao = "alínea \"b\";"
            break
        if julga_salario_bruto(salario, texto_contracheque):
            decisao = "2.6.1, alínea \"b\";"
            break
    if rotula_contracheque(texto_contracheque) == "Contracheque" and decisao == "":
        decisao = "DEFERIDO"

    dados.loc[indice, 'Análise programa'] = decisao

dados.to_excel('Teste contracheque (parte) saída.xlsx', index=False)