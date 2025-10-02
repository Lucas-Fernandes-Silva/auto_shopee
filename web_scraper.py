import requests
from bs4 import BeautifulSoup
import json
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio
from playwright.async_api import async_playwright
from logger import logger
import pandas as pd


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
            logger.info("Cache salvo.")

    def _processar_com_requests(self, produto):
        url = self._montar_url(produto)
        if not url:
            return {}

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/json")
            if not script:
                logger.warning(f"Script JSON não encontrado na URL: {url}")
                return {}
            data = json.loads(script.string)
            return self._extrair_dados(data)

        except requests.RequestException as e:
            logger.exception(f"Erro ao fazer request para {url}: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.exception(f"Falha ao decodificar JSON em {url}: {e}")
            return {}
        except Exception as e:
            logger.exception(f"Erro inesperado em _processar_com_requests {url}: {e}")
            return {}

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

    def _get_nested(self, data, keys, default=None):
        try:
            for k in keys:
                if isinstance(data, dict):
                    data = data.get(k, default)
                elif isinstance(data, list) and isinstance(k, int):
                    data = data[k]
                else:
                    return default
            return data
        except Exception:
            return default

    def _extrair_dados(self, data):
        try:
            produto = self._get_nested(data, ["props", "pageProps", "produto"], {})
            if isinstance(produto, list):  
                logger.warning("Produto veio como lista, pegando o primeiro elemento.")
                produto = produto[0] if produto else {}

            if not isinstance(produto, dict):
                logger.error(f"Formato inesperado de produto: {type(produto)}")
                return {}
            peso = produto.get("pesoBruto")
            codigo_barras = produto.get("codBarra")

            seo = self._get_nested(data, ["props", "pageProps", "seo"], {})
            url_img = seo.get("imageUrl")
            marca = next(
                (p.get("desc") for p in produto.get("dimensoes", [])
                if isinstance(p, dict) and p.get("label") == "MARCA"), None
            
            )
            return {
                "marca": marca,
                "peso": peso,
                "codigo_barras": codigo_barras,
                "url_img": url_img
        }
        except Exception as e:
            logger.info(f'Produto não encontrado{e}')

    def _processar_produto(self, produto):
        codigo = produto.get("Codigo Produto")
        if codigo in self.cache:
            return codigo, self.cache[codigo]

        try:
            dados = self._processar_com_requests(produto) or {}
        except Exception as e:
            logger.error(f"Erro inesperado no requests para {produto.get('Descrição')} ({codigo}): {e}")
            self.cache[codigo] = {}
            return codigo, {}


        if any(v is None or v == '' for v in (dados.get('marca'), dados.get('peso'), dados.get('codigo_barras'))):
            logger.info(f"Fallback Playwright para {produto.get('Descrição')}")
            try:
                dados = asyncio.run(self._processar_com_playwright(produto)) or {}
            except RuntimeError:
                loop = asyncio.get_event_loop()
                dados = loop.run_until_complete(self._processar_com_playwright(produto))
            except Exception as e:
                logger.error(f"Erro no Playwright para {produto.get('Descrição')} ({codigo}): {e}")
                dados = {}

        self.cache[codigo] = dados
        return codigo, dados   # <-- retorna chave + valor


    def enriquecer_dataframe(self, df, paralelo=True):
        for col in ["Marca", "Peso", "Url Imagem"]:
            if col not in df.columns:
                df[col] = None

            if paralelo:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    resultados = dict(executor.map(self._processar_produto, df.to_dict("records")))
            else:
                resultados = dict(self._processar_produto(p) for p in df.to_dict("records"))

        def processar_linha(row):
            codigo = row["Codigo Produto"]
            dados = resultados.get(codigo, {}) or {}
            return pd.Series({
                "Marca": dados.get("marca"),
                "Peso": dados.get("peso"),
                "Url Imagem": dados.get("url_img"),
                "Código de Barras": (
                    dados.get("codigo_barras")
                    if row.get("Código de Barras") == "SEM GTIN"
                    else row.get("Código de Barras")
                )
            })

        df_novos = df.apply(processar_linha, axis=1)
        df.update(df_novos)
        self._salvar_cache()
        return df


