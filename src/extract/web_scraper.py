import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.utils.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            if response.status_code == 404:
                logger.warning(f"Produto não encontrado (404): {url}")
                return {}
            if not response.text.strip():
                logger.warning(f"Página vazia para {url}")
                return {}
            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/json")
            if not script:
                logger.warning(f"Script JSON não encontrado na URL: {url}")
                return {}
            data = json.loads(script.text)
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
            data = json.loads(script.text)
            return self._extrair_dados(data)

    def _montar_url(self, produto):
        fornecedor = produto.get("Fornecedor")
        codigo = produto.get("Codigo Produto")

        if fornecedor == "CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA":
            return f"https://www.construdigi.com.br/produto/{codigo}/{codigo}"
        elif fornecedor == "M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO":
            return f"https://msbitaqua.com.br/produto/{codigo}/{codigo}"
        elif fornecedor == "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU":
            return f"https://www.construja.com.br/produto/{codigo}/{codigo}"
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
            if not produto:
                logger.warning("Produto vazio no JSON — pulando item.")
                return {}
            if isinstance(produto, list):
                logger.warning("Produto veio como lista, pegando o primeiro elemento.")
                produto = produto[0] if produto else {}
            if not isinstance(produto, dict):
                logger.error(f"Formato inesperado de produto: {type(produto)}")
                return {}
            peso = produto.get("pesoBruto")
            codigo_barras = produto.get("codBarra")
            altura = produto.get("altura")
            largura = produto.get("largura")
            comprimento = produto.get("comprimento")

            seo = self._get_nested(data, ["props", "pageProps", "seo"], {})
            url_img = seo.get("imageUrl") if seo else None
            marca = next(
                (
                    p.get("desc")
                    for p in produto.get("dimensoes", [])
                    if isinstance(p, dict) and p.get("label") == "MARCA"
                ),
                "",
            )
            cartegoria = next(
                (
                    p.get("desc")
                    for p in produto.get("dimensoes", [])
                    if isinstance(p, dict) and p.get("label") == "SUB CATEGORIA"
                ),
                None,
            )
            return {
                "categoria": cartegoria,
                "marca": marca,
                "peso": peso,
                "codigo_barras": codigo_barras,
                "url_img": url_img,
                "largura": largura,
                "altura": altura,
                "comprimento": comprimento,
            }
        except Exception as e:
            logger.info(f"Produto não encontrado{e}")

    def _processar_produto(self, produto):
        codigo = produto.get("Codigo Produto")
        if codigo in self.cache:
            return codigo, self.cache[codigo]

        try:
            dados = self._processar_com_requests(produto) or {}
        except Exception as e:
            logger.error(
                f"Erro inesperado no requests para {produto.get('Descrição')} ({codigo}): {e}"
            )
            self.cache[codigo] = {}
            return codigo, {}

        if any(
            v is None or v == ""
            for v in (dados.get("marca"), dados.get("peso"), dados.get("codigo_barras"))
        ):
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
        return codigo, dados  # <-- retorna chave + valor

    def enriquecer_dataframe(self, df_produtos, fornecedores, paralelo=True):
        df_resultado = df_produtos.copy()

        df_filtrado = df_resultado[df_resultado["Fornecedor"].isin(fornecedores[1])].copy()

        if df_filtrado.empty:
            logger.info("Nenhum fornecedor da lista de web scrapping encontrado no DataFrame.")
            return df_resultado

        for col in [
            "Marca",
            "Peso",
            "Url Imagem",
            "Largura",
            "Altura",
            "Comprimento",
            "Categoria",
        ]:
            if col not in df_resultado.columns:
                df_resultado[col] = None

            if paralelo:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    resultados = dict(
                        executor.map(self._processar_produto, df_filtrado.to_dict("records"))
                    )
            else:
                resultados = dict(
                    self._processar_produto(p) for p in df_filtrado.to_dict("records")
                )

        def processar_linha(row):
            codigo = row["Codigo Produto"]
            dados = resultados.get(codigo, {}) or {}
            descricao = str(row.get("Descrição")).strip()
            marca = dados.get("marca")
            if marca is not None and marca not in descricao:
                descrição_completa = f"{descricao} {marca}".strip()
            else:
                descrição_completa = descricao
            return pd.Series(
                {
                    "Altura": dados.get("altura"),
                    "Largura": dados.get("largura"),
                    "Comprimento": dados.get("comprimento"),
                    "Marca": marca,
                    "Categoria": dados.get("categoria"),
                    "Descrição": descrição_completa,
                    "Peso": dados.get("peso") or "NÃO DISPONIVEL",
                    "Url Imagem": dados.get("url_img") or "NÃO DISPONIVEL",
                    "Código de Barras": (
                        dados.get("codigo_barras")
                        if row.get("Código de Barras") == "SEM GTIN"
                        else row.get("Código de Barras")
                    ),
                }
            )

        df_novo = df_filtrado.apply(processar_linha, axis=1)
        df_resultado.update(df_novo)
        df_resultado["Peso"] = df_resultado["Peso"].fillna(1)
        df_resultado = df_resultado[
            (df_resultado["Peso"].astype(str).str.upper() != "NÃO DISPONIVEL")
            & (df_resultado["Url Imagem"].astype(str).str.upper() != "NÃO DISPONIVEL")
        ]

        self._salvar_cache()
        return df_resultado
