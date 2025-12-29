import re
import pandas as pd

from src.utils.normalizer import Normalizer
from dados import dados

class BrandDetector:
    def __init__(self, df, marca_variacoes, marcas_adicionais):
        self.df = df
        self.marcas_adicionais = dados.marcas_adicionais
        self.marca_variacoes = dados.marca_variacoes

        # Marca PADRÃO -> variaçõese
        self.marca_variacoes = {
            Normalizer.normalize(marca): {
                Normalizer.normalize(v) for v in variacoes
            }
            for marca, variacoes in self.marca_variacoes.items()
        }

        # Marcas adicionais (sem variação)
        self.marcas_adicionais = {
            Normalizer.normalize(m) for m in self.marcas_adicionais
        }

    def detectar_descricao(self, descricao):
        if not isinstance(descricao, str) or descricao.strip() == "":
            return None

        desc = Normalizer.normalize(descricao)

        # 1️⃣ Prioridade: variações → marca padronizada
        for marca_padrao, variacoes in self.marca_variacoes.items():
            for v in variacoes:
                if re.search(rf"\b{re.escape(v)}\b", desc):
                    return marca_padrao

        # 2️⃣ Marcas adicionais
        for marca in self.marcas_adicionais:
            if re.search(rf"\b{re.escape(marca)}\b", desc):
                return marca

        return None

    def aplicar(self):
        def resolver(row):
            # tenta detectar pela descrição
            marca_detectada = self.detectar_descricao(row["Descrição"])
            if marca_detectada:
                return marca_detectada

            # mantém marca existente
            marca_atual = row.get("Marca")
            if pd.notna(marca_atual) and str(marca_atual).strip() != "":
                return marca_atual

            # fallback final
            return "GENÉRICO"

        self.df["Marca"] = self.df.apply(resolver, axis=1)
        return self.df
