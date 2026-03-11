import pandas as pd


def ajustar_produtos_unicos(
    df: pd.DataFrame,
    col_descricao="Descricao_Limpa",
    col_base="Nome_Produto_Base",
    col_variacao="Nome_Variacao",
    col_grupo="grupo_id",
    col_codigo_pai="codigo_pai",
    col_tipo="tipo_relacionamento",
):
    df = df.copy()

    if col_grupo not in df.columns:
        return df

    grupo_tamanho = df.groupby(col_grupo)[col_grupo].transform("size")
    mask_unico = grupo_tamanho == 1

    # produto único = base igual descrição
    df.loc[mask_unico, col_base] = df.loc[mask_unico, col_descricao]

    # produto único = sem variação
    df.loc[mask_unico, col_variacao] = ""

    # produto único = pai
    if col_tipo in df.columns:
        df.loc[mask_unico, col_tipo] = "PAI"

    # produto único = sem código pai
    if col_codigo_pai in df.columns:
        df.loc[mask_unico, col_codigo_pai] = None

    return df
