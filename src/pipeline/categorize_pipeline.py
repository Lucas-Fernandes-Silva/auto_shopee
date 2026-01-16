import pandas as pd

from src.categorization.DomainClassifier import DomainClassifier
from src.categorization.DomainMapLoader import DomainMapLoader
from src.categorization.extratores import RebiteVariationExtractor
from src.categorization.extratores.ArruelaVariationExtractor import ArruelaVariationExtractor
from src.categorization.extratores.BuchaVariationExtractor import BuchaVariationExtractor
from src.categorization.extratores.ChumbadorVariationExtractor import ChumbadorAncoraVariationExtractor
from src.categorization.extratores.ParafusoVariationExtractor import ParafusoVariationExtractor
from src.categorization.extratores.PorcaVariationExtractor import PorcaVariationExtractor
from src.categorization.extratores.RebiteVariationExtractor import RebiteVariationExtractor


class CategorizationPipeline:
    def __init__(self, domain_classifier):
        self.domain_classifier = domain_classifier

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")

        resultado = {}

        dominio, score_dominio = self.domain_classifier.classificar(descricao)

        resultado["Dominio"] = dominio
        resultado["Score_Dominio"] = score_dominio
        if dominio == "PARAFUSOS":
            variacoes = {}

            variacoes.update(
                ParafusoVariationExtractor().extrair(descricao)
            )
            variacoes.update(
                PorcaVariationExtractor().extrair(descricao)
            )
            variacoes.update(
                BuchaVariationExtractor().extrair(descricao)
            )
            variacoes.update(
                ArruelaVariationExtractor().extrair(descricao)
            )
            variacoes.update(
                ChumbadorAncoraVariationExtractor().extrair(descricao)
            )
            variacoes.update(
                RebiteVariationExtractor().extrair(descricao)
            )



        resultado.update(variacoes)
        return pd.Series(resultado)

    def aplicar(self, df: pd.DataFrame):
        atributos = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, atributos], axis=1)

    def get_relatorio_fallback(self):
        return self.domain_classifier.get_relatorio_fallback()


loader = DomainMapLoader("/home/lucas-silva/auto_shopee/planilhas/outputs/Categorizados.xlsx")
df_dominios = loader.carregar()

domain_classifier = DomainClassifier(df_dominios)

pipeline = CategorizationPipeline(domain_classifier=domain_classifier)

df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")

df_final = pipeline.aplicar(df)
df_final.to_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados.xlsx", index=False
)

df_fallback = pipeline.get_relatorio_fallback()

if not df_fallback.empty:
    df_fallback.to_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Relatorio_Dominios_Ambiguos.xlsx",
        index=False,
    )

