import pandas as pd
import os

arquivo = 'colunas_upseller.xlsx'
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel('produtos.xlsx')
upseller_colunas = upseller.columns.tolist()


def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    mapa = {
    'Nome do Produto*': item.get("Base",""),
    'SKU Principal': item.get("SKU Principal",""),
    'Descrição*': item.get("Descrição",""),
    'Categoria ID': "101197",
    'Nome Variante1': item.get("Nome da variante 1", ""),
    'Opção por Variante1': item.get("Variação",""),
    'Imagem por Variante': item.get("Url Imagem",""),
    'SKU': item.get("SKU Variação",""),
    'Preço*': item.get("Valor_unitário",""),
    'Quantidade*': "0",
    'GTIN': item.get("Código de Barras",""),
    'Imagem de Capa': item.get("Url Imagem",""),
    'Item da Imagem1': item.get("Url Imagem",""),
    'Item da Imagem2': item.get("Url Imagem",""),
    'Item da Imagem3': item.get("Url Imagem",""),
    'Peso (kg)*': item.get("Peso","1"),
    'Comprimento (cm)': "10",
    'Largura (cm)': "10",
    'Altura (cm)': "10",
    }

    linha.update(mapa)
    return linha

linhas_bling = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=upseller_colunas)

bling_df['Peso (kg)*'] = bling_df['Peso (kg)*'].fillna(1)

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, bling_df], ignore_index=True)
else:
    df_final = bling_df



# Salva tudo de novo (mantém todas as linhas)
df_final.to_excel('upseller_template.xlsx', index=False)