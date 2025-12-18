import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from dados import dados
from src.utils.logger import logger
from src.utils.normalizer import Normalizer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebScraper:
    def __init__(
        self,
        headers=dados.headers,
        cache_file="cache/produtos.json",
        marca_variacoes=dados.marca_variacoes,
    ):
        self.headers = headers or {"User-Agent": "Mozilla/5.0"}
        self.cache_file = cache_file
        self.cache = self._carregar_cache()

        # Marca padrão -> variações (APENAS padronização)
        self.marca_variacoes = {
            Normalizer.normalize(marca): {
                Normalizer.normalize(v) for v in variacoes
            }
            for marca, variacoes in (marca_variacoes or {}).items()
        }

    # ==========================================================
    # CACHE
    # ==========================================================
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

    # ==========================================================
    # MARCA — APENAS PADRONIZAÇÃO
    # ==========================================================
    def _padronizar_marca(self, marca):
        if not isinstance(marca, str) or marca.strip() == "":
            return None

        marca_norm = Normalizer.normalize(marca)

        for marca_padrao, variacoes in self.marca_variacoes.items():
            if marca_norm == marca_padrao or marca_norm in variacoes:
                return marca_padrao

        # Não reconheceu → mantém como veio (limpo)
        return marca.strip()

    # ==========================================================
    # REQUESTS
    # ==========================================================
    def _processar_com_requests(self, produto):
        url = self._montar_url(produto)
        if not url:
            return {}

        try:
            response = requests.get(
                url, headers=self.headers, timeout=10, verify=False
            )

            if response.status_code == 404:
                logger.warning(f"Produto não encontrado (404): {url}")
                return {}

            if not response.text.strip():
                logger.warning(f"Página vazia para {url}")
                return {}

            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/json")

            if not script:
                logger.warning(f"Script JSON não encontrado: {url}")
                return {}

            data = json.loads(script.text)
            return self._extrair_dados(data)

        except Exception as e:
            logger.exception(f"Erro no requests para {url}: {e}")
            return {}

    # ==========================================================
    # PLAYWRIGHT
    # ==========================================================
    async def _processar_com_playwright(self, produto):
        url = self._montar_url(produto)
        if not url:
            return {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")

        if not script:
            return {}

        data = json.loads(script.text)
        return self._extrair_dados(data)

    # ==========================================================
    # URL
    # ==========================================================
    def _montar_url(self, produto):
        fornecedor = produto.get("Fornecedor")
        codigo = produto.get("Codigo Produto")

        if fornecedor == "CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA":
            return f"https://www.construdigi.com.br/produto/{codigo}/{codigo}"

        elif fornecedor == "M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO":
            return f"https://msbitaqua.com.br/produto/{codigo}/{codigo}"

        elif fornecedor == "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU":
            return f"https://www.construja.com.br/produto/{codigo}/{codigo}"

        return None

    # ==========================================================
    # UTIL
    # ==========================================================
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

    # ==========================================================
    # EXTRAÇÃO
    # ==========================================================
    def _extrair_dados(self, data):
        try:
            produto = self._get_nested(
                data, ["props", "pageProps", "produto"], {}
            )

            if not produto:
                return {}

            peso = produto.get("pesoBruto")
            codigo_barras = produto.get("codBarra")
            altura = produto.get("altura")
            largura = produto.get("largura")
            comprimento = produto.get("comprimento")

            seo = self._get_nested(data, ["props", "pageProps", "seo"], {})
            url_img = seo.get("imageUrl") if seo else None

            marca_raw = next(
                (
                    p.get("desc")
                    for p in produto.get("dimensoes", [])
                    if isinstance(p, dict) and p.get("label") == "MARCA"
                ),
                "",
            )

            marca = self._padronizar_marca(marca_raw)

            categoria = next(
                (
                    p.get("desc")
                    for p in produto.get("dimensoes", [])
                    if isinstance(p, dict)
                    and p.get("label") == "SUB CATEGORIA"
                ),
                None,
            )

            return {
                "categoria": categoria,
                "marca": marca,
                "peso": peso,
                "codigo_barras": codigo_barras,
                "url_img": url_img,
                "largura": largura,
                "altura": altura,
                "comprimento": comprimento,
            }

        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return {}

    # ==========================================================
    # PROCESSAMENTO
    # ==========================================================
    def _processar_produto(self, produto):
        codigo = produto.get("Codigo Produto")

        if codigo in self.cache:
            return codigo, self.cache[codigo]

        dados_produto = self._processar_com_requests(produto) or {}

        if any(
            v in (None, "")
            for v in (
                dados_produto.get("marca"),
                dados_produto.get("peso"),
                dados_produto.get("codigo_barras"),
            )
        ):
            try:
                dados_produto = asyncio.run(
                    self._processar_com_playwright(produto)
                ) or {}
            except RuntimeError:
                loop = asyncio.get_event_loop()
                dados_produto = loop.run_until_complete(
                    self._processar_com_playwright(produto)
                )
            except Exception:
                pass

        self.cache[codigo] = dados_produto
        return codigo, dados_produto

    # ==========================================================
    # DATAFRAME
    # ==========================================================
    def enriquecer_dataframe(self, df_produtos, paralelo=True):
        fornecedores = dados.fornecedores
        df_resultado = df_produtos.copy()

        colunas_necessarias = [
        "Marca",
        "Categoria",
        "Peso",
        "Url Imagem",
        "Largura",
        "Altura",
        "Comprimento",
        "Código de Barras",

    ]

        for col in colunas_necessarias:
            if col not in df_resultado.columns:
                df_resultado[col] = None


        df_filtrado = df_resultado[
            df_resultado["Fornecedor"].isin(fornecedores[1])
        ].copy()

        if df_filtrado.empty:
            return df_resultado

        if paralelo:
            with ThreadPoolExecutor(max_workers=5) as executor:
                resultados = dict(
                    executor.map(
                        self._processar_produto,
                        df_filtrado.to_dict("records"),
                    )
                )
        else:
            resultados = dict(
                self._processar_produto(p)
                for p in df_filtrado.to_dict("records")
            )

        def processar_linha(row):
            codigo = row["Codigo Produto"]
            dados_prod = resultados.get(codigo, {}) or {}

            return pd.Series(
                {
                    "Altura": dados_prod.get("altura"),
                    "Largura": dados_prod.get("largura"),
                    "Comprimento": dados_prod.get("comprimento"),
                    "Marca": dados_prod.get("marca"),
                    "Categoria": dados_prod.get("categoria"),
                    "Peso": dados_prod.get("peso") or row.get("Peso"),
                    "Url Imagem": dados_prod.get("url_img") or row.get("Url Imagem"),
                    "Código de Barras": (
                        dados_prod.get("codigo_barras")
                        if row.get("Código de Barras") == "SEM GTIN"
                        else row.get("Código de Barras")
                    ),
                }
            )

        df_novo = df_filtrado.apply(processar_linha, axis=1)
        df_resultado.update(df_novo)
        self._salvar_cache()
        return df_resultado
