import re
from datetime import datetime, timedelta
import requests
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import os
import tempfile


def extrair_texto(url):
    text = ""
    # Verificar a extensão do arquivo na URL
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
            text = ""
        # Iterar pelas páginas do documento
        for page_number in range(doc.page_count):
            # Obter uma página específica
            page = doc[page_number]
            # Extrai o texto diretamente
            page_text = page.get_text("text")
            if not page_text.strip():
                # Converter a página para uma imagem
                image = page.get_pixmap()
                # Salvar a imagem temporariamente
                image_path = f"temp_image_page_{page_number + 1}.png"
                image.save(image_path)
                # Realizar OCR na imagem
                page_text = pytesseract.image_to_string(Image.open(image_path), lang='por')
                # Remover a imagem temporária
                os.remove(image_path)
            # Acumular o texto da página atual
            text += page_text + " "
        # Fechar o documento
        doc.close()
        # Remover o arquivo temporário do PDF
        os.remove(temp_filename)
    elif url.endswith((".jpg", ".jpeg")):
        # Baixar o conteúdo da imagem JPEG
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        # Realizar OCR na imagem
        try:
            text = pytesseract.image_to_string(image, lang='por')
        except TypeError as e:
            print(f"Erro ao processar a imagem: {e}")
            text = ""

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
    if "instituto nacional do seguro social" in text or "cadastro nacional de informações sociais":
        return "Contracheque"
    elif "anexo" in text or "declaração" in text:
        return "Declaração"
    elif "extrato financeiro de estágio" in text or "proventos" or "descontos":
        return "Contracheque"
    elif any(keyword in text for keyword in ["carteira de trabalho digital", "nota fiscal",
                                             "informações cadastrais da familia",
                                             "carteira de trabalho digital",
                                             "comprovante de trasferência", "tipo de admissão",
                                             "termo de recisão de contrato de trabalho", "entrada conta corrente",
                                             "imposto de renda", "mobile banking", "meu nis",
                                             "termo de recisão do contrato de trabalho",
                                             "termo de homologação de recisão de contato de trabalho"]):
        return "Inválido"
    elif ("comprovante de cadastro" in text or "comprovante de situação cadastral no cpf" or "extrato" in text)\
            and numero_paginas == 1:
        return "Inválido"
    elif any(keyword in text for keyword in ["proventos", "folha mensal", "vencimentos", "salário", "descontos",
                                             "líquido", "bolsa auxilio"]):
        return "Contracheque"
    elif "carteira de trabalho" in text:
        return "Carteira de Trabalho"
    elif "imposto sobre a renda" in text:
        return "Imposto de Renda"
    else:
        return "Não é possível analisar este arquivo"


def rotula_imposto_de_renda(text, numero_paginas):
    if "edital complementar" in text or "edital de abertura" in text or "conselho federal" in text:
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
        if "exercício 2023" not in text:
            return "Inválido"
        else:
            return "Imposto de Renda"
    else:
        return "Não é possível analizar este arquivo"


def extrair_salario_bruto(texto):
    salario_bruto = 0
    # Encontrar todas as ocorrências de números no texto
    numeros = re.findall(r'\d+\.\d+\,\d+', texto)
    if numeros:
        # Remover pontos, substituir vírgulas por pontos e converter para floats
        numeros_floats = [float(num.replace('.', '').replace(',', '.')) for num in numeros]

        # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
        if numeros_floats:
            salario_bruto = max(numeros_floats)
    else:
        numeros_2 = re.findall(r'\d+\,\d+\.\d+', texto)
        if numeros_2:
            # Remover pontos, substituir vírgulas por pontos e converter para floats
            numeros_floats = [float(num.replace(',', '')) for num in numeros_2]

            # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
            if numeros_floats:
                salario_bruto = max(numeros_floats)
        else:
            numeros_3 = re.findall(r'\d+\,\d+', texto)
            if numeros_3:
                # Remover pontos, substituir vírgulas por pontos e converter para floats
                numeros_floats = [float(num.replace(',', '.')) for num in numeros_3]

                # Se houver números, retornar o maior (assumindo que o salário bruto é o maior valor)
                if numeros_floats:
                    salario_bruto = max(numeros_floats)
    return salario_bruto


def julga_salario_bruto(salario, texto):
    passou = False
    if salario != 0 and salario > 3960:
        passou = True
    if "férias" in texto or "recesso" in texto or "ferias" in texto or "repouso" in texto\
            or "adiantamento 13salario" in texto:
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
        'Dezembro': 12
    }
    return meses.get(mes, 0)


def extrair_mes_ano(texto):
    padroes_data = [
        r'(?<![\d/])\b(0?[1-9]|1[0-2])/(20\d{2})\b',  # Padrão MM/AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro) / (20\d{2})\b',  # Padrão Mês / AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)/(20\d{2})\b',  # Padrão Mês/AAAA
        r'\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro) de (20\d{2})',  # Padrão Mês de AAAA
        r'01/(0?[1-9]|10|11|12)/(20\d{2}) (a|à) (28|30|31)/(0?[1-9]|10|11|12)/(20\d{2})',  # Padrão MM/AAAA a MM/AAAA
        r'(?<![\d/])\b(0?[1-9]|1[0-2]) / (20\d{2})\b',  # Padrão MM / AAAA
        r'(?<![\d/])\b(0?[1-9]|1[0-2])-(20\d{2})\b'  # Padrão MM-AAAA
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
            datas_ordenadas = sorted(datas)
        # Verificar se as datas são consecutivas
            for i in range(len(datas_ordenadas) - 1):
                if datas_ordenadas[i].month == datas_ordenadas[i + 1].month:
                    return True
        return False




