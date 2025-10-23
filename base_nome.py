import pandas as pd
from rapidfuzz import fuzz
import unicodedata
from tqdm import tqdm
from difflib import SequenceMatcher

# --- Parâmetro ajustável ---
LIMIAR = 90          # similaridade entre chaves (fuzz)
SENSIBILIDADE = 0.4  # sensibilidade da parte comum (0 a 1)

# --- Função para normalizar textos ---
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

# --- Carrega o Excel ---
df = pd.read_excel("pai_filho_variantes.xlsx")

# --- Cria chave composta ---
df["Chave"] = (
    df["Descrição"].apply(normalizar) + " " +
    df["Categoria"].apply(normalizar)
)

# --- Inicializa controle ---
df["ID_Variacao"] = None
df["Tipo"] = None
df["SKU_Pai"] = None
grupo_id = 1
usados = set()

# --- Agrupamento ---
print("🔄 Agrupando variações...")

for i, linha in tqdm(df.iterrows(), total=len(df)):
    if i in usados:
        continue

    chave_ref = linha["chave"]
    similares = df.index[df["chave"].apply(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= LIMIAR)].tolist()

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

# --- Ordena ---
df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(drop=True)

# --- Função com controle de sensibilidade ---
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

        # Mantém só se atingir a sensibilidade mínima
        if proporcao >= sensibilidade:
            base = comum
        else:
            base = comum[:int(len(comum) * sensibilidade)]

    return base.strip()

# --- Cria colunas base e variante ---
print("🧩 Gerando colunas base e variante...")
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

# --- Salva ---
arquivo_saida = "base_nome.xlsx"
df.to_excel(arquivo_saida, index=False)

print("✅ Agrupamento concluído com sucesso!")
print(f"📂 Arquivo salvo como: {arquivo_saida}")
print(f"📦 Total de grupos de variações criados: {grupo_id - 1}")
