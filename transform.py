import pandas as pd
import numpy as np
import re
import unicodedata
from dados import marcas_adicionais, marca_variacoes
from main import df_enriquecido
from rapidfuzz import fuzz, process
from tqdm import tqdm
from rapidfuzz import fuzz
import itertools
from collections import Counter
from env import fornecedores_web_scraping


df = df_enriquecido


def gtin(codigo):
    return codigo.isdigit() and len(codigo) in [8, 12, 13, 14]

df['GTIN_Válido'] = df['Código de Barras'].astype(str).apply(gtin)

df_validos = df[df['GTIN_Válido']].copy()

def escolher_prioritario(grupo):
    if len(grupo) == 1:
        return grupo
    fornecedores = grupo['Fornecedor'].tolist()

    if any(f in fornecedores_web_scraping for f in fornecedores):
        return grupo[grupo['Fornecedor'].isin(fornecedores_web_scraping)].head(1)

    return grupo.head(1)

df_filtrado = df_validos.groupby('Código de Barras', group_keys=False).apply(escolher_prioritario)

df_final = pd.concat([df_filtrado, df[~df['GTIN_Válido']]], ignore_index=True)

df = df_final.reset_index(drop=True)


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

def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                    if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^A-Z0-9 ]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def similaridade_media(strings):
    """Calcula a similaridade média do grupo"""
    pares = list(itertools.combinations(strings, 2))
    if not pares:
        return 1.0
    scores = [fuzz.token_set_ratio(a, b) / 100 for a, b in pares]
    return sum(scores) / len(scores)


def parte_comum(strings, sensibilidade=0.7):
    """Extrai tokens comuns entre descrições, ignorando tamanhos e códigos numéricos"""
    if not strings:
        return ""

    # Tokeniza e normaliza
    token_lists = [normalizar(s).split() for s in strings]
    todas_palavras = set(sum(token_lists, []))

    # Remove tokens que são medidas ou números (ex: 3/4, 48X50)
    def eh_medida(p):
        return bool(re.match(r"^\d+[Xx/]\d+$", p)) or p.isdigit()

    todas_palavras = {p for p in todas_palavras if not eh_medida(p)}

    contagem = Counter()
    for palavra in todas_palavras:
        for tokens in token_lists:
            similar = any(fuzz.ratio(palavra, t) / 100 >= sensibilidade for t in tokens)
            if similar:
                contagem[palavra] += 1

    limite = max(1, int(len(strings) * 0.8))
    comuns = [w for w, c in contagem.items() if c >= limite]

    primeira = token_lists[0]
    base_ordenada = [
        t for t in primeira
        if any(fuzz.ratio(t, w) / 100 >= sensibilidade for w in comuns)
    ]

    base = " ".join(base_ordenada).strip()
    base = re.sub(r'\b\d+([Xx/]\d+)?\b', '', base).strip()
    base = re.sub(r'\s+', ' ', base).strip()

    return base

# --- Normaliza chave ---
df["Chave"] = np.where(
    df["Categoria"].isin(["CONEXÕES ESGOTO", "CONEXÕES ÁGUA"]),
    df["Categoria"].apply(normalizar) + " " + df["Descrição"].apply(normalizar),
    df["Descrição"].apply(normalizar)
)

# --- Ordena ---
df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(drop=True)

# --- Cria colunas ---
df["Base"] = ""
df["Variante"] = ""


for gid, grupo in tqdm(df.groupby("ID_Variacao", group_keys=False)):
    chaves = grupo["Chave"].tolist()
    media = similaridade_media(chaves)

    # Sensibilidade dinâmica
    if media >= 0.9:
        sensibilidade = 0.85
    elif media >= 0.8:
        sensibilidade = 0.75
    else:
        sensibilidade = 0.65

    comum = parte_comum(chaves, sensibilidade)

    # Se o grupo tiver só um item, usa a descrição completa como base
    if len(grupo) == 1 or not comum:
        comum = normalizar(grupo["Descrição"].iloc[0])

    for idx, linha in grupo.iterrows():
        texto = linha["Chave"]
        variante = texto.replace(comum, "").strip()
        df.at[idx, "Base"] = comum
        df.at[idx, "Variante"] = variante


# --- Resultado ---
df.to_excel('final.xlsx',index=False)