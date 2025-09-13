
from bs4 import BeautifulSoup
import json, requests, asyncio
from playwright.async_api import async_playwright

class WebScraper:
    def __init__(self, headers):
        self.headers = headers

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

