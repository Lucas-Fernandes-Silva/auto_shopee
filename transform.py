import pandas as pd
import numpy as np
import re
import unicodedata
from dados import marcas_adicionais, marca_variacoes
from main import df_enriquecido
from rapidfuzz import fuzz, process
from tqdm import tqdm
from difflib import SequenceMatcher

df = df_enriquecido

def limpar_texto(txt):
    if not isinstance(txt, str):
        return ""
    txt = unicodedata.normalize('NFD', txt)
    txt = txt.encode('ascii', 'ignore').decode('utf-8')
    txt = txt.upper()
    txt = re.sub(r'[^A-Z0-9 ]', '', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt


marcas_adicionais = [limpar_texto(m) for m in marcas_adicionais]
marcas_planilha = df['Marca'].dropna().unique().tolist()
marcas_planilha.remove('5+')
marcas_planilha = [limpar_texto(m) for m in marcas_planilha if isinstance(m, str) and m.strip()]
marcas = list(set(marcas_planilha + marcas_adicionais))


for marca_principal, variacoes in marca_variacoes.items():
    marcas.append(marca_principal)
    marcas.extend([limpar_texto(v) for v in variacoes])

marcas = list(set(marcas))

def detectar_marca(descricao):
    desc_limpa = limpar_texto(descricao)

    for marca_padrao, variacoes in marca_variacoes.items():
        for v in variacoes:
            if limpar_texto(v) in desc_limpa:
                return marca_padrao

    for marca in marcas:
        if marca and marca in desc_limpa:
            return marca

    return np.nan

df_filtrado = df.copy()

df_filtrado['Marca Detectada'] = df_filtrado['Descrição'].apply(detectar_marca)

df_filtrado['Marca'] = df_filtrado['Marca'].fillna(df_filtrado['Marca Detectada'])

df_filtrado['Marca'] = df_filtrado['Marca'].fillna('GENÉRICO')
df.update(df_filtrado)

df_marcas = df.copy()


def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

df = df_marcas

df["Descricao_norm"] = df["Descrição"].apply(normalizar)
df["Categoria_norm"] = df["Categoria"].apply(normalizar)

com_categoria = df[df["Categoria_norm"] != ""].reset_index(drop=True)
sem_categoria = df[df["Categoria_norm"] == ""].reset_index(drop=True)

preenchidas, scores, similares = [], [], []

for desc in sem_categoria["Descricao_norm"]:
    match = process.extractOne(
        desc,
        com_categoria["Descricao_norm"],
        scorer=fuzz.token_sort_ratio
    )
    if match:
        nome_similar, score, idx = match
        if score > 40:
            cat = com_categoria.iloc[idx]["Categoria"]
        else:
            cat = "Sem categoria semelhante"
        preenchidas.append(cat)
        scores.append(score)
        similares.append(com_categoria.iloc[idx]["Descrição"])
    else:
        preenchidas.append("Sem categoria semelhante")
        scores.append(0)
        similares.append("")

sem_categoria["Categoria_Preenchida"] = preenchidas

com_categoria["Categoria_Preenchida"] = com_categoria["Categoria"]

df_final = pd.concat([com_categoria, sem_categoria], ignore_index=True)

df_final["Categoria"] = df_final["Categoria_Preenchida"]

colunas_remover = ["Descricao_norm", "Categoria_norm", "Categoria_Preenchida"]
df_final = df_final.drop(columns=colunas_remover)

df_final

df = df_final

df["Chave"] = (
    df["Descrição"].apply(normalizar) + " " +
    df["Categoria"].apply(normalizar)
)

LIMIAR = 90

df["ID_Variacao"] = None
df["Tipo"] = None  
df["SKU_Pai"] = None
grupo_id = 1
usados = set()

for i, linha in tqdm(df.iterrows(), total=len(df)):
    if i in usados:
        continue

    chave_ref = linha["Chave"]
    similares = df.index[df["Chave"].apply(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= LIMIAR)].tolist()

    sku_pai = linha.get("Sku", linha.get("Código", i))  
    df.at[i, "Tipo"] = "PAI"
    df.at[i, "SKU_Pai"] = sku_pai
    df.at[i, "ID_Variacao"] = grupo_id

    for idx in similares:
        if idx not in usados:
            if idx != i:
                df.at[idx, "Tipo"] = "FILHO"
                df.at[idx, "SKU_Pai"] = sku_pai
            df.at[idx, "ID_Variacao"] = grupo_id
            usados.add(idx)

    grupo_id += 1

df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(drop=True)


LIMIAR = 90         
SENSIBILIDADE = 0.4  

df["Chave"] = (
    df["Descrição"].apply(normalizar) + " " +
    df["Categoria"].apply(normalizar)
)

df["ID_Variacao"] = None
df["Tipo"] = None
df["SKU_Pai"] = None
grupo_id = 1
usados = set()

for i, linha in tqdm(df.iterrows(), total=len(df)):
    if i in usados:
        continue

    chave_ref = linha["Chave"]
    similares = df.index[df["Chave"].apply(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= LIMIAR)].tolist()

    sku_pai = linha.get("Sku", linha.get("Código", i))
    df.at[i, "Tipo"] = "PAI"
    df.at[i, "SKU_Pai"] = sku_pai
    df.at[i, "ID_Variacao"] = grupo_id

    for idx in similares:
        if idx not in usados:
            if idx != i:
                df.at[idx, "Tipo"] = "FILHO"
                df.at[idx, "SKU_Pai"] = sku_pai
            df.at[idx, "ID_Variacao"] = grupo_id
            usados.add(idx)

    grupo_id += 1


df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(drop=True)

def parte_comum(strings, sensibilidade=SENSIBILIDADE):
    if not strings:
        return ""
    base = strings[0]
    for s in strings[1:]:
        seq = SequenceMatcher(None, base, s)
        match = seq.find_longest_match(0, len(base), 0, len(s))
        comum = base[match.a: match.a + match.size]

        tamanho_medio = (len(base) + len(s)) / 2
        proporcao = len(comum) / tamanho_medio

        if proporcao >= sensibilidade:
            base = comum
        else:
            base = comum[:int(len(comum) * sensibilidade)]

    return base.strip()

df["Base"] = ""
df["Variante"] = ""

for gid, grupo in tqdm(df.groupby("ID_Variacao"), total=df["ID_Variacao"].nunique()):
    chaves = grupo["Chave"].tolist()
    comum = parte_comum(chaves, SENSIBILIDADE)

    for idx, linha in grupo.iterrows():
        texto = linha["Chave"]
        variante = texto.replace(comum, "").strip()
        df.at[idx, "Base"] = comum
        df.at[idx, "Variante"] = variante


print(df)
# arquivo_saida = "final.xlsx"
# df.to_excel(arquivo_saida, index=False)
