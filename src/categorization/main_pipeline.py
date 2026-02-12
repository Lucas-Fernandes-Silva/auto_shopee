import pandas as pd  # noqa: I001

from src.categorization.categorize_pipeline import CategorizationPipeline
from src.categorization.DomainClassifier import DomainClassifier
from src.categorization.DomainMapLoader import DomainMapLoader
# from src.categorization.extratores.CorExtractor import CorExtractor
# from src.categorization.extratores.eletrica.disjuntores.CentrinhoVariationExtractor import (
#     CentrinhoVariationExtractor,
# )
# from src.categorization.extratores.eletrica.disjuntores.PolosDisjuntorExtractor import (
#     PolosDisjuntorExtractor,
# )
# from src.categorization.extratores.eletrica.lampadas.FormatoLampadaExtractor import (
#     FormatoLampadaExtractor,
# )
# from src.categorization.extratores.eletrica.lampadas.PotenciaLampadaExtractor import (
#     PotenciaLampadaExtractor,
# )
# from src.categorization.extratores.eletrica.lampadas.TemperaturaCorExtractor import (
#     TemperaturaCorExtractor,
# )
# from src.categorization.extratores.eletrica.lampadas.TipoLampadaExtractor import (
#     TipoLampadaExtractor,
# )
# from src.categorization.extratores.medida.MedidaExtractor import MedidaExtractor
# from src.categorization.extratores.parafusos.ArruelaVariationExtractor import (
#     ArruelaVariationExtractor,
# )
# from src.categorization.extratores.parafusos.BuchaVariationExtractor import BuchaVariationExtractor
# from src.categorization.extratores.parafusos.ChumbadorVariationExtractor import (
#     ChumbadorAncoraVariationExtractor,
# )
# from src.categorization.extratores.parafusos.ParafusoVariationExtractor import (
#     ParafusoVariationExtractor,
# )
# from src.categorization.extratores.parafusos.PorcaVariationExtractor import PorcaVariationExtractor
# from src.categorization.extratores.parafusos.RebiteVariationExtractor import (
#     RebiteVariationExtractor,
# )
# from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor
# from src.categorization.extratores.tomadas.PolosExtractor import PolosExtractor
# from src.categorization.extratores.tomadas.TipoTomadaExtractor import TipoTomadaExtractor
# from src.categorization.VariationPipeline import VariationPipeline

# ---- Domínios
loader = DomainMapLoader("/home/lucas-silva/auto_shopee/planilhas/outputs/Categorizados.xlsx")
df_dominios = loader.carregar()
domain_classifier = DomainClassifier(df_dominios)

# ---- Pipelines
categorization_pipeline = CategorizationPipeline(domain_classifier)

# variation_pipeline = VariationPipeline(
#     dominio_extractors={
#         "PARAFUSOS": [
#             ParafusoVariationExtractor(),
#             ChumbadorAncoraVariationExtractor(),
#             RebiteVariationExtractor(),
#             BuchaVariationExtractor(),
#             PorcaVariationExtractor(),
#             ArruelaVariationExtractor(),
#         ],
#         "TOMADAS": [
#             TipoTomadaExtractor(),
#             AmperagemExtractor(),
#             PolosExtractor(),
#             MedidaExtractor(),
#         ],
#         "ELETRICA": [
#             CentrinhoVariationExtractor(),
#             AmperagemExtractor(),
#             PolosDisjuntorExtractor(),
#             FormatoLampadaExtractor(),
#             PotenciaLampadaExtractor(),
#             TemperaturaCorExtractor(),
#             TipoLampadaExtractor(),
#             MedidaExtractor(),
#             CorExtractor(),
#         ],
#     }
# )

# ---- Executar
df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")

df_dominios = categorization_pipeline.aplicar(df)
# df_final = variation_pipeline.aplicar(df_dominios)
df_final = df_dominios

df_final.to_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados.xlsx",
    index=False,
)

# ---- Relatório fallback
df_fallback = categorization_pipeline.get_relatorio_fallback()
if not df_fallback.empty:
    df_fallback.to_excel(
        "/home/lucas-silva/auto_shopee/planilhas/outputs/Relatorio_Dominios_Ambiguos.xlsx",
        index=False,
    )
