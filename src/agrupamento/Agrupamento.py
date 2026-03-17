import pandas as pd


def _safe_str(v) -> str:
    if pd.isna(v):
        return ""
    s = str(v).strip().upper()
    return "" if s == "NAN" else s


def _marca_para_chave(row) -> str:
    marca = _safe_str(row.get("Marca"))
    return "" if marca == "GENERICO" else marca


def montar_chave_agrupamento_parafusos(row) -> str:
    campos = [
        _safe_str(row.get("Dominio")),
        _marca_para_chave(row),
        _safe_str(row.get("Tipo_Parafuso")),
        _safe_str(row.get("Tipo_Cabeca")),
        _safe_str(row.get("Tipo_Rebite")),
        _safe_str(row.get("Tipo_Porca")),
        _safe_str(row.get("Tipo_Chumbador")),
        _safe_str(row.get("Tipo_Bucha")),
        _safe_str(row.get("Tipo_Arruela")),
        _safe_str(row.get("Modelo_Rebite")),
    ]
    return " | ".join([c for c in campos if c])


def montar_chave_agrupamento_eletrica(row) -> str:
    campos = [
        _safe_str(row.get("Dominio")),
        _marca_para_chave(row),
        _safe_str(row.get("Nome_Produto_Base")),
    ]
    return " | ".join([c for c in campos if c])


def montar_chave_agrupamento_hidraulica(row) -> str:
    campos = [
        _safe_str(row.get("Dominio")),
        _marca_para_chave(row),
        _safe_str(row.get("Nome_Produto_Base")),
    ]
    return " | ".join([c for c in campos if c])


def montar_chave_agrupamento_tomadas(row) -> str:
    campos = [
        _safe_str(row.get("Dominio")),
        _marca_para_chave(row),
        _safe_str(row.get("Tipo_Tomada")),
        _safe_str(row.get("Polos")),
    ]
    return " | ".join([c for c in campos if c])


def montar_chave_agrupamento(row) -> str:
    dominio = _safe_str(row.get("Dominio"))

    if dominio == "PARAFUSOS":
        return montar_chave_agrupamento_parafusos(row)

    if dominio == "ELETRICA":
        return montar_chave_agrupamento_eletrica(row)

    if dominio == "HIDRAULICA":
        return montar_chave_agrupamento_hidraulica(row)

    if dominio == "TOMADAS":
        return montar_chave_agrupamento_tomadas(row)

    campos = [
        _safe_str(row.get("Dominio")),
        _marca_para_chave(row),
        _safe_str(row.get("Nome_Produto_Base")),
    ]
    return " | ".join([c for c in campos if c])


def aplicar_chave_agrupamento(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Chave_Agrupamento"] = df.apply(montar_chave_agrupamento, axis=1)
    return df
