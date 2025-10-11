import pandas as pd

# === 1. Ler o arquivo com os grupos já criados ===
arquivo = "todos_produtos.xlsx"
df = pd.read_excel(arquivo)

# === 2. Validar colunas necessárias ===
colunas_necessarias = ["Grupo", "Variação"]
for col in colunas_necessarias:
    if col not in df.columns:
        raise ValueError(f"A planilha deve conter a coluna '{col}' (execute o script de agrupamento antes)")

# === 3. Detectar a coluna de SKU automaticamente ===
col_sku = None
for nome in df.columns:
    if "SKU" in nome.upper():
        col_sku = nome
        break

if not col_sku:
    raise ValueError("A planilha precisa ter uma coluna com o SKU (nome contendo 'SKU')")

# === 4. Criar coluna 'SKU Principal' ===
# Primeiro: obter o primeiro SKU de cada grupo
sku_principal = df.groupby("Grupo")[col_sku].transform("first")

# Verifica grupos únicos (sem variação)
tamanho_grupo = df.groupby("Grupo")[col_sku].transform("count")

# Se o grupo tiver só 1 item, o SKU principal é o próprio SKU
df["SKU Principal"] = sku_principal
df.loc[tamanho_grupo == 1, "SKU Principal"] = df.loc[tamanho_grupo == 1, col_sku]

# === 5. Renomear SKU atual para 'SKU Variação' (opcional, para clareza)
df = df.rename(columns={col_sku: "SKU Variação"})

# === 6. Reordenar colunas: colocar SKU Principal logo após Variação ===
cols = df.columns.tolist()
if "Variação" in cols and "SKU Principal" in cols:
    idx_var = cols.index("Variação")
    cols.insert(idx_var + 1, cols.pop(cols.index("SKU Principal")))
    df = df[cols]

# === 7. Salvar no mesmo arquivo ===
df.to_excel(arquivo, index=False)

print(f"✅ Coluna 'SKU Principal' adicionada com sucesso ao arquivo '{arquivo}'!")
print("   - Se o produto tiver grupo único, o SKU principal será igual ao SKU da própria linha.")
print("   - Caso tenha variações, todas compartilham o mesmo SKU principal do primeiro item.")
