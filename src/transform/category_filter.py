import os
import sys

import pandas as pd
from rapidfuzz import fuzz, process

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.logger import logger
from src.utils.normalizer import Normalizer


class CategoryFiller:
    def __init__(self, df, cache_path="/home/lucas-silva/auto_shopee/cache/produtos.json"):
        self.df = df
        self.cache_path = cache_path

        # 🔹 Produtos sem categoria no DF atual
        self.sem_categoria = df[df["Categoria"].isna() | (df["Categoria"] == "")].copy()

        # 🔹 Carregar cache
        self.cache = self._carregar_cache()

    def _carregar_cache(self):
        if not os.path.exists(self.cache_path):
            logger.warning("Arquivo de cache não encontrado.")
            return pd.DataFrame(columns=["Descrição", "Categoria"])

        cache = pd.read_csv(self.cache_path)

        cache = cache[cache["Categoria"].notna() & (cache["Categoria"] != "")].copy()

        logger.info(f"Cache carregado com {len(cache)} produtos categorizados.")
        return cache

    def _buscar_categoria(self, descricao):
        if self.cache.empty or not isinstance(descricao, str) or descricao.strip() == "":
            return ""

        match = process.extractOne(
            Normalizer.normalize(descricao),
            self.cache["Descrição"].map(Normalizer.normalize),
            scorer=fuzz.token_sort_ratio,
        )

        if not match:
            return ""

        _, score, idx = match

        if score < 40:
            return ""

        return self.cache.iloc[idx]["Categoria"]

    def aplicar(self):
        if self.sem_categoria.empty:
            logger.info("Nenhuma linha sem categoria encontrada.")
            return self.df

        self.sem_categoria["Categoria"] = self.sem_categoria["Descrição"].map(
            self._buscar_categoria
        )

        df_final = pd.concat(
            [
                self.df[self.df["Categoria"].notna() & (self.df["Categoria"] != "")],
                self.sem_categoria,
            ],
            ignore_index=True,
        )

        return df_final
