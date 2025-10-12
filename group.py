import pandas as pd
import re

# === 1. Ler o arquivo atualizado ===
arquivo = "todos_produtos.xlsx"
df = pd.read_excel(arquivo)

# === 2. Garantir colunas esperadas ===
for col in ["Variação", "Grupo", "SKU Principal", "SKU Variação"]:
    if col not in df.columns:
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
tipos, valores = zip(*df["Variação"].map(detectar_tipo_variacao))
df["Nome da variante 1"] = tipos
df["Valor da variante 1"] = valores

# === 5. Coluna “É Variação” ===
df["É Variação"] = df.groupby("Grupo")["Grupo"].transform("count").apply(lambda x: "Sim" if x > 1 else "Não")

# === 6. Reordenar colunas para melhor visualização ===
cols = df.columns.tolist()
if "Variação" in cols and "Nome da variante 1" in cols:
    idx = cols.index("Variação")
    for c in ["Nome da variante 1", "Valor da variante 1", "É Variação"]:
        if c in cols:
            cols.insert(idx + 1, cols.pop(cols.index(c)))
            idx += 1
    df = df[cols]

# === 7. Salvar novamente no mesmo arquivo ===
df.to_excel(arquivo, index=False)

print(f"✅ Colunas de variação adicionadas com sucesso no arquivo '{arquivo}'!")
