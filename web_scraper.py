import requests
from bs4 import BeautifulSoup
import json
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio
from playwright.async_api import async_playwright

class WebScraper:
    def __init__(self, headers=None, cache_file="cache/produtos.json"):
        self.headers = headers or {"User-Agent": "Mozilla/5.0"}
        self.cache_file = cache_file
        self.cache = self._carregar_cache()

    def _carregar_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _salvar_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _processar_com_requests(self, produto):
        url = self._montar_url(produto)
        if not url:
            return {}

        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        script = soup.find("script", type="application/json")
        if not script:
            return {}

        data = json.loads(script.string)
        return self._extrair_dados(data)

    async def _processar_com_playwright(self, produto):

        url = self._montar_url(produto)
        if not url:
            return {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            await browser.close()

            if not script:
                return {}
            data = json.loads(script.string)
            return self._extrair_dados(data)

    def _montar_url(self, produto):
    
        fornecedor = produto.get("Fornecedor")
        codigo = produto.get("Codigo Produto")

        if fornecedor == 'CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA':
            return f'https://www.construdigi.com.br/produto/{codigo}/{codigo}'
        elif fornecedor == 'M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO':
            return f'https://msbitaqua.com.br/produto/{codigo}/{codigo}'
        elif fornecedor == "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU":
            return f'https://www.construja.com.br/produto/{codigo}/{codigo}'
        else:
            return None

    def _extrair_dados(self, data):
 
        produto = data.get("props", {}).get("pageProps", {}).get("produto", {})
        seo = data.get("props", {}).get("pageProps", {}).get("seo", {})

        return {
            "marca": next((p.get("desc") for p in produto.get("dimensoes", []) if p.get("label") == "MARCA"), "Não disponível"),
            "peso": produto.get("pesoBruto", "Não disponível"),
            "codigo_barras": produto.get("codBarra", "SEM GTIN"),
            "url_img": seo.get("imageUrl", "Não disponível")
        }

    def enriquecer_dataframe(self, df, paralelo=True):

        produtos = df.to_dict("records")

        if paralelo:
            with ThreadPoolExecutor(max_workers=5) as executor:
                resultados = list(executor.map(self._processar_produto, produtos))
        else:
            resultados = [self._processar_produto(p) for p in produtos]

        for i, dados in enumerate(resultados):
            df.at[i, "Marca"] = dados.get("marca", "")
            df.at[i, "Peso"] = dados.get("peso", "")
            df.at[i, "Código de Barras"] = dados.get("codigo_barras", "")
            df.at[i, "Url Imagem"] = dados.get("url_img", "")

        self._salvar_cache()

        return df

    def _processar_produto(self, produto):

        codigo = produto.get("Codigo Produto")

        if codigo in self.cache:
            return self.cache[codigo]

        dados = self._processar_com_requests(produto)

        if not dados:
            print(f"⚠️ Fallback Playwright para {produto.get('Descrição')}")
            dados = asyncio.run(self._processar_com_playwright(produto))

        self.cache[codigo] = dados
        return dados

