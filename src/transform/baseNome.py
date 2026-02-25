import re

import pandas as pd

COLUNAS_VARIACAO_POR_DOMINIO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Cor",
        "Diametro",
        "Comprimento_Venda",
        "Formato_Caixa",
        "Capacidade_Centrinho",
        "Formato",
        "Potencia_W",
        "Temperatura_Cor",
        "Tipo_Lampada",
    ]
}

COLUNAS_REMOVE_TEXTO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Cor",
        "Diametro",
        "Comprimento_Venda",
        "Formato_Caixa",
        "Capacidade_Centrinho",
        "Formato",
        "Potencia_W",
        "Temperatura_Cor",
        "Tipo_Lampada",
    ]
}

FORMATACAO_VARIACOES = {
    "Amperagem": lambda v: str(f"{v}A"),
    "Polos": lambda v: str(v),
    "Cor": lambda v: str(v),
    "Formato": lambda v: str(v),
    "Potencia_W": lambda v: str(v),
    "Temperatura_Cor": lambda v: str(v),
    "Tipo_Lampada": lambda v: str(v),
    "Diametro": lambda v: str(v),
    "Comprimento": lambda v: str(v),
    "Formato_Caixa": lambda v: str(v),
    "Capacidade_Centrinho": lambda v: str(v),
}


def gerar_tokens_equivalentes(valor, campo):
    tokens = []

    v = str(valor).upper().replace(",", ".")

    # amperagem
    if campo == "Amperagem":
        tokens.extend(
            [
                v,
                f"{v}A",
                f"{v} A",
                f"{v}.0A",
                f"{v}.0 A",
            ]
        )

    # polos
    elif campo == "Polos":
        tokens.append(v)
        if v == "1P":
            tokens.append("UNIPOLAR")
        elif v == "2P":
            tokens.append("BIPOLAR")
        elif v == "3P":
            tokens.append("TRIPOLAR")

    # polegadas
    elif "/" in v:
        tokens.extend(
            [
                v,
                v.replace('"', ""),
                f'{v}"',
            ]
        )

    # genérico
    else:
        tokens.append(v)

    return list(set(tokens))


def gerar_nome_variacao(row, campos_variacao, formatacao_map):
    partes = []

    for campo in campos_variacao:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None:
            continue

        formatter = formatacao_map.get(campo, lambda v: str(v))
        partes.append(formatter(valor))

    return " ".join(partes)


def gerar_nome_base(row, colunas_remove):
    if not isinstance(row["Descricao_Limpa"], str):
        return None

    texto = row["Descricao_Limpa"].upper()

    for campo in colunas_remove:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None:
            continue

        tokens = gerar_tokens_equivalentes(valor, campo)

        for token in tokens:
            texto = re.sub(rf"\b{re.escape(token)}\b", "", texto)

    texto = re.sub(r"\s{2,}", " ", texto).strip()
    return texto if texto else None


df_eletrica = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados_Por_Dominio.xlsx",
    sheet_name="ELETRICA",
)

campos_remove = COLUNAS_REMOVE_TEXTO["ELETRICA"]

df_eletrica["Nome_Produto_Base"] = df_eletrica.apply(
    lambda row: gerar_nome_base(row, campos_remove), axis=1
)

df_eletrica["Nome_Variacao"] = df_eletrica.apply(
    lambda row: gerar_nome_variacao(row, campos_remove, FORMATACAO_VARIACOES), axis=1
)


df_eletrica.to_excel("NomeEletrica.xlsx", index=False)
