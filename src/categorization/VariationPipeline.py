import pandas as pd


class VariationPipeline:
    def __init__(self, dominio_extractors: dict):
        """
        dominio_extractors = {
            "PARAFUSOS": [extractor1, extractor2, ...],
            "REBITE": [...],
        }
        """
        self.dominio_extractors = dominio_extractors

    def extrair(self, descricao: str, dominio: str) -> dict:
        if not isinstance(descricao, str):
            return {}

        extractors = self.dominio_extractors.get(dominio, [])
        variacoes = {}

        for extractor in extractors:
            try:
                resultado = extractor.extrair(descricao)
                if resultado:
                    variacoes.update(resultado)
            except Exception:
                # segurança: não quebra pipeline
                continue

        return variacoes

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")
        dominio = row.get("Dominio")

        variacoes = self.extrair(descricao, dominio)
        return pd.Series(variacoes)

    def aplicar(self, df: pd.DataFrame):
        variacoes = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, variacoes], axis=1)
