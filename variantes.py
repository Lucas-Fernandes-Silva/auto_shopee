import pandas as pd
from rapidfuzz import fuzz
import unicodedata
from tqdm import tqdm

# --- Função para normalizar textos ---
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

# --- Carrega o Excel ---
df = pd.read_excel("produtos_categorias.xlsx")

# --- Cria chave composta com as 3 colunas ---
df["chave"] = (
    df["Descrição"].apply(normalizar) + " " +
    df["Categoria"].apply(normalizar)
)

# --- Parâmetro de similaridade ---
LIMIAR = 90

# --- Inicializa controle ---
df["ID_Variacao"] = None
df["Tipo"] = None  # Pai ou Filho
df["SKU_Pai"] = None
grupo_id = 1
usados = set()

# --- Loop principal de agrupamento ---
print("🔄 Agrupando variações...")

for i, linha in tqdm(df.iterrows(), total=len(df)):
    if i in usados:
        continue

    chave_ref = linha["chave"]
    similares = df.index[df["chave"].apply(lambda x: fuzz.token_sort_ratio(chave_ref, x) >= LIMIAR)].tolist()

    # Define o produto principal (primeiro do grupo)
    sku_pai = linha.get("Sku", linha.get("Código", i))  # usa coluna SKU ou índice
    df.at[i, "Tipo"] = "PAI"
    df.at[i, "SKU_Pai"] = sku_pai
    df.at[i, "ID_Variacao"] = grupo_id

    # Marca os produtos similares como filhos
    for idx in similares:
        if idx not in usados:
            if idx != i:
                df.at[idx, "Tipo"] = "FILHO"
                df.at[idx, "SKU_Pai"] = sku_pai
            df.at[idx, "ID_Variacao"] = grupo_id
            usados.add(idx)

    grupo_id += 1

# --- Ordena resultado ---
df = df.sort_values(by=["ID_Variacao", "Tipo"], ascending=[True, True]).reset_index(drop=True)


# --- Salva resultado ---
arquivo_saida = "pai_filho_variantes.xlsx"
df.to_excel(arquivo_saida, index=False)

print(f"✅ Agrupamento concluído com sucesso!")
print(f"📂 Arquivo salvo como: {arquivo_saida}")
print(f"📦 Total de grupos de variações criados: {grupo_id - 1}")
