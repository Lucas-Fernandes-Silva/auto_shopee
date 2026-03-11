import pandas as pd

from src.categorization.extratores.CorExtractor import CorExtractor
from src.categorization.extratores.eletrica.disjuntores.CentrinhoVariationExtractor import (
    CentrinhoVariationExtractor,
)
from src.categorization.extratores.eletrica.disjuntores.PolosDisjuntorExtractor import (
    PolosDisjuntorExtractor,
)
from src.categorization.extratores.eletrica.lampadas.FormatoLampadaExtractor import (
    FormatoLampadaExtractor,
)
from src.categorization.extratores.eletrica.lampadas.PotenciaLampadaExtractor import (
    PotenciaLampadaExtractor,
)
from src.categorization.extratores.eletrica.lampadas.TemperaturaCorExtractor import (
    TemperaturaCorExtractor,
)
from src.categorization.extratores.eletrica.lampadas.TipoLampadaExtractor import (
    TipoLampadaExtractor,
)
from src.categorization.extratores.medida.MedidaAxBExtractor import MedidaAxBExtractor
from src.categorization.extratores.medida.MedidaExtractor import MedidaExtractor
from src.categorization.extratores.parafusos.ArruelaVariationExtractor import (
    ArruelaVariationExtractor,
)
from src.categorization.extratores.parafusos.BuchaVariationExtractor import (
    BuchaVariationExtractor,
)
from src.categorization.extratores.parafusos.ChumbadorVariationExtractor import (
    ChumbadorAncoraVariationExtractor,
)
from src.categorization.extratores.parafusos.ParafusoVariationExtractor import (
    ParafusoVariationExtractor,
)
from src.categorization.extratores.parafusos.PorcaVariationExtractor import (
    PorcaVariationExtractor,
)
from src.categorization.extratores.parafusos.RebiteVariationExtractor import (
    RebiteVariationExtractor,
)
from src.categorization.extratores.tomadas.AmperagemExtractor import AmperagemExtractor
from src.categorization.extratores.tomadas.PolosExtractor import PolosExtractor
from src.categorization.extratores.tomadas.TipoTomadaExtractor import TipoTomadaExtractor
from src.categorization.pipeline.ajustar_produtos_unicos import ajustar_produtos_unicos
from src.categorization.pipeline.categorize_pipeline import CategorizationPipeline
from src.categorization.pipeline.DomainClassifier import DomainClassifier
from src.categorization.pipeline.DomainMapLoader import DomainMapLoader
from src.categorization.pipeline.Fuzzy import AgrupadorFuzzyPaiFilho
from src.categorization.pipeline.VariationPipeline import VariationPipeline

# ✅ importe o aplicar_nomes do seu baseNome.py
# Se baseNome.py estiver na raiz do projeto:
from src.transform.baseNome import aplicar_nomes

# Se estiver dentro de src/naming, por exemplo:
# from src.categorization.naming.baseNome import aplicar_nomes


# =========================
# Paths (ajuste conforme seu projeto)
# =========================
DOMINIOS_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Categorizados.xlsx"
INPUT_XLSX = "/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx"

OUT_CLASSIFICADO = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados.xlsx"
OUT_FINAL_COM_NOMES = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Com_Nomes.xlsx"
OUT_FALLBACK = "/home/lucas-silva/auto_shopee/planilhas/outputs/Relatorio_Dominios_Ambiguos.xlsx"


# =========================
# Setup domínios
# =========================
loader = DomainMapLoader(DOMINIOS_XLSX)
df_dominios = loader.carregar()
domain_classifier = DomainClassifier(df_dominios)

categorization_pipeline = CategorizationPipeline(domain_classifier)

# =========================
# Pipeline de variações (por domínio)
# =========================
variation_pipeline = VariationPipeline(
    dominio_extractors={
        "PARAFUSOS": [
            ParafusoVariationExtractor(),
            MedidaAxBExtractor(),
            ChumbadorAncoraVariationExtractor(),
            RebiteVariationExtractor(),
            BuchaVariationExtractor(),
            PorcaVariationExtractor(),
            ArruelaVariationExtractor(),
            MedidaExtractor(),
            CorExtractor(),
        ],
        "TOMADAS": [
            TipoTomadaExtractor(),
            AmperagemExtractor(),
            MedidaAxBExtractor(),
            PolosExtractor(),
            CorExtractor(),
        ],
        "ELETRICA": [
            CentrinhoVariationExtractor(),
            AmperagemExtractor(),
            PolosDisjuntorExtractor(),
            PolosExtractor(),
            FormatoLampadaExtractor(),
            PotenciaLampadaExtractor(),
            TemperaturaCorExtractor(),
            TipoLampadaExtractor(),
            MedidaAxBExtractor(),
            MedidaExtractor(),
            CorExtractor(),
        ],
        "HIDRAULICA": [
            MedidaAxBExtractor(),
            MedidaExtractor(),
            CorExtractor(),
        ],
    },
)

# =========================
# Execução
# =========================
df = pd.read_excel(INPUT_XLSX, dtype=str)

# 1) Classificação domínio
df_dominios = categorization_pipeline.aplicar(df)

# 2) Extração de atributos (variações) por domínio
df_classificado = variation_pipeline.aplicar(df_dominios)

# (opcional) salvar intermediário, ajuda a debugar
df_classificado.to_excel(OUT_CLASSIFICADO, index=False)

df_final = aplicar_nomes(df_classificado)

df_dominios = categorization_pipeline.aplicar(df)
df_classificado = variation_pipeline.aplicar(df_dominios)
df_final = aplicar_nomes(df_classificado)

agrupador = AgrupadorFuzzyPaiFilho(
    df_final,
    col_codigo="Codigo Produto",
    col_base="Nome_Produto_Base",
    col_variacao="Nome_Variacao",
    col_dominio="Dominio",
    coluna_marca="Marca",
    threshold=90,
)


df_dominios = categorization_pipeline.aplicar(df)
df_classificado = variation_pipeline.aplicar(df_dominios)
df_nomes = aplicar_nomes(df_classificado)
df_agrupado = agrupador.processar()
df_final = ajustar_produtos_unicos(df_agrupado)


df_final.to_excel(OUT_FINAL_COM_NOMES, index=False)




# 4) Relatório fallback de domínio
df_fallback = categorization_pipeline.get_relatorio_fallback()
if not df_fallback.empty:
    df_fallback.to_excel(OUT_FALLBACK, index=False)

print(f"OK: {OUT_FINAL_COM_NOMES}")
