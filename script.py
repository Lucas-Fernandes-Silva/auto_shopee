# #Criar um script que faça:  
# #Pegue as nfe em xml do email  
# #Extrai os dados necessarios   
# #Tratar dados   
# #Remover materiais pesado E outras notas 
# -TABUAS CABOQUINHO  
# -CIMENTRO VOTORAN  
# -Magalu   
# 
# #Aplicador formula de taxas  
# #Inserir no template dos marketplaces
#   

import os
import shutil
import xml.etree.ElementTree as ET
import pandas as pd
from imap_tools import MailBox, AND
from config import pwd, user
from datetime import date
import requests
from bs4 import BeautifulSoup
import json
from playwright.async_api import async_playwright
import asyncio


save_folder = "notas/nfes/"
os.makedirs(save_folder, exist_ok=True)

# 🔹 Baixar anexos XML do e-mail
with MailBox("imap.gmail.com").login(user, pwd, initial_folder="INBOX") as mailbox:
    list_mail = mailbox.fetch(criteria=AND(date=date.today()))
    for email in list_mail:
        for anexo in email.attachments:
            if anexo.filename.lower().endswith(".xml"):
                file_path = os.path.join(save_folder, anexo.filename)
                if not os.path.exists(file_path):
                    with open(file_path, "wb") as f:
                        f.write(anexo.payload)

pasta_origem = "notas/nfes"
todos_produtos = []


# 🔹 Função para extrair dados do XML
def extrai_dados(caminho_arquivo):
    produtos = []
    tree = ET.parse(caminho_arquivo)
    root = tree.getroot()
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

    natOp = root.find(".//ns:ide/ns:natOp", ns)
    if natOp is not None and natOp.text.strip().upper() == 'BONIFICACAO, DOACAO OU BRINDE':
        return [] 

    for det in root.findall(".//ns:det", ns):   
        produto = {}
        produto['Codigo Produto'] = det.find("./ns:prod/ns:cProd", ns).text
        produto['Descrição'] = det.find("./ns:prod/ns:xProd", ns).text
        produto['Valor_unitário'] = det.find("./ns:prod/ns:vUnCom", ns).text
        produto['Código de Barras'] = det.find("./ns:prod/ns:cEAN", ns).text 
        produto['Sku'] = produto['Código de Barras']
        if produto['Sku'] == 'SEM GTIN':
            produto['Sku'] = produto['Descrição']
        produto['Fornecedor'] = root.find(".//ns:emit/ns:xNome", ns).text
        produtos.append(produto)
    return produtos
        

# 🔹 Processar todos os XMLs da pasta
for arquivo in os.listdir(pasta_origem):
    if arquivo.lower().endswith(".xml"):
        caminho_arquivo = os.path.join(pasta_origem, arquivo)
        try:
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

            cnpj_emitente = root.find(".//ns:emit/ns:CNPJ", ns)
            if cnpj_emitente is None:
                print(f"⚠️ CNPJ não encontrado em {arquivo}")
                continue

            produtos_xml = extrai_dados(caminho_arquivo)
            todos_produtos.extend(produtos_xml)

            # Copia o arquivo para "notas/"
            pasta_destino = os.path.join("notas/")
            os.makedirs(pasta_destino, exist_ok=True)
            shutil.copy(caminho_arquivo, pasta_destino)

        except Exception as e:
            print(f"{arquivo}: {e}")


# 🔹 Fornecedores que devem ser ignorados
fornecedores_pesados = [
    'IND E COM DE TUBOS E CONEXOES FORT.COM',
    'VOTORANTIM CIMENTOS SA',
    'CABOQUINHO MATERIAIS PARA CONSTRUCAO'
]

# 🔹 DataFrame inicial
produtos = pd.DataFrame(todos_produtos)
produtos = produtos[~produtos['Fornecedor'].isin(fornecedores_pesados)]
produtos = produtos.drop_duplicates(subset='Codigo Produto', keep='first')

# 🔹 Headers para requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


# 🔹 Função fallback com Playwright
async def get_data_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            await browser.close()
            return {}

        data = json.loads(script.string)
        produto = data.get("props", {}).get("pageProps", {}).get("produto", {})
        url_img = data.get("props", {}).get("pageProps", {}).get("seo", {}).get("imageUrl", 'Não disponível')

        await browser.close()
        return {
            'marca': next((p.get("desc") for p in produto.get("dimensoes", []) if p.get("label") == "MARCA"), "Não disponível"),
            'peso': produto.get("pesoBruto", "Não disponível"),
            'codigo_barras': produto.get("codBarra", "Não disponível"),
            'url_img': url_img,
        }


# 🔹 Loop principal (síncrono, com fallback)
def processa_produtos(produtos, headers):
    for index, produto in produtos.iterrows():
        fornecedor = produto['Fornecedor']
        codigo_produto = produto['Codigo Produto']
        descricao = produto['Descrição']

        # Monta URL conforme fornecedor
        if fornecedor == 'CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA':   
            url = f'https://www.construdigi.com.br/produto/{codigo_produto}/{descricao}'
        elif fornecedor == 'M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO':
            url = f'https://msbitaqua.com.br/produto/{codigo_produto}/{descricao}'
        elif fornecedor == "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU":
            url = f'https://www.construja.com.br/produto/{codigo_produto}/{descricao}'
        else:
            print('Indisponível')
            continue

        try:
            # Primeiro tenta com requests (rápido)
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/json")
            data = json.loads(script.string) if script else {}

            extrai = data.get("props", {}).get("pageProps", {}).get("produto", {})
            url_img = data.get("props", {}).get("pageProps", {}).get("seo", {}).get("imageUrl", '')

            marca = next((p.get("desc") for p in extrai.get("dimensoes", []) if p.get("label") == "MARCA"), "")
            peso = extrai.get("pesoBruto", "")
            codigo_barras = extrai.get("codBarra", "")

            # Se não conseguiu pegar nada → fallback Playwright
            if not (marca or peso or codigo_barras):
                print(f"⚠️ Fallback Playwright para {descricao}")
                dados = asyncio.run(get_data_playwright(url))
                marca = dados["marca"]
                peso = dados["peso"]
                codigo_barras = dados["codigo_barras"]
                url_img = dados["url_img"]

            # Atualiza DataFrame
            produtos.at[index, 'Código de Barras'] = codigo_barras or "Não disponível"
            produtos.at[index, 'Peso'] = peso or "Não disponível"
            produtos.at[index, "Marca"] = marca or "Não disponível"
            produtos.at[index, 'Url Imagem'] = url_img or "Não disponível"

            print("✅", descricao)

        except Exception as e:
            print("❌ Erro:", e)


# 🔹 Executar
processa_produtos(produtos, headers)

# 🔹 Salvar Excel final
produtos.to_excel("produtos.xlsx", index=False)
print("📁 Arquivo 'produtos.xlsx' gerado com sucesso!")
