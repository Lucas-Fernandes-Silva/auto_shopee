import pandas as pd
from rapidfuzz import fuzz, process

from src.utils.normalizer import Normalizer


class CategoryFiller:
    def __init__(self, df):
        self.df = df
        self.com_categoria = df[df["Categoria"].notna() & (df["Categoria"] != "")]
        self.sem_categoria = df[df["Categoria"].isna() | (df["Categoria"] == "")]

    def _buscar_categoria(self, descricao):
        match = process.extractOne(
            Normalizer.normalize(descricao),
            self.com_categoria["Descrição"].map(Normalizer.normalize),
            scorer=fuzz.token_sort_ratio,
        )
        if not match:
            return "Sem categoria semelhante"
        _, score, idx = match
        return (
            self.com_categoria.iloc[idx]["Categoria"]
            if score > 40
            else "Sem categoria semelhante"
        )

    def aplicar(self):
        if self.sem_categoria.empty:
            return self.df
        self.sem_categoria["Categoria"] = self.sem_categoria["Descrição"].map(
            self._buscar_categoria
        )
        return pd.concat([self.com_categoria, self.sem_categoria], ignore_index=True)
