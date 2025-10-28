import pandas as pd
import numpy as np
import re
import unicodedata
from rapidfuzz import fuzz, process
from tqdm import tqdm
from collections import Counter
import itertools
from src.dados import marcas_adicionais, marca_variacoes
from src.env import fornecedores_web_scraping
from scripts.main import df_enriquecido
from logger import logger


def normalizar(texto: str) -> str:
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^A-Z0-9 ]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def limpar_texto(txt: str) -> str:
    return normalizar(txt)


def gtin(codigo: str) -> bool:
    return str(codigo).isdigit() and len(str(codigo)) in [8, 12, 13, 14]


df = df_enriquecido.copy()
df["GTIN_Válido"] = df["Código de Barras"].astype(str).apply(gtin)


def escolher_prioritario(grupo):
    fornecedores = grupo["Fornecedor"].tolist()
    preferidos = [f for f in fornecedores if f in fornecedores_web_scraping]
    return (
        grupo[grupo["Fornecedor"].isin(preferidos)].head(1)
        if preferidos
        else grupo.head(1)
    )


df_validos = df[df["GTIN_Válido"]]
df_filtrado = df_validos.groupby("Código de Barras", group_keys=False).apply(
    escolher_prioritario
)
df_final = pd.concat([df_filtrado, df[~df["GTIN_Válido"]]], ignore_index=True)
df = df_final.reset_index(drop=True)

marcas = set(map(limpar_texto, marcas_adicionais))

marcas_planilha = set(map(limpar_texto, df["Marca"].dropna().astype(str)))
marcas_planilha.discard("5+")
marcas |= marcas_planilha

for marca_principal, variacoes in marca_variacoes.items():
    marcas.add(limpar_texto(marca_principal))
    marcas |= {limpar_texto(v) for v in variacoes}


def detectar_marca(desc):
    desc_limpa = limpar_texto(desc)
    for marca_padrao, variacoes in marca_variacoes.items():
        if any(limpar_texto(v) in desc_limpa for v in variacoes):
            return marca_padrao
    for marca in marcas:
        if marca in desc_limpa:
            return marca
    return np.nan


df["Marca"] = (
    df["Marca"].fillna(df["Descrição"].apply(detectar_marca)).fillna("GENÉRICO")
)

df["Descricao_norm"] = df["Descrição"].apply(normalizar)
df["Categoria_norm"] = df["Categoria"].apply(normalizar)

com_categoria = df[df["Categoria_norm"] != ""].reset_index(drop=True)
sem_categoria = df[df["Categoria_norm"] == ""].reset_index(drop=True)


def preencher_categoria(desc):
    match = process.extractOne(
        desc, com_categoria["Descricao_norm"], scorer=fuzz.token_sort_ratio
    )
    if not match:
        return "Sem categoria semelhante"
    nome_similar, score, idx = match
    return (
        com_categoria.iloc[idx]["Categoria"]
        if score > 40
        else "Sem categoria semelhante"
    )


sem_categoria["Categoria"] = sem_categoria["Descricao_norm"].apply(preencher_categoria)
df = pd.concat([com_categoria, sem_categoria], ignore_index=True)
df.drop(columns=["Descricao_norm", "Categoria_norm"], inplace=True)


df["Chave"] = (
    df["Descrição"].apply(normalizar) + " " + df["Categoria"].apply(normalizar)
).str.strip()
df["ID_Variacao"] = None
df["Tipo"] = None
df["SKU_Pai"] = None

LIMIAR = 90
grupo_id, usados = 1, set()

for i, linha in tqdm(df.iterrows(), total=len(df), desc="Agrupando variações"):
    if i in usados:
        continue
    chave_ref = linha["Chave"]
    similares = df.index[
        df["Chave"].apply(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= LIMIAR)
    ].tolist()

    sku_pai = linha.get("Sku", linha.get("Código", i))
    df.loc[i, ["Tipo", "SKU_Pai", "ID_Variacao"]] = ["PAI", sku_pai, grupo_id]

    for idx in similares:
        if idx not in usados:
            df.loc[idx, ["Tipo", "SKU_Pai", "ID_Variacao"]] = [
                "FILHO" if idx != i else "PAI",
                sku_pai,
                grupo_id,
            ]
            usados.add(idx)
    grupo_id += 1

df.sort_values(["ID_Variacao", "Tipo"], inplace=True)
df.reset_index(drop=True, inplace=True)


def similaridade_media(strings):
    pares = list(itertools.combinations(strings, 2))
    if not pares:
        return 1.0
    return np.mean([fuzz.token_set_ratio(a, b) / 100 for a, b in pares])


def parte_comum(strings, sensibilidade=0.7):
    token_lists = [normalizar(s).split() for s in strings if s]
    if not token_lists:
        return ""
    todas_palavras = {
        p for tokens in token_lists for p in tokens if not re.match(r"^\d+[Xx/]\d+$", p)
    }
    contagem = Counter(
        {
            p: sum(
                fuzz.ratio(p, t) / 100 >= sensibilidade
                for tokens in token_lists
                for t in tokens
            )
            for p in todas_palavras
        }
    )
    limite = max(1, int(len(strings) * 0.8))
    comuns = [w for w, c in contagem.items() if c >= limite]
    base = " ".join(
        [
            t
            for t in token_lists[0]
            if any(fuzz.ratio(t, w) / 100 >= sensibilidade for w in comuns)
        ]
    )
    return re.sub(r"\b\d+([Xx/]\d+)?\b", "", base).strip()


df["Base"], df["Variante"] = "", ""

for gid, grupo in tqdm(
    df.groupby("ID_Variacao", group_keys=False), desc="Gerando bases"
):
    chaves = grupo["Chave"].tolist()
    media = similaridade_media(chaves)
    sensibilidade = 0.85 if media >= 0.9 else 0.75 if media >= 0.8 else 0.65
    comum = parte_comum(chaves, sensibilidade) or normalizar(grupo["Descrição"].iloc[0])

    df.loc[grupo.index, "Base"] = comum
    df.loc[grupo.index, "Variante"] = grupo["Chave"].apply(
        lambda x: x.replace(comum, "").strip()
    )

df.to_excel("final.xlsx", index=False)
logger.info("✅ Arquivo final.xlsx gerado com sucesso!")
