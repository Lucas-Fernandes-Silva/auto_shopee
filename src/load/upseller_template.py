import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_upseller.xlsx"
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel("/home/lucas-silva/auto_shopee/taxas_corrigidas.xlsx")
upseller_colunas = upseller.columns.tolist()

teste = produtos[:5]
produtos = teste.copy()

def criar_linha(item, colunas_produtos):
    linha = {col: "" for col in colunas_produtos}

    mapa = {
        "Nome do Produto*": item.get("Base", ""),
        "SKU Principal": item.get("SKU_Pai", ""),
        "Descrição*": item.get("Descrição", ""),
        "Categoria ID": "101197",
        "Nome Variante1": "Variação",
        "Opção por Variante1": item.get("Variante", ""),
        "Imagem por Variante": next(
        (item.get(k) for k in ["Url_Imagem1", "Url_Imagem2", "Url_Imagem3", "Url Imagem"] if item.get(k))),
        "SKU": item.get("Sku", ""),
        "Preço*": item.get("Preço Final", ""),
        "Quantidade*": "0",
        "GTIN": item.get("Código de Barras", ""),
        "Imagem de Capa": item.get("Url_Imagem1", ""),
        "Item da Imagem1": item.get("Url_Imagem2", ""),
        "Item da Imagem2": item.get("Url_Imagem3", ""),
        "Item da Imagem3": item.get("Url Imagem", ""),
        "Peso (kg)*": item.get("Peso", "1"),
        "Comprimento (cm)":item.get("Comprimento",""),
        "Largura (cm)": item.get("Largura",""),
        "Altura (cm)": item.get("Altura","")
    }

    linha.update(mapa)
    return linha


linhas_upseller = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
upseller_df = pd.DataFrame(linhas_upseller, columns=upseller_colunas)

upseller_df["Peso (kg)*"] = upseller_df["Peso (kg)*"].fillna(1)

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, upseller_df], ignore_index=True)
else:
    df_final = upseller_df


# Salva tudo de novo (mantém todas as linhas)
df_final.to_excel("teste.xlsx", index=False)
