import pandas as pd

VARIACAO_POR_DOMINIO = {
    "ELETRICA": [
        "Amperagem",
        "Polos",
        "Diametro",
        "Comprimento",
        "Formato_Caixa",
        "Capacidade_Centrinho",
        "Cor",
    ],
}


def criar_chave_variacao(row, campos):
    valores = []
    for campo in campos:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None:
            valores.append("NA")
        else:
            valores.append(str(valor).strip())

    return "|".join(valores)


df_final = pd.read_excel("planilhas/outputs/Produtos_Classificados.xlsx", dtype=str)


df = df_final.copy()

df_debug = pd.read_excel(
    "planilhas/outputs/Produtos_Classificados.xlsx",
    dtype=str
)

print(
    df_debug[
        ["Descricao_Limpa", "Diametro", "Comprimento", "Formato_Caixa"]
    ]
    .head(30)
)


# dominio = "ELETRICA"
# campos_variacao = VARIACAO_POR_DOMINIO[dominio]

# df_eletrica = df[df["Dominio"] == dominio].copy()

# df_eletrica["Chave_Variacao"] = df_eletrica.apply(
#     lambda row: criar_chave_variacao(row, campos_variacao), axis=1
# )


# agrupado = (
#     df_eletrica.groupby("Chave_Variacao")
#     .agg(
#         Qtd_Produtos=("Descricao_Limpa", "count"),
#         Exemplos=("Descricao_Limpa", lambda x: list(x[:3])),
#     )
#     .reset_index()
# )

# agrupado.sort_values("Qtd_Produtos", ascending=False).head(10)


# df_eletrica[["Descricao_Limpa"] + campos_variacao + ["Chave_Variacao"]].to_excel(
#     "Teste_Variacoes_Eletrica.xlsx", index=False
# )
