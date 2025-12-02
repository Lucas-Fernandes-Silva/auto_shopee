import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_upseller.xlsx"
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel("/home/lucas-silva/auto_shopee/produtos_padrao.xlsx")
upseller_colunas = upseller.columns.tolist()


def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    mapa = {
        "Nome do Produto*": item.get("Descrição", ""),
        "SKU Principal": item.get("Sku", ""),
        "Descrição*": item.get("Descrição", ""),
        "Categoria ID": "101197",
        "Preço*": item.get("Preço Final", ""),
        "Quantidade*": "0",
        "GTIN": item.get("Código de Barras", ""),
        "Imagem de Capa": item.get("Url_Imagem1.0", ""),
        "Item da Imagem1": item.get("Url_Imagem2.0", ""),
        "Item da Imagem2": item.get("Url_Imagem3.0", ""),
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

bling_df["Peso (kg)*"] = bling_df["Peso (kg)*"].fillna(1)

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, bling_df], ignore_index=True)
else:
    df_final = bling_df


# Salva tudo de novo (mantém todas as linhas)
df_final.to_excel("upseller.xlsx", index=False)
