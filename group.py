import pandas as pd

grupo = pd.read_excel('produtos.xlsx')

df_filtrado = grupo[
    (grupo["peso"].astype(str).str.upper() != "NÃO DISPONIVEL") &
    (grupo["url imagem"].astype(str).str.upper() != "NÃO DISPONIVEL")
]

print(df_filtrado)