import pandas as pd
from rapidfuzz import fuzz, process
import unicodedata

def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

# === Ler arquivo ===
df = pd.read_excel("produtos_com_marcas.xlsx")

# Criar colunas temporárias apenas para uso interno
df["Descricao_norm"] = df["Descrição"].apply(normalizar)
df["Categoria_norm"] = df["Categoria"].apply(normalizar)

# === Separar produtos com e sem categoria ===
com_categoria = df[df["Categoria_norm"] != ""].reset_index(drop=True)
sem_categoria = df[df["Categoria_norm"] == ""].reset_index(drop=True)

preenchidas, scores, similares = [], [], []

# === Preencher categorias vazias ===
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

# Copiar dados para com_categoria
com_categoria["Categoria_Preenchida"] = com_categoria["Categoria"]

# === Unir novamente ===
df_final = pd.concat([com_categoria, sem_categoria], ignore_index=True)

# === Ajustes finais ===
df_final["Categoria"] = df_final["Categoria_Preenchida"]

# Remover colunas auxiliares antes de salvar
colunas_remover = ["Descricao_norm", "Categoria_norm", "Categoria_Preenchida"]
df_final = df_final.drop(columns=colunas_remover)

# === Exportar ===
with pd.ExcelWriter("produtos_categorias.xlsx") as writer:
    df_final.to_excel(writer, sheet_name="Produtos", index=False)

print("✅ Arquivo gerado: produtos_categorias.xlsx")
