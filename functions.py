import re
from datetime import datetime, timedelta
import requests
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import os
import tempfile
import cv2
import numpy as np


def preprocess_image(img):
    # Aplique técnicas de pré-processamento, como binarização e remoção de ruído
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    return img


def extract_text_from_image(img):
    # Use Tesseract para extrair texto da imagem
    return pytesseract.image_to_string(img, lang='por')


def extrair_texto(url):
    text = ""

    if url.endswith(".pdf"):
        response = requests.get(url)
        pdf_content = BytesIO(response.content)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content.getvalue())
            temp_filename = temp_file.name

        try:
            doc = fitz.open(temp_filename)
            for page_number in range(doc.page_count):
                page = doc[page_number]
                page_text = page.get_text("text")
                numero_linhas = page_text.count('\n')

                if not page_text.strip() or numero_linhas < 5:
                    image = page.get_pixmap()
                    image_path = f"temp_image_page_{page_number + 1}.png"
                    image.save(image_path)
                    img = cv2.imread(image_path)
                    img = preprocess_image(img)
                    page_text = extract_text_from_image(img)
                    os.remove(image_path)

                text += page_text + " "

            doc.close()
        except Exception as e:
            print(f"Erro ao processar o PDF: {e}")
        finally:
            os.remove(temp_filename)

    elif url.endswith((".jpg", ".jpeg")):
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img = preprocess_image(img)
        text = extract_text_from_image(img)

    text = text.replace("\n", " ")
    text = text.replace("R$", "")
    return text.lower()


def extrai_numero_de_paginas(url):
    if url.endswith(".pdf"):
        # Baixar o conteúdo do PDF
        response = requests.get(url)
        pdf_content = BytesIO(response.content)
        # Salvar o conteúdo do PDF em um arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content.getvalue())
            temp_filename = temp_file.name
        # Criar um objeto de documento PDF
        try:
            doc = fitz.open(temp_filename)
        except TypeError as e:
            print(f"Erro ao processar a imagem: {e}")
        return doc.page_count


def rotula_contracheque(text, numero_paginas):
    if "instituto nacional do seguro social" in text or "cadastro nacional de informações sociais" in text:
        return "Contracheque"
    elif any(keyword in text for keyword in ["imposto sobre a renda", "imposto de renda"]):
        return "Inválido"
    elif "anexo" in text or "declaração" in text:
        return "Declaração"
    elif "extrato financeiro de estágio" in text or "proventos" in text or "descontos" in text or "valor bruto" in text or "salário base" in text:
        return "Contracheque"
    elif any(keyword in text for keyword in ["carteira de trabalho digital", "nota fiscal",
                                             "informações cadastrais da familia",
                                             "carteira de trabalho digital",
                                             "comprovante de transferência", "tipo de admissão",
                                             "termo de recisão de contrato de trabalho", "entrada conta corrente",
                                             "imposto de renda", "mobile banking", "meu nis",
                                             "termo de recisão do contrato de trabalho",
                                             "termo de homologação de recisão de contato de trabalho", "comprovante pix", "pix recebimento"]):
        return "Inválido"
    elif ("comprovante de cadastro" in text or "comprovante de situação cadastral no cpf" in text or "cadastro único" in text or "cadastro unico" in text or "extrato" in text)\
            and (numero_paginas == 1 or numero_paginas is None):
        return "Inválido"
    elif any(keyword in text for keyword in ["provento", "folha mensal", "vencimentos", "descontos",
                                             "líquido", "bolsa auxilio", "recibo de pagamento de salário", "demonstrativo pagamento"]):
        return "Contracheque"
    elif "carteira de trabalho" in text:
        return "Carteira de Trabalho"
    else:
        return "Não é possível analisar este arquivo"


def rotula_imposto_de_renda(text, numero_paginas):
    if "edital complementar" in text or "edital de abertura" in text or "conselho federal" in text or\
            "declaração de isenção do imposto de renda pessoa física" in text:
        return "Declaração"
    elif "imposto sobre a renda retido na fonte" in text or\
            "não consta entrega de declaração para este ano" in text or "vencimentos" in text or\
            "certidão negativa de débitos" in text or\
            "cópia para simples conferência" in text or\
            "declaração anual do simei" in text or "situação da declaração" in text or\
            "não consta entrega de declarações" in text or "não consta entrega de declaração este ano" in text or\
            "não há informação para o exercício informado" in text or\
            "não há informe de rendimentos de benefícios" in text or\
            "sua declaração não consta na base de dados da receita federal" in text or\
            "termo de recisão do contrato de trabalho" in text:
        return "Inválido"
    elif numero_paginas == 1 and ("comprovante de cadastro" in text or "comprovante de situação cadastral no cpf" in text or
                                  "cadastro único" in text or "o número do recibo de sua declaração apresentada" in text):
        return "Inválido"
    elif "imposto sobre a renda" in text:
        if "exercício 2022" in text:
            return "Inválido"
        elif "exercício 2023" not in text and "exercício 2022" not in text:
            return "Não é possível analizar este arquivo"
        else:
            return "Imposto de Renda"
    else:
        return "Não é possível analizar este arquivo"


