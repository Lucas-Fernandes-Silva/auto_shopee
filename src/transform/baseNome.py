import re

import pandas as pd

COLUNAS_VARIACAO_POR_DOMINIO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Diametro",
        "Comprimento_Venda",
        "Formato_Caixa",
        "Capacidade_Centrinho",
    ]
}

COLUNAS_REMOVE_TEXTO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Diametro",
        "Comprimento_Venda",
        "Formato_Caixa",
        "Capacidade_Centrinho",
    ]
}

FORMATACAO_VARIACOES = {
    "Amperagem": lambda v: f"{v}A",
    "Polos": lambda v: str(v),
    "Diametro": lambda v: str(v),
    "Comprimento": lambda v: str(v),
    "Formato_Caixa": lambda v: str(v),
    "Capacidade_Centrinho": lambda v: str(v),
}


def gerar_nome_variacao(row, campos_variacao, formatacao_map):
    partes = []

    for campo in campos_variacao:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None:
            continue

        formatter = formatacao_map.get(campo, lambda v: str(v))
        partes.append(formatter(valor))

    return " ".join(partes)


def gerar_nome_base(row, campos_variacao):
    if not isinstance(row["Descricao_Limpa"], str):
        return None

    texto = row["Descricao_Limpa"].upper()

    for campo in campos_variacao:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None:
            continue

        valor_str = str(valor).upper()

        texto = re.sub(rf"\b{re.escape(valor_str)}\b", "", texto)

        texto = re.sub(rf"\b{re.escape(valor_str)}\s*(A|MM|M|MT)?\b", "", texto)

    texto = re.sub(r"\s{2,}", " ", texto).strip()
    return texto


df_eletrica = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados_Por_Dominio.xlsx",
    sheet_name="ELETRICA",
)

print(df_eletrica["Comprimento_Venda"])

# campos_remove = COLUNAS_REMOVE_TEXTO["ELETRICA"]

# df_eletrica["Nome_Produto_Base"] = df_eletrica.apply(
#     lambda row: gerar_nome_base(row, campos_remove), axis=1
# )

# df_eletrica["Nome_Variacao"] = df_eletrica.apply(
#     lambda row: gerar_nome_variacao(row, campos_remove, FORMATACAO_VARIACOES), axis=1
# )


# df_eletrica.to_excel("NomeEletrica.xlsx", index=False)
