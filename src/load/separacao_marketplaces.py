from typing import Optional

import pandas as pd

# ======================================================
# ARQUIVO DE ENTRADA
# ======================================================

ARQUIVO_BLING = "/home/lucas-silva/auto_shopee/planilhas/input/produtos_bling_ajustado.csv"

# ======================================================
# SAÍDAS
# ======================================================

ARQUIVO_RESULTADO = (
    "resultado_marketplaces.xlsx"
)

ARQUIVO_CUSTOMIZADOS = (
    "bling_campos_customizados.csv"
)


# ======================================================
# LIMITES MARKETPLACES
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
        "Profundidade",
        "Profundidade do produto",
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


def converter_numero(
    valor
) -> Optional[float]:

    if (
        pd.isna(valor)
        or valor == ""
    ):

        return None

    valor = (
        str(valor)
        .replace(",", ".")
        .strip()
    )

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
):

    if None in [
        peso,
        largura,
        altura,
        comprimento,
    ]:

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

        and

        maior_lado <= limite["lado_max"]

        and

        soma_lados <= limite["soma_max"]
    )


# ======================================================
# CLASSIFICAÇÃO
# ======================================================

def classificar_produto(row):

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

            "canal_ml":
                "REVISAR",

            "canal_shopee":
                "REVISAR",

            "tipo_envio_ml_sugerido":
                "REVISAR_DADOS",

            "classificacao_marketplace":
                "REVISAR_DADOS",

            "peso_validado":
                peso,

            "largura_validada":
                largura,

            "altura_validada":
                altura,

            "comprimento_validado":
                comprimento,

            "maior_lado":
                "",

            "soma_lados":
                "",
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
    # ML
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

    ml_ok = any([
        ml_correios_ok,
        ml_agencia_ok,
        ml_full_ok,
    ])

    # ==================================================
    # TIPO ENVIO ML
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

        classificacao = (
            "VALIDO_AMBOS"
        )

    elif shopee_ok and not ml_ok:

        classificacao = (
            "SOMENTE_SHOPEE"
        )

    elif ml_ok and not shopee_ok:

        classificacao = (
            "SOMENTE_ML"
        )

    else:

        classificacao = (
            "FORA_LIMITE"
        )

    # ==================================================
    # RETORNO
    # ==================================================

    return {

        "canal_ml":
            "SIM"
            if ml_ok
            else "NAO",

        "canal_shopee":
            "SIM"
            if shopee_ok
            else "NAO",

        "tipo_envio_ml_sugerido":
            tipo_envio_ml,

        "classificacao_marketplace":
            classificacao,

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
    }


# ======================================================
# PROCESSAMENTO
# ======================================================

def processar():

    print(
        "Lendo planilha..."
    )

    df = pd.read_csv(
        ARQUIVO_BLING,
        sep=";",
        encoding="utf-8-sig",
        low_memory=False,
    )

    print(
        f"Produtos encontrados: {len(df)}"
    )

    # ==================================================
    # CLASSIFICAÇÃO
    # ==================================================

    resultados = df.apply(
        classificar_produto,
        axis=1,
    )

    resultados_df = pd.DataFrame(
        resultados.tolist()
    )

    # ==================================================
    # RESULTADO COMPLETO
    # ==================================================

    df_resultado = pd.concat(
        [df, resultados_df],
        axis=1,
    )

    # ==================================================
    # RESULTADO MARKETPLACES
    # ==================================================

    print(
        "Gerando resultado marketplaces..."
    )

    with pd.ExcelWriter(
        ARQUIVO_RESULTADO,
        engine="openpyxl",
    ) as writer:

        df_resultado.to_excel(
            writer,
            sheet_name="todos_classificados",
            index=False,
        )

        df_resultado[
            df_resultado[
                "classificacao_marketplace"
            ]
            == "VALIDO_AMBOS"
        ].to_excel(
            writer,
            sheet_name="validos_ambos",
            index=False,
        )

        df_resultado[
            df_resultado[
                "classificacao_marketplace"
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

        df_resultado[
            df_resultado[
                "classificacao_marketplace"
            ]
            == "FORA_LIMITE"
        ].to_excel(
            writer,
            sheet_name="fora_limite",
            index=False,
        )

        df_resultado[
            df_resultado[
                "classificacao_marketplace"
            ]
            == "REVISAR_DADOS"
        ].to_excel(
            writer,
            sheet_name="revisar_dados",
            index=False,
        )

    # ==================================================
    # CAMPOS CUSTOMIZADOS
    # ==================================================

    print(
        "Gerando CSV campos customizados..."
    )

    df_customizados = pd.DataFrame()

    # ==================================================
    # IDENTIFICADOR
    # ==================================================

    if "Código" in df_resultado.columns:

        df_customizados[
            "Código"
        ] = df_resultado[
            "Código"
        ]

    elif "SKU" in df_resultado.columns:

        df_customizados[
            "SKU"
        ] = df_resultado[
            "SKU"
        ]

    # ==================================================
    # CAMPOS CUSTOMIZADOS
    # ==================================================

    df_customizados[
        "classificacao_marketplace"
    ] = df_resultado[
        "classificacao_marketplace"
    ]

    df_customizados[
        "canal_ml"
    ] = df_resultado[
        "canal_ml"
    ]

    df_customizados[
        "canal_shopee"
    ] = df_resultado[
        "canal_shopee"
    ]

    df_customizados[
        "tipo_envio_ml_sugerido"
    ] = df_resultado[
        "tipo_envio_ml_sugerido"
    ]
    df_customizados[
        "produtoPersonalizado"
    ] = "Não"

    df_customizados[
        "necessitaMontagem"
    ] = "Não"

    # ==================================================
    # REMOVE NAN
    # ==================================================

    df_customizados = (
        df_customizados.fillna("")
    )

    # ==================================================
    # SALVA CSV
    # ==================================================

    df_customizados.to_csv(
        ARQUIVO_CUSTOMIZADOS,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    # ==================================================
    # FINAL
    # ==================================================

    print(
        f"✅ {ARQUIVO_RESULTADO}"
    )

    print(
        f"✅ {ARQUIVO_CUSTOMIZADOS}"
    )


# ======================================================
# EXECUÇÃO
# ======================================================

processar()
