# Análise de Contracheques e Declarações de Imposto de Renda

Este projeto é destinado à análise automatizada de contracheques e declarações de imposto de renda. Utilizando técnicas de extração de texto de PDFs e imagens, o programa avalia as informações extraídas e classifica os documentos com base em regras predefinidas.

## Estrutura do Projeto

### Arquivos Principais

- `main.py`: Script principal que lê o arquivo de entrada, executa a análise dos documentos e salva os resultados em um arquivo de saída.
- `functions.py`: Contém as funções auxiliares para extração e processamento dos dados dos documentos.

### Funções Importantes

- `extrair_texto(url)`: Extrai texto de PDFs e imagens utilizando OCR (Tesseract).
- `extrai_numero_de_paginas(url)`: Retorna o número de páginas de um PDF.
- `rotula_contracheque(text, numero_paginas)`: Classifica um documento como contracheque ou inválido.
- `rotula_imposto_de_renda(text, numero_paginas)`: Classifica um documento como declaração de imposto de renda ou inválido.
- `extrair_salario_bruto(texto)`: Extrai o valor do salário bruto de um texto.
- `julga_salario_bruto(salario, texto)`: Avalia se o salário bruto atende aos critérios estabelecidos.
- `extrair_imposto_de_renda(texto)`: Extrai o valor do imposto de renda de um texto.
- `julga_imposto_de_renda(imposto_de_renda)`: Avalia se o valor do imposto de renda atende aos critérios estabelecidos.
- `extrair_mes_ano(texto)`: Extrai a data (mês e ano) de um texto.
- `verifica_meses_iguais(datas)`: Verifica se os meses extraídos dos documentos são iguais.

## Dependências

Para rodar este projeto, você precisa instalar as seguintes bibliotecas Python:

- `pandas`
- `tqdm`
- `requests`
- `fitz` (PyMuPDF)
- `pytesseract`
- `Pillow`
- `opencv-python`
- `numpy`

Você pode instalar todas as dependências utilizando o seguinte comando:

```bash
pip install pandas tqdm requests pymupdf pytesseract Pillow opencv-python numpy
```
## Uso
1. Coloque o arquivo de entrada (em formato .xlsx) na pasta do projeto.
2. Atualize o caminho do arquivo de entrada no script main.py.
3. Execute o script principal:

```bash
python main.py
```
4. O resultado será salvo em um arquivo Excel na pasta do projeto com o nome Saída Programa Lote 5.xlsx.

## Estrutura do Arquivo de Entrada
O arquivo de entrada deve estar no formato Excel (.xlsx) e deve conter as seguintes colunas:

* B.1) Contracheque 1 - Contracheque/comprovante de pagamento do examinando
* B.2) Contracheque 2 - Contracheque/comprovante de pagamento do examinando
* B.3) Contracheque 3 - Contracheque/comprovante de pagamento do examinando
* C) Declaração do imposto de renda do examinando
Cada coluna deve conter a URL para o respectivo documento.

## Saída
O arquivo de saída (Saída Programa Lote 5.xlsx) conterá as colunas do arquivo de entrada, além das seguintes colunas adicionais:

* 'Análise Programa (Contracheque)'
* 'Análise Programa (Imposto de Renda)'

## Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Contato
* João Lucas
* Email: jaolucasssp@gmail.com
