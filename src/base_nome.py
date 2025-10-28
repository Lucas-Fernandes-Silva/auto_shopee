import pandas as pd
from rapidfuzz import fuzz
import unicodedata
import re
from tqdm import tqdm
import itertools
from collections import Counter
import numpy as np


def normalizar(texto):
    texto = str(texto).upper().strip()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^A-Z0-9 ]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    if texto == 'NaN':
        texto = ""
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
        t
        for t in primeira
        if any(fuzz.ratio(t, w) / 100 >= sensibilidade for w in comuns)
    ]

    base = " ".join(base_ordenada).strip()
    base = re.sub(r"\b\d+([Xx/]\d+)?\b", "", base).strip()
    base = re.sub(r"\s+", " ", base).strip()

    return base


# --- Carrega base ---
df = pd.read_excel("pai_filho_variantes.xlsx")
df = df.head(20)


# --- Normaliza chave ---
df["Chave"] = np.where(
    df["Categoria"].isin(["CONEXÕES ESGOTO", "CONEXÕES ÁGUA"]),
    df["Categoria"].apply(normalizar) + " " + df["Descrição"].apply(normalizar),
    df["Descrição"].apply(normalizar),
)

# --- Ordena ---
df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(
    drop=True
)

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


df[["ID_Variacao", "Descrição", "Base", "Variante"]]
