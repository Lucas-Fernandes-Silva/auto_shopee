import math
import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_upseller.xlsx"
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/final_urls_cloudinary.xlsx"
)

upseller_colunas = upseller.columns.tolist()


def criar_linha(item, colunas_upseller):
    linha = {col: "" for col in colunas_upseller}

    mapa = {
        "Nome do Produto*": item.get("Descrição", ""),
        "SKU Principal": item.get("Sku", ""),
        "Descrição*": item.get("Descrição", ""),
        "Categoria ID": "101199",
        "Preço*": item.get("Preço Final", ""),
        "Quantidade*": "0",
        "GTIN": item.get("Código de Barras", ""),
        "Imagem de Capa": item.get("Url_Imagem1.0", ""),
        "Item da Imagem1": item.get("Url_Imagem2.0", ""),
        "Item da Imagem2": item.get("Url_Imagem3.0", ""),
        "Item da Imagem4": item.get("Url Imagem", ""),
        "Item da Imagem3": "https://res.cloudinary.com/dbpq32fiq/image/upload/v1764623485/46ba78f5-9d01-49fb-a96f-f00aead7f851_wgbwkj.png",
        "Peso (kg)*": item.get("Peso", ""),
        "Comprimento (cm)": item.get("Comprimento", ""),
        "Largura (cm)": item.get("Largura", ""),
        "Altura (cm)": item.get("Altura", ""),
    }

    linha.update(mapa)
    return linha


linhas_upseller = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
upseller_df = pd.DataFrame(linhas_upseller, columns=upseller_colunas)


upseller_df["Peso (kg)*"] = (
    pd.to_numeric(upseller_df["Peso (kg)*"], errors="coerce")
    .fillna(1)
    .apply(lambda x: math.ceil(x))  # arredonda pra cima
    .astype("Int64")
)


# Dimensões inteiras (Comprimento, Largura, Altura)
for col in ["Comprimento (cm)", "Largura (cm)", "Altura (cm)"]:
    upseller_df[col] = (
        pd.to_numeric(upseller_df[col], errors="coerce").fillna(0).round(0).astype("Int64")
    )

# Preço permanece com decimais (caso você já tenha ajustado antes)
upseller_df["Preço*"] = pd.to_numeric(upseller_df["Preço*"], errors="coerce").round(2)

# ---------------------------------------
# Mantém o restante igual
# ---------------------------------------

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, upseller_df], ignore_index=True)
else:
    df_final = upseller_df

df_final.to_excel("upseller.xlsx", index=False)
