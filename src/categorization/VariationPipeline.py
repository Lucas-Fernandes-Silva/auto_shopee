import pandas as pd


class VariationPipeline:
    def __init__(self, dominio_extractors: dict):
        self.dominio_extractors = dominio_extractors

    def extrair(self, descricao: str, dominio: str) -> dict:
        if not isinstance(descricao, str):
            return {}

        extractors = self.dominio_extractors.get(dominio, [])
        variacoes = {}

        for extractor in extractors:
            resultado = extractor.extrair(descricao)

            if not isinstance(resultado, dict):
                continue

            for chave, valor in resultado.items():
                if chave not in variacoes or variacoes[chave] is None:
                    variacoes[chave] = valor

        return variacoes

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")
        dominio = row.get("Dominio")

        variacoes = self.extrair(descricao, dominio)
        return pd.Series(variacoes)

    def aplicar(self, df: pd.DataFrame):
        variacoes = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, variacoes], axis=1)
