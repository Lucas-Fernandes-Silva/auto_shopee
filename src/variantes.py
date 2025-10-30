import unicodedata

import pandas as pd
from rapidfuzz import fuzz, process

from logger import logger


# --- Função para normalizar textos ---
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto


# --- Carrega o Excel ---
df = pd.read_excel("produtos_categorias.xlsx")

# --- Cria chave composta com as 3 colunas ---
df["Chave"] = (
    df["Descrição"].apply(normalizar) + " " + df["Categoria"].apply(normalizar)
)

# --- Parâmetro de similaridade ---
LIMIAR = 85

# --- Inicializa controle ---
df["ID_Variacao"] = pd.NA
df["Tipo"] = pd.NA
df["SKU_Pai"] = pd.NA

usados = set()
grupo_id = 1

chaves = df["Chave"].tolist()

for i, chave_ref in enumerate(chaves):
    if i in usados:
        continue

    similares = process.extract(
        chave_ref, chaves, scorer=fuzz.token_sort_ratio, score_cutoff=LIMIAR, limit=None
    )
    similares_idx = [
        j
        for j, _ in enumerate(chaves)
        if (chaves[j], 100) in similares
        or fuzz.token_sort_ratio(chave_ref, chaves[j]) >= LIMIAR
    ]

    sku_pai = df.at[i, "Sku"] if "Sku" in df.columns else df.at[i, "Código"]

    mask = df.index.isin(similares_idx)
    df.loc[mask, "ID_Variacao"] = grupo_id
    df.loc[mask, "SKU_Pai"] = sku_pai
    df.loc[mask, "Tipo"] = df.index.to_series().apply(
        lambda idx: "PAI" if idx == i else "FILHO"
    )

    usados.update(similares_idx)
    grupo_id += 1

df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(
    drop=True
)


arquivo_saida = "planilhas/pai_filho_variantes.xlsx"
df.to_excel(arquivo_saida, index=False)

logger.info("✅ Agrupamento concluído com sucesso!")
logger.info(f"📂 Arquivo salvo como: {arquivo_saida}")
logger.info(f"📦 Total de grupos de variações criados: {grupo_id - 1}")
