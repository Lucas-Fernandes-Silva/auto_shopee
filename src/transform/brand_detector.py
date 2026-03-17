import re
import pandas as pd

from dados import dados
from src.utils.normalizer import Normalizer


class BrandDetector:
    def __init__(self, df, marca_variacoes=None, marcas_adicionais=None):
        self.df = df

        self.marcas_adicionais = marcas_adicionais or dados.marcas_adicionais
        self.marca_variacoes = marca_variacoes or dados.marca_variacoes

        # Marca padrão -> variações normalizadas
        self.marca_variacoes = {
            Normalizer.normalize(marca): {
                Normalizer.normalize(marca),
                *(Normalizer.normalize(v) for v in variacoes)
            }
            for marca, variacoes in self.marca_variacoes.items()
        }

        # Marcas adicionais
        self.marcas_adicionais = {
            Normalizer.normalize(m) for m in self.marcas_adicionais
        }

    def detectar_descricao(self, descricao):
        if not isinstance(descricao, str) or descricao.strip() == "":
            return None

        desc = Normalizer.normalize(descricao)

        # 1) Prioridade: variações -> marca padronizada
        for marca_padrao, variacoes in self.marca_variacoes.items():
            for v in sorted(variacoes, key=len, reverse=True):
                if re.search(rf"\b{re.escape(v)}\b", desc):
                    return marca_padrao.upper()

        # 2) Marcas adicionais
        for marca in sorted(self.marcas_adicionais, key=len, reverse=True):
            if re.search(rf"\b{re.escape(marca)}\b", desc):
                return marca.upper()

        return None

    def _marca_ja_esta_na_descricao(self, descricao, marca):
        if not isinstance(descricao, str) or not descricao.strip():
            return False

        if not marca or str(marca).strip() == "":
            return False

        desc_norm = Normalizer.normalize(descricao)
        marca_norm = Normalizer.normalize(marca)

        return bool(re.search(rf"\b{re.escape(marca_norm)}\b", desc_norm))

    def _adicionar_marca_na_descricao(self, descricao, marca):
        if not isinstance(descricao, str):
            descricao = ""

        descricao = descricao.strip()

        if not marca or str(marca).strip() == "":
            return descricao

        marca = str(marca).strip().upper()

        if marca in {"GENERICO", "GENÉRICO"}:
            return descricao

        if self._marca_ja_esta_na_descricao(descricao, marca):
            return descricao

        if descricao:
            return f"{descricao} {marca}".strip()

        return marca

    def aplicar(self):
        def resolver_marca(row):
            marca_detectada = self.detectar_descricao(row["Descrição"])
            if marca_detectada:
                return marca_detectada

            marca_atual = row.get("Marca")
            if pd.notna(marca_atual) and str(marca_atual).strip() != "":
                return str(marca_atual).strip().upper()

            return "GENERICO"

        self.df["Marca"] = self.df.apply(resolver_marca, axis=1)

        self.df["Descrição"] = self.df.apply(
            lambda row: self._adicionar_marca_na_descricao(
                row["Descrição"],
                row["Marca"]
            ),
            axis=1
        )

        return self.df