def extrair_salario_bruto(texto):
    salario_bruto = 0
    # Encontrar todas as ocorrências de números no texto
    numeros = re.findall(r'(?<= )\d+\.\d+,\d+(?= )', texto)
    if numeros:
        # Remover pontos, substituir vírgulas por pontos e converter para floats
        numeros_floats = [float(num.replace('.', '').replace(',', '.')) for num in numeros]

        # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
        if numeros_floats:
            salario_bruto = max(numeros_floats)
            if salario_bruto > 15000:
                numeros_floats = sorted(numeros_floats, reverse=True)
                if len(numeros_floats) >= 2:
                    salario_bruto = numeros_floats[1]
    else:
        numeros_2 = re.findall(r'(?<= )\d+,\d+\.\d+(?= )', texto)
        if numeros_2:
            # Remover pontos, substituir vírgulas por pontos e converter para floats
            numeros_floats = [float(num.replace(',', '')) for num in numeros_2]

            # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
            if numeros_floats:
                salario_bruto = max(numeros_floats)
                if salario_bruto > 15000:
                    numeros_floats = sorted(numeros_floats, reverse=True)
                    if len(numeros_floats) >= 2:
                        salario_bruto = numeros_floats[1]
        else:
            numeros_3 = re.findall(r'(?<= )\d+,\d+,\d(?= )', texto)
            print(f"encontrou: {numeros_3}")
            if numeros_3:

                numeros_floats = [float(num.replace(',', '', 1).replace(',', '.')) for num in numeros_3]

                # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
                if numeros_floats:
                    salario_bruto = max(numeros_floats)
                    if salario_bruto > 15000:
                        numeros_floats = sorted(numeros_floats, reverse=True)
                        if len(numeros_floats) >= 2:
                            salario_bruto = numeros_floats[1]
            else:
                numeros_4 = re.findall(r'(?<= )\d+\.\d+(?= )', texto)
                if numeros_4:
                    # Remover pontos, substituir vírgulas por pontos e converter para floats
                    numeros_floats = [float(num.replace(',', '.')) for num in numeros_4]

                    # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
                    if numeros_floats:
                        salario_bruto = max(numeros_floats)
                        if salario_bruto > 15000:
                            numeros_floats = sorted(numeros_floats, reverse=True)
                            if len(numeros_floats) >= 2:
                                salario_bruto = numeros_floats[1]
                else:
                    numeros_5 = re.findall(r'\b\d+\.\d+,\d+\b', texto)
                    if numeros_5:
                        # Remover pontos, substituir vírgulas por pontos e converter para floats
                        numeros_floats = [float(num.replace('.', '').replace(',', '.')) for num in numeros_5]

                        # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
                        if numeros_floats:
                            salario_bruto = max(numeros_floats)
                            if salario_bruto > 15000:
                                numeros_floats = sorted(numeros_floats, reverse=True)
                                if len(numeros_floats) >= 2:
                                    salario_bruto = numeros_floats[1]
                    else:
                        numeros_6 = re.findall(r'(?<= )\d+,\d+(?= )', texto)
                        if numeros_6:
                            # Remover pontos, substituir vírgulas por pontos e converter para floats
                            numeros_floats = [float(num.replace(',', '.')) for num in numeros_6]

                            # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
                            if numeros_floats:
                                salario_bruto = max(numeros_floats)
                                if salario_bruto > 15000:
                                    numeros_floats = sorted(numeros_floats, reverse=True)
                                    if len(numeros_floats) >= 2:
                                        salario_bruto = numeros_floats[1]
    return salario_bruto


def julga_salario_bruto(salario, texto):
    passou = False
    if salario != 0 and salario > 3960:
        passou = True
    if "férias" in texto or "recesso" in texto or "ferias" in texto or "repouso" in texto\
            or "adiantamento 13salario" in texto or "decimo-terceiro salario" in texto:
        passou = False
    return passou


def extrair_imposto_de_renda(texto):
    # Procurar a frase específica e extrair o valor associado
    match = re.search(r'rendimentos tributáveis e desconto simplificado[\s\S]*?(\d{1,3}(?:\.\d{3})*,\d+\b)', texto, re.IGNORECASE)

    imposto_de_renda = 0
    if match:
        # Extrair o valor da primeira captura
        valor_encontrado = match.group(1)

        # Remover pontos, substituir vírgulas por pontos e converter para float
        valor_float = float(valor_encontrado.replace('.', '').replace(',', '.'))

        imposto_de_renda = valor_float

    return imposto_de_renda


def julga_imposto_de_renda(imposto_de_renda):
    passou = False
    if imposto_de_renda != 0 and imposto_de_renda > 47000:
        passou = True
    return passou


