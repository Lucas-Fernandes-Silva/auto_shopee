import pandas as pd

df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados_Por_Dominio.xlsx")

df["Produto_Base_ID"] = (
    df["grupo_id"].astype(str)
    + "|"
    + df["Marca"].str.upper().fillna("SEM_MARCA")
)

df["Nome_Produto_Base"] = (
    "Disjuntor DIN Curva C "
    + df["Marca"].str.upper()
)

df["Chave_Variacao"] = (
    df["Polos"].fillna("NA").astype(str)
    + "|"
    + df["Amperagem"].fillna("NA").astype(str)
)

df["Nome_Variacao"] = (
    df["Polos"].fillna("")
    + " "
    + df["Amperagem"].astype(str)
    + "A"
)

df[
    df["grupo_id"] == 436
][
    [
        "Descricao_Limpa",
        "Marca",
        "Nome_Produto_Base",
        "Nome_Variacao"
    ]
]


