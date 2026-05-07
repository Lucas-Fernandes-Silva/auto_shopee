import pandas as pd

# Caminho da planilha
arquivo = "/home/lucas-silva/auto_shopee/produtos_com_descricoes.xlsx"

# Ler planilha
df = pd.read_excel(arquivo)

# Garantir texto nas colunas
df["grupo_id"] = df["grupo_id"].astype(str)
df["tipo_grupo"] = df["tipo_grupo"].astype(str).str.lower()

# =========================================
# Pegar o código do produto pai por grupo
# =========================================
pais = df[df["tipo_grupo"] == "pai"].groupby("grupo_id")["Codigo Produto"].first().to_dict()

# =========================================
# Adicionar código do pai nos filhos
# =========================================
df["codigo_pai"] = df["grupo_id"].map(pais)

# Se quiser deixar vazio para pai/unico:
df.loc[df["tipo_grupo"] != "filho", "codigo_pai"] = ""

# =========================================
# Salvar resultado
# =========================================
saida = "/home/lucas-silva/auto_shopee/produtos_com_descricoes.xlsx"
df.to_excel(saida, index=False)

print(f"Arquivo salvo: {saida}")
