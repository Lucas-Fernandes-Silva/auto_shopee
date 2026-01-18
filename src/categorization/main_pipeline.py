import pandas as pd

from src.categorization.DomainClassifier import DomainClassifier
from src.categorization.DomainMapLoader import DomainMapLoader
from src.categorization.VariationPipeline import VariationPipeline

from src.categorization.categorize_pipeline import CategorizationPipeline
from src.categorization.extratores.ArruelaVariationExtractor import ArruelaVariationExtractor
from src.categorization.extratores.BuchaVariationExtractor import BuchaVariationExtractor
from src.categorization.extratores.ChumbadorVariationExtractor import (
    ChumbadorAncoraVariationExtractor,
)
from src.categorization.extratores.ParafusoVariationExtractor import ParafusoVariationExtractor
from src.categorization.extratores.PorcaVariationExtractor import PorcaVariationExtractor
from src.categorization.extratores.RebiteVariationExtractor import RebiteVariationExtractor


# ---- Domínios
loader = DomainMapLoader(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Categorizados.xlsx"
)
df_dominios = loader.carregar()
domain_classifier = DomainClassifier(df_dominios)

# ---- Pipelines
categorization_pipeline = CategorizationPipeline(domain_classifier)

variation_pipeline = VariationPipeline(
    dominio_extractors={
        "PARAFUSOS": [
            ParafusoVariationExtractor(),
            ChumbadorAncoraVariationExtractor(),
            RebiteVariationExtractor(),
            BuchaVariationExtractor(),
            PorcaVariationExtractor(),
            ArruelaVariationExtractor(),
        ]
    }
)

# ---- Executar
df = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx"
)

df_dominios = categorization_pipeline.aplicar(df)
df_final = variation_pipeline.aplicar(df_dominios)

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
