import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from rapidfuzz import fuzz, process

from src.utils.logger import logger
from src.utils.normalizer import Normalizer


class CategoryFiller:
    def __init__(self, df):
        self.df = df
        self.com_categoria = df[df["Categoria"].notna() & (df["Categoria"] != "")].copy()
        self.sem_categoria = df[df["Categoria"].isna() | (df["Categoria"] == "")].copy()

    def _buscar_categoria(self, descricao):
        if not isinstance(descricao, str) or descricao.strip() == "":
            return "Sem categoria semelhante"

        match = process.extractOne(
            Normalizer.normalize(descricao),
            self.com_categoria["Descrição"].map(Normalizer.normalize),
            scorer=fuzz.token_sort_ratio,
        )

        # Nenhum match encontrado
        if not match:
            return "Sem categoria semelhante"

        _, score, idx = match

        # idx aqui é o RÓTULO do índice — use .loc em vez de .iloc
        if idx not in self.com_categoria.index or score <= 65:
            return "Sem categoria semelhante"

        return self.com_categoria.loc[idx, "Categoria"]

    def aplicar(self):
        if self.sem_categoria.empty:
            logger.info("Nenhuma linha sem categoria encontrada.")
            return self.df

        # .map aplica a função de busca de forma segura
        self.sem_categoria["Categoria"] = self.sem_categoria["Descrição"].map(
            self._buscar_categoria
        )

        # Recombina
        df_final = pd.concat([self.com_categoria, self.sem_categoria], ignore_index=True)

        return df_final
