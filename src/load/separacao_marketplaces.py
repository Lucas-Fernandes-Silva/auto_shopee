from typing import Optional

import pandas as pd

# ======================================================
# ARQUIVOS
# ======================================================

ARQUIVO_ENTRADA = "produtos_com_embalagem.xlsx"

ARQUIVO_SAIDA = "resultado_marketplaces.xlsx"


# ======================================================
# LIMITES DOS MARKETPLACES
# ======================================================

LIMITES = {
    "shopee_padrao": {
        "peso_max": 30,
        "lado_max": 120,
        "soma_max": 200,
    },
    "ml_correios": {
        "peso_max": 30,
        "lado_max": 100,
        "soma_max": 200,
    },
    "ml_agencia_coleta": {
        "peso_max": 50,
        "lado_max": 200,
        "soma_max": 300,
    },
    "ml_full": {
        "peso_max": 25,
        "lado_max": 120,
        "soma_max": 260,
    },
}


# ======================================================
# POSSÍVEIS NOMES DE COLUNAS
# ======================================================

COLUNAS_POSSIVEIS = {
    "sku": [
        "Sku",
        "SKU",
        "Código",
        "codigo",
        "Código Produto",
    ],
    "descricao": [
        "Descrição",
        "descricao",
        "Produto",
        "Nome",
        "nome_original",
    ],
    "peso": [
        "Peso",
        "peso",
        "Peso bruto (Kg)",
        "Peso líquido (Kg)",
    ],
    "largura": [
        "Largura",
        "largura",
        "Largura do Produto",
    ],
    "altura": [
        "Altura",
        "altura",
        "Altura do Produto",
    ],
    "comprimento": [
        "Comprimento",
        "comprimento",
        "Profundidade do produto",
        "Profundidade",
    ],
}


# ======================================================
# AUXILIARES
# ======================================================

def pegar_valor(row, nomes):

    for nome in nomes:

        if nome in row and pd.notna(row[nome]):

            return row[nome]

    return ""


def converter_numero(valor) -> Optional[float]:

    if pd.isna(valor) or valor == "":

        return None

    valor = str(valor).replace(",", ".").strip()

    try:

        return float(valor)

    except ValueError:

        return None


# ======================================================
# VALIDAÇÃO
# ======================================================

def validar_limite(
    peso: Optional[float],
    largura: Optional[float],
    altura: Optional[float],
    comprimento: Optional[float],
    limite,
) -> bool:

    if None in [peso, largura, altura, comprimento]:

        return False

    assert peso is not None
    assert largura is not None
    assert altura is not None
    assert comprimento is not None

    peso = float(peso)
    largura = float(largura)
    altura = float(altura)
    comprimento = float(comprimento)

    soma_lados = (
        largura
        + altura
        + comprimento
    )

    maior_lado = max(
        largura,
        altura,
        comprimento,
    )

    return (
        peso <= limite["peso_max"]
        and maior_lado <= limite["lado_max"]
        and soma_lados <= limite["soma_max"]
    )


# ======================================================
# CLASSIFICAÇÃO
# ======================================================

