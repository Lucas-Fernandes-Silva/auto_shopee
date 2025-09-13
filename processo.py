import os
import shutil
import xml.etree.ElementTree as ET
import pandas as pd
from imap_tools import MailBox, AND
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import json
from playwright.async_api import async_playwright
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from env import user, pwd

class ProcessadorNotas:
    def __init__(self, email_user, email_pwd, pasta_notas="notas/nfes", max_threads=5, log_file="processador.log"):
        self.email_user = email_user
        self.email_pwd = email_pwd
        self.save_folder = pasta_notas
        os.makedirs(self.save_folder, exist_ok=True)
        self.todos_produtos = []
        self.max_threads = max_threads

        # Configuração de logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
        

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        self.fornecedores_pesados = [
            'IND E COM DE TUBOS E CONEXOES FORT.COM',
            'VOTORANTIM CIMENTOS SA',
            'CABOQUINHO MATERIAIS PARA CONSTRUCAO'
        ]

    def baixar_anexos(self, data_inicio=date.today()):
        self.logger.info("🔹 Baixando anexos XML do e-mail…")
        with MailBox("imap.gmail.com").login(self.email_user, self.email_pwd, initial_folder="INBOX") as mailbox:
            list_mail = mailbox.fetch(criteria=AND(date_gte=data_inicio))
            for email in list_mail:
                for anexo in email.attachments:
                    if anexo.filename.lower().endswith(".xml"):
                        file_path = os.path.join(self.save_folder, anexo.filename)
                        if not os.path.exists(file_path):
                            with open(file_path, "wb") as f:
                                f.write(anexo.payload)
                            self.logger.info(f"Arquivo salvo: {file_path}")

    def extrai_dados(self, caminho_arquivo):
        produtos = []
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()
        ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
        data_str = root.find(".//ns:ide/ns:dhEmi", ns).text
        data_emissao = datetime.fromisoformat(data_str).replace(tzinfo=None)

        natOp = root.find(".//ns:ide/ns:natOp", ns)
        if natOp is not None and natOp.text.strip().upper() == 'BONIFICACAO, DOACAO OU BRINDE':
            return [] 

        for det in root.findall(".//ns:det", ns):   
            produto = {}
            temp_codigo = det.find("./ns:prod/ns:cProd", ns).text
            if "-" not in temp_codigo:
                produto['Codigo Produto'] = temp_codigo
            produto['Descrição'] = det.find("./ns:prod/ns:xProd", ns).text
            produto['Valor_unitário'] = det.find("./ns:prod/ns:vUnCom", ns).text
            produto['Código de Barras'] = det.find("./ns:prod/ns:cEAN", ns).text 
            produto['Sku'] = produto['Código de Barras']
            if produto['Sku'] == 'SEM GTIN':
                produto['Sku'] = produto['Descrição']
            produto['Fornecedor'] = root.find(".//ns:emit/ns:xNome", ns).text
            produto['Data Emissão'] = data_emissao
            produtos.append(produto)
        return produtos

    def processar_xmls(self):
        self.logger.info("🔹 Processando XMLs da pasta…")
        for arquivo in os.listdir(self.save_folder):
            if arquivo.lower().endswith(".xml"):
                caminho_arquivo = os.path.join(self.save_folder, arquivo)
                try:
                    tree = ET.parse(caminho_arquivo)
                    root = tree.getroot()
                    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

                    cnpj_emitente = root.find(".//ns:emit/ns:CNPJ", ns)
                    if cnpj_emitente is None:
                        self.logger.warning(f"CNPJ não encontrado em {arquivo}")
                        continue

                    produtos_xml = self.extrai_dados(caminho_arquivo)
                    self.todos_produtos.extend(produtos_xml)

                    pasta_destino = os.path.join("notas/")
                    os.makedirs(pasta_destino, exist_ok=True)
                    shutil.copy(caminho_arquivo, pasta_destino)

                except Exception as e:
                    self.logger.error(f"{arquivo}: {e}")

    async def get_data_playwright(self, url):
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
                'codigo_barras': produto.get("codBarra", "SEM GTIN"),
                'url_img': url_img,
            }

    def _processar_um_produto(self, index, produto, produtos_df):
        fornecedor = produto['Fornecedor']
        codigo_produto = produto['Codigo Produto']
        descricao = produto['Descrição']
        codigo_barras = produto['Código de Barras']

        if fornecedor == 'CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA':   
            url = f'https://www.construdigi.com.br/produto/{codigo_produto}/{codigo_produto}'
        elif fornecedor == 'M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO':
            url = f'https://msbitaqua.com.br/produto/{codigo_produto}/{codigo_produto}'
        elif fornecedor == "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU":
            url = f'https://www.construja.com.br/produto/{codigo_produto}/{codigo_produto}'
        else:
            return  # pula

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/json")
            data = json.loads(script.string) if script else {}

            extrai = data.get("props", {}).get("pageProps", {}).get("produto", {})
            url_img = data.get("props", {}).get("pageProps", {}).get("seo", {}).get("imageUrl", '')

            marca = next((p.get("desc") for p in extrai.get("dimensoes", []) if p.get("label") == "MARCA"), "")
            peso = extrai.get("pesoBruto", "")
            if codigo_barras == 'SEM GTIN':
                codigo_barras = extrai.get("codBarra", "SEM GTIN")

            if extrai == {}:
                self.logger.warning(f"Fallback Playwright para {descricao}")
                dados = asyncio.run(self.get_data_playwright(url))
                marca = dados["marca"]
                peso = dados["peso"]
                codigo_barras = dados["codigo_barras"]
                url_img = dados["url_img"]

            produtos_df.at[index, 'Código de Barras'] = codigo_barras or "Não disponível"
            produtos_df.at[index, 'Peso'] = peso or "Não disponível"
            produtos_df.at[index, "Marca"] = marca or "Não disponível"
            produtos_df.at[index, 'Url Imagem'] = url_img or "Não disponível"

            self.logger.info(f"✅ {descricao}")

        except Exception as e:
            self.logger.error(f"❌ Erro {descricao}: {e}")

    def processa_produtos(self, produtos_df):
        self.logger.info("🔹 Enriquecendo produtos (threads)…")
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            for index, produto in produtos_df.iterrows():
                futures.append(executor.submit(self._processar_um_produto, index, produto, produtos_df))

            for future in as_completed(futures):
                # só força exceções aparecerem
                future.result()

    def run(self):
        self.baixar_anexos(date(2025, 9, 1))
        self.processar_xmls()

        produtos = pd.DataFrame(self.todos_produtos)
        produtos = produtos[~produtos['Fornecedor'].isin(self.fornecedores_pesados)]
        produtos = produtos.sort_values(by="Data Emissão", ascending=False)
        produtos = produtos.drop_duplicates(subset='Codigo Produto', keep='first')

        self.processa_produtos(produtos)

        produtos.to_excel("produtos.xlsx", index=False)
        self.logger.info("📁 Arquivo 'produtos.xlsx' gerado com sucesso!")



proc = ProcessadorNotas(email_user=user, email_pwd=pwd, max_threads=10)
proc.run()
