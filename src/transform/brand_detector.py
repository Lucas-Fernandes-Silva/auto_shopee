import numpy as np

from src.utils.normalizer import Normalizer


class BrandDetector:
    def __init__(self, df, marcas_adicionais, marca_variacoes):
        self.df = df
        self.marcas_adicionais = {Normalizer.normalize(m) for m in marcas_adicionais}
        self.marca_variacoes = marca_variacoes
        self.marcas = self._compilar_marcas()

    def _compilar_marcas(self):
        marcas = set(self.marcas_adicionais)
        marcas_planilha = {
            Normalizer.normalize(m) for m in self.df["Marca"].dropna().astype(str)
        }
        marcas_planilha.discard("5")
        marcas |= marcas_planilha

        for marca, variacoes in self.marca_variacoes.items():
            marcas.add(Normalizer.normalize(marca))
            marcas |= {Normalizer.normalize(v) for v in variacoes}
        return marcas

    def detectar(self, descricao):
        desc = Normalizer.normalize(descricao)
        for marca_padrao, variacoes in self.marca_variacoes.items():
            if any(Normalizer.normalize(v) in desc for v in variacoes):
                return marca_padrao
        for marca in self.marcas:
            if marca in desc:
                return marca
        return np.nan

    def aplicar(self):
        self.df["Marca"] = (
            self.df["Marca"]
            .fillna(self.df["Descrição"].map(self.detectar))
            .fillna("GENÉRICO")
        )
        return self.df
