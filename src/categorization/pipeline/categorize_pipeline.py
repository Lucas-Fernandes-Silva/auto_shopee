import pandas as pd


class CategorizationPipeline:
    def __init__(self, domain_classifier):
        self.domain_classifier = domain_classifier

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")

        resultado = {}

        dominio, score_dominio = self.domain_classifier.classificar(descricao)

        resultado["Dominio"] = dominio
        resultado["Score_Dominio"] = score_dominio

        return pd.Series(resultado)

    def aplicar(self, df: pd.DataFrame):
        dominios = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, dominios], axis=1)

    def get_relatorio_fallback(self):
        return self.domain_classifier.get_relatorio_fallback()
