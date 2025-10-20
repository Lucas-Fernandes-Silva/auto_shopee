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

df["Descricao_norm"] = df["Descrição"].apply(normalizar)
df["Categoria_norm"] = df["Categoria"].apply(normalizar)

# === Separar produtos com e sem categoria ===
com_categoria = df[df["Categoria_norm"] != ""].reset_index(drop=True)  # <-- resetado
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
        if score > 60:
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
sem_categoria["Similaridade"] = scores
sem_categoria["Descricao_Referencia"] = similares

com_categoria["Categoria_Preenchida"] = com_categoria["Categoria"]
com_categoria["Similaridade"] = 100
com_categoria["Descricao_Referencia"] = com_categoria["Descrição"]

df_final = pd.concat([com_categoria, sem_categoria], ignore_index=True)

# === Agrupar produtos em variações ===
grupos = []
for categoria, grupo in df_final.groupby("Categoria_Preenchida"):
    nomes = grupo["Descricao_norm"].tolist()
    usados = set()
    for i, nome in enumerate(nomes):
        if i in usados:
            continue
        grupo_variacao = [i]
        for j in range(i+1, len(nomes)):
            if fuzz.token_sort_ratio(nome, nomes[j]) > 85:
                grupo_variacao.append(j)
        usados.update(grupo_variacao)
        grupo_id = f"{categoria[:5]}_{len(grupos)+1}"
        for idx in grupo_variacao:
            grupos.append((grupo.index[idx], grupo_id))

df_final["Grupo_Variacao"] = ""
for idx, gid in grupos:
    df_final.loc[idx, "Grupo_Variacao"] = gid

# === Relatórios de conflito ===
conflitos_cat = df_final[(df_final["Similaridade"] < 60) & (df_final["Categoria_norm"] == "")]

possiveis_erros = []
for categoria, grupo in df_final.groupby("Categoria_Preenchida"):
    descricoes = grupo["Descricao_norm"].tolist()
    for i in range(len(descricoes)):
        for j in range(i + 1, len(descricoes)):
            sim = fuzz.token_sort_ratio(descricoes[i], descricoes[j])
            if 80 < sim < 90:
                possiveis_erros.append({
                    "Categoria": categoria,
                    "Descricao_1": grupo.iloc[i]["Descrição"],
                    "Descricao_2": grupo.iloc[j]["Descrição"],
                    "Similaridade": sim
                })

df_conflitos = pd.DataFrame(possiveis_erros)

with pd.ExcelWriter("produtos_com_categorias_e_variacoes.xlsx") as writer:
    df_final.to_excel(writer, sheet_name="Produtos", index=False)
    conflitos_cat.to_excel(writer, sheet_name="CategoriasBaixaSimilaridade", index=False)
    df_conflitos.to_excel(writer, sheet_name="PossiveisErrosGrupos", index=False)

print("✅ Arquivo gerado: produtos_com_categorias_e_variacoes.xlsx")
