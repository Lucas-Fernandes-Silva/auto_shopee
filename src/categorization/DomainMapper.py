import pandas as pd

from src.utils.normalizer import Normalizer


class DomainMapper:
    def __init__(self, path_categorizados: str):
        self.mapa = pd.read_excel(path_categorizados)

        self.mapa["Termos"] = self.mapa["Termos_Chave"].fillna("").str.upper().str.split(";")

    def resolve(self, descricao: str):
        texto = Normalizer.normalize(descricao)

        for _, row in self.mapa.iterrows():
            if any(t in texto for t in row["Termos"] if t):
                return (
                    row["Dominio"],
                    row["Categoria_Principal"],
                    row["Subcategoria"],
                )

        return "OUTROS", None, None
