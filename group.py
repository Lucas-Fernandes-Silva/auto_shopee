import pandas as pd
import re
from rapidfuzz import fuzz
from tqdm import tqdm
from logger import logger


arquivo = "produtos.xlsx"
df = pd.read_excel(arquivo)

if "Descrição" not in df.columns:
    raise ValueError("A planilha deve conter uma coluna chamada 'Descrição'")

df['Descrição'] = df['Descrição'].astype(str).str.strip()
produtos = df['Descrição'].tolist()


similaridade_minima = 60

# === 3. Agrupar produtos semelhantes (com barra de progresso) ===
grupos = []
visitados = set()
grupo_id = 0

print("\n🔍 Agrupando produtos semelhantes...\n")
for i, prod in tqdm(enumerate(produtos), total=len(produtos)):
    if i in visitados:
        continue

    grupo_id += 1
    grupo = [prod]
    visitados.add(i)

    for j, outro in enumerate(produtos):
        if j in visitados:
            continue
        if fuzz.token_sort_ratio(prod, outro) >= similaridade_minima:
            grupo.append(outro)
            visitados.add(j)

    grupos.append((grupo_id, grupo))


linhas = []
for gid, grupo in grupos:
    if len(grupo) == 1:
        linhas.append({
            "Descrição": grupo[0],
            "Base": grupo[0],
            "Variação": "",
            "Grupo": gid
        })
        continue


    ref = grupo[0].split()


    comuns = set(ref)
    for g in grupo[1:]:
        comuns &= set(g.split())

    for g in grupo:
        palavras = g.split()
        base = " ".join([p for p in palavras if p in comuns])
        variacao = " ".join([p for p in palavras if p not in comuns])
        linhas.append({
            "Descrição": g,
            "Base": base.strip(),
            "Variação": variacao.strip(),
            "Grupo": gid
        })

resultado = pd.DataFrame(linhas)

df_final = df.merge(resultado, on="Descrição", how="left")

col_sku = None
for nome in df_final.columns:
    if "SKU" in nome.upper():
        col_sku = nome
        break

if not col_sku:
    raise ValueError("A planilha precisa ter uma coluna com o SKU (nome contendo 'SKU')")


sku_principal = df_final.groupby("Grupo")[col_sku].transform("first")

# Verifica grupos únicos (sem variação)
tamanho_grupo = df_final.groupby("Grupo")[col_sku].transform("count")

# Se o grupo tiver só 1 item, o SKU principal é o próprio SKU
df_final["SKU Principal"] = sku_principal
df.loc[tamanho_grupo == 1, "SKU Principal"] = df.loc[tamanho_grupo == 1, col_sku]

# === 5. Renomear SKU atual para 'SKU Variação' (opcional, para clareza)
df_final = df_final.rename(columns={col_sku: "SKU Variação"})

# === 6. Reordenar colunas: colocar SKU Principal logo após Variação ===
cols = df_final.columns.tolist()
if "Variação" in cols and "SKU Principal" in cols:
    idx_var = cols.index("Variação")
    cols.insert(idx_var + 1, cols.pop(cols.index("SKU Principal")))
    df_final = df_final[cols]


# === 2. Garantir colunas esperadas ===
for col in ["Variação", "Grupo", "SKU Principal", "SKU Variação"]:
    if col not in df_final.columns:
        raise ValueError(f"A planilha deve conter a coluna '{col}' (execute os scripts anteriores antes).")

# === 3. Funções auxiliares ===
def detectar_tipo_variacao(var):
    if pd.isna(var) or str(var).strip() == "":
        return "", ""
    
    var = str(var).upper().strip()
    tem_numero = bool(re.search(r"\d", var))
    tem_letra = bool(re.search(r"[A-Z]", var))

    # Códigos de cores comuns
    cores = ["AM", "PT", "AZ", "VM", "VD", "BC", "PR", "CZ", "BR", "RS", "BE", "CO", "LA", "MA"]
    partes = var.split()
    contem_cor = any(p in cores for p in partes)

    if tem_numero and contem_cor:
        return "Tamanho + Cor", var
    elif tem_numero:
        return "Tamanho", var
    elif contem_cor:
        return "Cor", var
    else:
        return "Outros", var

# === 4. Criar colunas de variação ===
tipos, valores = zip(*df_final["Variação"].map(detectar_tipo_variacao))
df_final["Nome da variante 1"] = tipos
df_final["Valor da variante 1"] = valores

# === 5. Coluna “É Variação” ===
df_final["É Variação"] = df_final.groupby("Grupo")["Grupo"].transform("count").apply(lambda x: "Sim" if x > 1 else "Não")

# === 6. Reordenar colunas para melhor visualização ===
cols = df_final.columns.tolist()
if "Variação" in cols and "Nome da variante 1" in cols:
    idx = cols.index("Variação")
    for c in ["Nome da variante 1", "Valor da variante 1", "É Variação"]:
        if c in cols:
            cols.insert(idx + 1, cols.pop(cols.index(c)))
            idx += 1
    df_final = df_final[cols]

df_final.to_excel('variantes.xlsx', index=False)

