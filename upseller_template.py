import pandas as pd

upseller = pd.read_excel('upseller.xlsx')
produtos= pd.read_excel('todos_produtos.xlsx')
upseller_colunas = upseller.columns.tolist()

def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    mapa = {
    'Nome do Produto*': item.get("Base",""),
    'SKU Principal': item.get("SKU Principal",""),
    'Descrição*': item.get("Descrição",""),
    'Categoria ID': "101197",
    'Nome Variante1': item.get("Variação",""),
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
    'Peso (kg)*': item.get("Peso",""),
    'Comprimento (cm)': "10",
    'Largura (cm)': "10",
    'Altura (cm)': "10",
    }

    linha.update(mapa)
    return linha

linhas_bling = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=upseller_colunas)
bling_df.to_excel('produtos_upseller.xlsx', index=False)