import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_upseller.xlsx"
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/final_urls_cloudinary.xlsx"
)
upseller_colunas = upseller.columns.tolist()


def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    mapa = {
        "Nome do Produto*": item.get("Base", ""),
        "SKU Principal": item.get("SKU_Pai", ""),
        "Descrição*": item.get("Descrição", ""),
        "Categoria ID": "101199",
        "Nome Variante1": "Variação",
        "Opção por Variante1": item.get("Variante", ""),
        "Imagem por Variante": item.get("Url_Imagem1.0", "")
        or item.get("Url_Imagem2.0")
        or item.get("Url_Imagem3.0")
        or item.get("Url Imagem"),
        "SKU": item.get("Sku", ""),
        "Preço*": item.get("Preço Final", ""),
        "Quantidade*": "0",
        "GTIN": item.get("Código de Barras", ""),
        "Imagem de Capa": item.get("Url_Imagem1.0", ""),
        "Item da Imagem1": item.get("Url_Imagem2.0", ""),
        "Item da Imagem2": item.get("Url_Imagem3.0", ""),
        "Item da Imagem4": item.get("Url Imagem", ""),
        "Item da Imagem3": "https://res.cloudinary.com/dbpq32fiq/image/upload/v1764623485/46ba78f5-9d01-49fb-a96f-f00aead7f851_wgbwkj.png",
        "Peso (kg)*": item.get("Peso", "1"),
        "Comprimento (cm)": item.get("Comprimento", ""),
        "Largura (cm)": item.get("Largura", ""),
        "Altura (cm)": item.get("Altura", ""),
    }

    linha.update(mapa)
    return linha


linhas_bling = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=upseller_colunas)


# Peso inteiro
bling_df["Peso (kg)*"] = (
    pd.to_numeric(bling_df["Peso (kg)*"], errors="coerce").fillna(1).round(0).astype("Int64")
)

# Dimensões inteiras (Comprimento, Largura, Altura)
for col in ["Comprimento (cm)", "Largura (cm)", "Altura (cm)"]:
    bling_df[col] = pd.to_numeric(bling_df[col], errors="coerce").fillna(0).round(0).astype("Int64")

# Preço permanece com decimais (caso você já tenha ajustado antes)
bling_df["Preço*"] = pd.to_numeric(bling_df["Preço*"], errors="coerce").round(2)

# ---------------------------------------
# Mantém o restante igual
# ---------------------------------------

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, bling_df], ignore_index=True)
else:
    df_final = bling_df

df_final.to_excel("upseller.xlsx", index=False)
