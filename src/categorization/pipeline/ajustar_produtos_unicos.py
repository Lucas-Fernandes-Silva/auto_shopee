import pandas as pd


def ajustar_produtos_unicos(
    df: pd.DataFrame,
    col_grupo="grupo_id",
    col_codigo_pai="codigo_pai",
    col_tipo="tipo_relacionamento",
    col_produto_unico="produto_unico",
):
    df = df.copy()

    if col_grupo not in df.columns:
        df[col_produto_unico] = False
        return df

    grupo_tamanho = df.groupby(col_grupo)[col_grupo].transform("size")
    mask_unico = grupo_tamanho == 1

    # apenas marca produto único
    df[col_produto_unico] = mask_unico

    # produto único continua sendo pai
    if col_tipo in df.columns:
        df.loc[mask_unico, col_tipo] = "PAI"

    # produto único não tem código pai
    if col_codigo_pai in df.columns:
        df.loc[mask_unico, col_codigo_pai] = None

    return df