def obter_numero_mes(mes):
    meses = {
        'Janeiro': 1,
        'Fevereiro': 2,
        'Março': 3,
        'Abril': 4,
        'Maio': 5,
        'Junho': 6,
        'Julho': 7,
        'Agosto': 8,
        'Setembro': 9,
        'Outubro': 10,
        'Novembro': 11,
        'Dezembro': 12,
        'Jan': 1,
        'Fev': 2,
        'Marc': 3,
        'Abr': 4,
        'Mai': 5,
        'Jun': 6,
        'Jul': 7,
        'Ago': 8,
        'Set': 9,
        'Out': 10,
        'Nov': 11,
        'Dez': 12
    }
    return meses.get(mes, 0)


def extrair_mes_ano(texto):
    padroes_data = [
        r'(?<![\d/])\b(0?[1-9]|1[0-2])/(20\d{2})\b',  # Padrão MM/AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro) / (20\d{2})\b',  # Padrão Mês / AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)/(20\d{2})\b',  # Padrão Mês/AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro) de (20\d{2})',  # Padrão Mês de AAAA
        r'\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez) (20\d{2})',  # Padrão Mês AAAA
        r'\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/(20\d{2})',  # Padrão Mês AAAA
        r'01/(0?[1-9]|10|11|12)/(20\d{2}) (a|à) (28|30|31)/(0?[1-9]|10|11|12)/(20\d{2})',  # Padrão MM/AAAA a MM/AAAA
        r'(?<![\d/])\b(0?[1-9]|1[0-2]) / (20\d{2})\b',  # Padrão MM / AAAA
        r'(?<![\d/])\b(0?[1-9]|1[0-2])-(20\d{2})\b',  # Padrão MM-AAAA
        r'(?<![\d/])\b(0?[1-9]|1[0-2])/ (20\d{2})\b',  # Padrão MM/ AAAA
    ]

    for padrao_data in padroes_data:
        resultado = re.search(padrao_data, texto)
        if resultado:
            if padrao_data == r'01/(0?[1-9]|10|11|12)/(20\d{2}) (a|à) (28|30|31)/(0?[1-9]|10|11|12)/(20\d{2})':
                _, _, _, _, mes, ano = resultado.groups()
                return datetime.strptime(f"{mes}/{ano}", "%m/%Y")
            else:
                mes, ano = resultado.groups()
                mes_transformado = obter_numero_mes(mes.capitalize())
                if mes_transformado == 0:
                    return datetime.strptime(f"{mes}/{ano}", "%m/%Y")
                else:
                    return datetime.strptime(f"{mes_transformado}/{ano}", "%m/%Y")

    return 0


def verifica_meses_iguais(datas):
    # Ordenar as datas por ordem crescente
    for data in datas:
        if data != 0:
            try:
                datas_ordenadas = sorted(datas)
                for i in range(len(datas_ordenadas) - 1):
                    if datas_ordenadas[i].month == datas_ordenadas[i + 1].month:
                        return True
            except Exception as e:
                print(f"Não foi possível ordenar as datas pelo seguinte erro: {e}")
        # Verificar se as datas são consecutivas
        return False


def testa_uni_contracheque(contracheques):
    decisao_contracheque = ""
    texto_contracheque = ""
    datas = []
    verify = 0
    count = 1
    quantidade_pag = 0
    for url_contracheque in contracheques:
        print(f"Contracheque {count}")
        count += 1
        try:
            texto_contracheque = extrair_texto(url_contracheque)
            quantidade_pag = extrai_numero_de_paginas(url_contracheque)
            data = extrair_mes_ano(texto_contracheque)
            print(data)
            datas.append(data)
        except Exception as erro:
            print(f"Não foi possível analizar o contracheque pelo seguinte erro: {erro}")
            break
        print(rotula_contracheque(texto_contracheque, quantidade_pag))
        if rotula_contracheque(texto_contracheque, quantidade_pag) != "Contracheque" and rotula_contracheque(
                texto_contracheque, quantidade_pag) != "Inválido":
            break
        salario = extrair_salario_bruto(texto_contracheque)
        print(f"salário = {salario}")
        if rotula_contracheque(texto_contracheque, quantidade_pag) == "Contracheque" and salario == 0 and count != 4:
            decisao_contracheque = ""
            print("Não foi possível extrair o salário")
            verify += 1
            break
        if rotula_contracheque(texto_contracheque, quantidade_pag) == "Inválido":
            print(rotula_contracheque(texto_contracheque, quantidade_pag), url_contracheque)
            decisao_contracheque = "alínea \"b\";"
            break
        if julga_salario_bruto(salario, texto_contracheque):
            decisao_contracheque = "2.6.1, alínea \"b\";"
            break
    if verifica_meses_iguais(datas):
        decisao_contracheque = "alínea \"b\";"
        print("Meses Iguais")
        print(datas)
    if rotula_contracheque(texto_contracheque, quantidade_pag) == "Contracheque" and decisao_contracheque == "" and verify == 0:
        decisao_contracheque = "DEFERIDO"

    return decisao_contracheque


