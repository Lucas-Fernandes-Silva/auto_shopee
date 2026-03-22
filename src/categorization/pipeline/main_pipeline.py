import pandas as pd

from src.agrupamento.Agrupamento import aplicar_chave_agrupamento
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
from src.categorization.extratores.eletrica.lampadas.LumensExtractor import LumensExtractor
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
from src.categorization.pipeline.RemovedorComercial import aplicar_limpeza_nome_base
from src.categorization.pipeline.VariationPipeline import VariationPipeline
from src.transform.baseNome import aplicar_nomes

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
            MedidaExtractor(),
            MedidaAxBExtractor(),
            PolosExtractor(),
            CorExtractor(),
        ],
        "ELETRICA": [
            CentrinhoVariationExtractor(),
            AmperagemExtractor(),
            PolosExtractor(),
            PolosDisjuntorExtractor(),
            LumensExtractor(),
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


# 2) Limpeza de ruídos da descrição
df_limpo = aplicar_limpeza_nome_base(df_dominios)


df_classificado = variation_pipeline.aplicar(df_limpo)

df_classificado.to_excel(OUT_CLASSIFICADO, index=False)


df_nomes = aplicar_nomes(df_classificado)


# df_nomes = df_nomes.loc[:, ~df_nomes.columns.duplicated()]

df_agrupado = aplicar_chave_agrupamento(df_nomes)


agrupador = AgrupadorFuzzyPaiFilho(
    df_agrupado,
    col_codigo="Codigo Produto",
    col_base="Nome_Produto_Base",
    col_variacao="Nome_Variacao",
    col_chave="Chave_Agrupamento",
    threshold=90,
)
df_agrupado = agrupador.processar()

# 6) Ajuste para produtos únicos
df_final = ajustar_produtos_unicos(df_agrupado)

df_final = df_agrupado
# 7) Salvar resultado final
df_final.to_excel(OUT_FINAL_COM_NOMES, index=False)

# 8) Relatório fallback
df_fallback = categorization_pipeline.get_relatorio_fallback()
if not df_fallback.empty:
    df_fallback.to_excel(OUT_FALLBACK, index=False)

print(f"OK: {OUT_FINAL_COM_NOMES}")


