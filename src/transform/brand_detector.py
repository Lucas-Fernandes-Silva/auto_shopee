import numpy as np
import pandas as pd

from dados import dados
from src.utils.normalizer import Normalizer


class BrandDetector:
    def __init__(self, df):
        self.df = df
        self.marca_variacoes = dados.marca_variacoes
        self.marcas_adicionais = dados.marcas_adicionais or []

        # Normaliza marcas adicionais
        self.marcas_adicionais = {Normalizer.normalize(m) for m in self.marcas_adicionais}

        # Compila todas as marcas conhecidas
        self.marcas = self._compilar_marcas()

    def _compilar_marcas(self):
        marcas = set(self.marcas_adicionais)

        # Marcas já existentes na planilha
        if "Marca" in self.df.columns:
            marcas_planilha = {
                Normalizer.normalize(m) for m in self.df["Marca"].dropna().astype(str)
            }
            marcas_planilha.discard("5")  # sujeira comum
            marcas |= marcas_planilha

        # Marcas padrão + variações
        for marca_padrao, variacoes in self.marca_variacoes.items():
            marcas.add(Normalizer.normalize(marca_padrao))
            marcas |= {Normalizer.normalize(v) for v in variacoes}

        return marcas

    def detectar(self, descricao):
        if not isinstance(descricao, str) or not descricao.strip():
            return np.nan

        desc = Normalizer.normalize(descricao)

        # 1️⃣ Prioridade: variações mapeadas → marca padrão
        for marca_padrao, variacoes in self.marca_variacoes.items():
            for v in variacoes:
                if Normalizer.normalize(v) in desc:
                    return marca_padrao

        # 2️⃣ Fallback: marca solta no texto
        for marca in self.marcas:
            if marca in desc:
                return marca

        return np.nan

    def aplicar(self, sobrescrever=False):
        if sobrescrever:
            self.df["Marca"] = self.df["Descrição"].map(self.detectar).fillna("GENÉRICO")
        else:
            self.df["Marca"] = (
                self.df.get("Marca", pd.Series(index=self.df.index))
                .fillna(self.df["Descrição"].map(self.detectar))
                .fillna("GENÉRICO")
            )

        return self.df