def classificar_produto(row):

    sku = pegar_valor(
        row,
        COLUNAS_POSSIVEIS["sku"],
    )

    descricao = pegar_valor(
        row,
        COLUNAS_POSSIVEIS["descricao"],
    )

    peso = converter_numero(
        pegar_valor(
            row,
            COLUNAS_POSSIVEIS["peso"],
        )
    )

    largura = converter_numero(
        pegar_valor(
            row,
            COLUNAS_POSSIVEIS["largura"],
        )
    )

    altura = converter_numero(
        pegar_valor(
            row,
            COLUNAS_POSSIVEIS["altura"],
        )
    )

    comprimento = converter_numero(
        pegar_valor(
            row,
            COLUNAS_POSSIVEIS["comprimento"],
        )
    )

    # ==================================================
    # DADOS INVÁLIDOS
    # ==================================================

    if None in [
        peso,
        largura,
        altura,
        comprimento,
    ]:

        return {
            "sku_validado": sku,
            "descricao_validada": descricao,
            "canal_shopee": "REVISAR",
            "canal_ml": "REVISAR",
            "tipo_envio_ml_sugerido": "REVISAR_DADOS",
            "tipos_ml_possiveis": "REVISAR_DADOS",
            "classificacao_final": "REVISAR_DADOS",
            "peso_validado": peso,
            "largura_validada": largura,
            "altura_validada": altura,
            "comprimento_validado": comprimento,
            "maior_lado": "",
            "soma_lados": "",
            "motivo": "Peso ou dimensões inválidas",
        }

    assert peso is not None
    assert largura is not None
    assert altura is not None
    assert comprimento is not None

    peso = float(peso)
    largura = float(largura)
    altura = float(altura)
    comprimento = float(comprimento)

    soma_lados = (
        largura
        + altura
        + comprimento
    )

    maior_lado = max(
        largura,
        altura,
        comprimento,
    )

    # ==================================================
    # SHOPEE
    # ==================================================

    shopee_ok = validar_limite(
        peso,
        largura,
        altura,
        comprimento,
        LIMITES["shopee_padrao"],
    )

    # ==================================================
    # MERCADO LIVRE
    # ==================================================

    ml_correios_ok = validar_limite(
        peso,
        largura,
        altura,
        comprimento,
        LIMITES["ml_correios"],
    )

    ml_agencia_ok = validar_limite(
        peso,
        largura,
        altura,
        comprimento,
        LIMITES["ml_agencia_coleta"],
    )

    ml_full_ok = validar_limite(
        peso,
        largura,
        altura,
        comprimento,
        LIMITES["ml_full"],
    )

    tipos_ml_possiveis = []

    if ml_correios_ok:

        tipos_ml_possiveis.append(
            "ML_CORREIOS"
        )

    if ml_agencia_ok:

        tipos_ml_possiveis.append(
            "ML_AGENCIA_COLETA"
        )

    if ml_full_ok:

        tipos_ml_possiveis.append(
            "ML_FULL"
        )

    ml_ok = (
        len(
            tipos_ml_possiveis
        ) > 0
    )

    # ==================================================
    # PRIORIDADE ML
    # ==================================================

    if ml_correios_ok:

        tipo_envio_ml = (
            "ML_CORREIOS"
        )

    elif ml_agencia_ok:

        tipo_envio_ml = (
            "ML_AGENCIA_COLETA"
        )

    elif ml_full_ok:

        tipo_envio_ml = (
            "ML_FULL"
        )

    else:

        tipo_envio_ml = (
            "FORA_ML"
        )

    # ==================================================
    # CLASSIFICAÇÃO FINAL
    # ==================================================

    if shopee_ok and ml_ok:

        classificacao_final = (
            "VALIDO_AMBOS"
        )

    elif shopee_ok and not ml_ok:

        classificacao_final = (
            "SOMENTE_SHOPEE"
        )

    elif ml_ok and not shopee_ok:

        classificacao_final = (
            "SOMENTE_ML"
        )

    else:

        classificacao_final = (
            "FORA_LIMITE"
        )

    # ==================================================
    # RETORNO
    # ==================================================

    return {

        "sku_validado":
            sku,

        "descricao_validada":
            descricao,

        "canal_shopee":
            "SIM"
            if shopee_ok
            else "NAO",

        "canal_ml":
            "SIM"
            if ml_ok
            else "NAO",

        "tipo_envio_ml_sugerido":
            tipo_envio_ml,

        "tipos_ml_possiveis":
            ", ".join(
                tipos_ml_possiveis
            )
            if tipos_ml_possiveis
            else "FORA_ML",

        "classificacao_final":
            classificacao_final,

        "peso_validado":
            peso,

        "largura_validada":
            largura,

        "altura_validada":
            altura,

        "comprimento_validado":
            comprimento,

        "maior_lado":
            maior_lado,

        "soma_lados":
            soma_lados,

        "motivo":
            f"Peso: {peso} kg | "
            f"Medidas: "
            f"{largura} x "
            f"{altura} x "
            f"{comprimento} cm | "
            f"Soma lados: "
            f"{soma_lados} cm | "
            f"Maior lado: "
            f"{maior_lado} cm",
    }


# ======================================================
# PROCESSAMENTO
# ======================================================

def processar():

    print("Lendo planilha...")

    df = pd.read_excel(
        ARQUIVO_ENTRADA
    )

    print(
        f"Produtos encontrados: {len(df)}"
    )

    resultados = df.apply(
        classificar_produto,
        axis=1,
    )

    resultados_df = pd.DataFrame(
        resultados.tolist()
    )

    df_final = pd.concat(
        [df, resultados_df],
        axis=1,
    )

    print("Gerando planilha...")

    with pd.ExcelWriter(
        ARQUIVO_SAIDA,
        engine="openpyxl",
    ) as writer:

        df_final.to_excel(
            writer,
            sheet_name="todos_classificados",
            index=False,
        )

        df_final[
            df_final[
                "classificacao_final"
            ]
            == "VALIDO_AMBOS"
        ].to_excel(
            writer,
            sheet_name="validos_ambos",
            index=False,
        )

        df_final[
            df_final[
                "classificacao_final"
            ].isin(
                [
                    "SOMENTE_ML",
                    "SOMENTE_SHOPEE",
                ]
            )
        ].to_excel(
            writer,
            sheet_name="somente_uma",
            index=False,
        )

        df_final[
            df_final[
                "classificacao_final"
            ]
            == "FORA_LIMITE"
        ].to_excel(
            writer,
            sheet_name="fora_limite",
            index=False,
        )

        df_final[
            df_final[
                "classificacao_final"
            ]
            == "REVISAR_DADOS"
        ].to_excel(
            writer,
            sheet_name="revisar_dados",
            index=False,
        )

        resumo = (
            df_final[
                "classificacao_final"
            ]
            .value_counts()
            .reset_index()
        )

        resumo.columns = [
            "classificacao",
            "quantidade",
        ]

        resumo.to_excel(
            writer,
            sheet_name="resumo",
            index=False,
        )

    print(
        f"✅ Arquivo gerado: {ARQUIVO_SAIDA}"
    )


# ======================================================
# EXECUÇÃO
# ======================================================

processar()
