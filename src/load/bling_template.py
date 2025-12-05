import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_bling.xlsx"
bling = pd.read_excel(arquivo)
produtos = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/final_urls_cloudinary.xlsx"
)
bling_colunas = bling.columns.tolist()


def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    # ===== MULTI-IMAGENS =====
    urls = [
        str(item.get("Url_Imagem1.0", "") or ""),
        str(item.get("Url_Imagem2.0", "") or ""),
        str(item.get("Url_Imagem3.0", "") or ""),
        str(item.get("Url Imagem", "") or ""),
        str(
            "https://res.cloudinary.com/dbpq32fiq/image/upload/v1764623485/46ba78f5-9d01-49fb-a96f-f00aead7f851_wgbwkj.png"
        ),
    ]

    url_imagens = "|".join(u for u in urls if u and u.lower() != "nan")

    # ===== LÓGICA DO CÓDIGO PAI / INTEGRAÇÃO =====
    if item.get("Tipo") == "PAI":
        codigo_pai = ""
        codigo_integracao = ""
    else:
        codigo_pai = item.get("SKU_Pai", "")
        codigo_integracao = item.get("ID_Variacao", "")

    # ===== MAPA DE COLUNAS =====
    mapa = {
        "Código": item.get("Sku", ""),
        "Descrição": item.get("Descrição", ""),
        "NCM": item.get("NCM", ""),
        "Origem": "0",
        "Preço": item.get("Preço Final", ""),
        "Situação": "Ativo",
        "Estoque": "0",
        "Preço de custo": item.get("Valor_unitário", ""),
        "Fornecedor": item.get("Fornecedor", ""),
        "Estoque maximo": "1000",
        "Estoque minimo": "5",
        "Peso líquido (Kg)": item.get("Peso", ""),
        "Peso bruto (Kg)": item.get("Peso", ""),
        "Largura do Produto": item.get("Largura", ""),
        "Altura do Produto": item.get("Altura", ""),
        "Profundidade do produto": item.get("Comprimento", ""),
        "Descrição do Produto no Fornecedor": item.get("Descrição", ""),
        "Descrição Complementar": item.get("Descrição", ""),
        "Produto Variação": item.get("Sku", ""),
        "Tipo Produção": "Variação",
        "Código Pai": codigo_pai,
        "Código Integração": codigo_integracao,
        "Marca": item.get("Marca", ""),
        "Descrição Curta": item.get("Descrição", ""),
        "URL Imagens Externas": url_imagens,
        "Clonar dados do pai": "",
        "Condição do produto": "Novo",
        "Vídeo": "https://res.cloudinary.com/dbpq32fiq/video/upload/v1764713564/br-11110105-6kfkp-m9rgp2iu1rg979.16000081747233950_huycfh.mp4",
        "Departamento": item.get("Categoria", ""),
        "Preço de compra": item.get("Valor Unitário", ""),
        "Categoria do produto": "Materiais de Construção",
    }

    linha.update(mapa)
    return linha


# ===== MONTA AS LINHAS PARA A PLANILHA DO BLING =====
linhas_bling = [criar_linha(row, bling_colunas) for _, row in produtos.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=bling_colunas)


# ===== UNE COM O QUE JÁ EXISTE =====
if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, bling_df], ignore_index=True)
else:
    df_final = bling_df


# ===== SALVA =====
df_final.to_excel("bling.xlsx", index=False)
