import re

import pandas as pd

CAMPOS_VARIACAO_POR_DOMINIO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Cor",
        "Diametro",
        "Comprimento_Venda",
        "Capacidade_Centrinho",
        "Formato",
        "Potencia_W",
        "Lumens",
        "Temperatura_Cor",
        "Tipo_Lampada",
        "Medida",
    ],
    "PARAFUSOS": [
        "Tipo_Parafuso",
        "Tipo_Cabeca",
        "Medida",
        "Diametro",
        "Comprimento_Venda",
        "Cor",
        "Tipo_Rebite",
        "Tipo_Porca",
        "Tipo_Chumbador",
        "Tipo_Bucha",
        "Tipo_Arruela",
        "Modelo_Rebite",
    ],
    "HIDRAULICA": [
        "Medida",
        "Diametro",
        "Comprimento_Venda",
        "Cor",
        "Volume",
        "Peso_Venda",
    ],
    "TOMADAS": [
        "Tipo_Tomada",
        "Amperagem",
        "Polos",
        "Diametro",
        "Comprimento_Venda",
        "Cor",
        "Medida",
    ],
}


def normalizar_numero_tokens(valor) -> set[str]:
    s = str(valor).strip()
    if not s:
        return set()

    s_up = s.upper()
    tokens = {s_up}

    if "," in s_up:
        tokens.add(s_up.replace(",", "."))
    if "." in s_up:
        tokens.add(s_up.replace(".", ","))

    if "/" in s_up:
        return tokens

    if s_up.isdigit():
        try:
            n = str(int(s_up))
            tokens.add(n)

            if len(n) == 1:
                tokens.add(n.zfill(2))
            if len(n) == 2:
                tokens.add(n.zfill(3))
        except Exception:
            pass

    return tokens


def gerar_tokens_equivalentes(valor, campo):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return []

    v_raw = str(valor).strip()
    if not v_raw:
        return []

    v = v_raw.upper()
    tokens = set()

    if campo in {"Comprimento_Venda", "Peso_Venda", "Volume"}:
        match = re.match(r"(\d+(?:[.,]\d+)?)(.*)", v)
        if match:
            numero = match.group(1)
            unidade = match.group(2).strip()

            for n in normalizar_numero_tokens(numero):
                tokens.add(f"{n}{unidade}")
                if unidade:
                    tokens.add(f"{n} {unidade}")

    elif campo == "Medida" or campo == "Potencia_W":
        base = v_raw.strip().upper().replace("×", "X")

        # remove aspas antigas, se existirem
        base = base.replace('"', "").replace("'", "")
        base = re.sub(r"\s*[X]\s*", "X", base)

        variantes_base = {base, base.replace(",", "."), base.replace(".", ",")}

        tokens = set()

        for v in variantes_base:
            partes = re.split(r"X", v)
            if len(partes) >= 2:
                tokens.add("X".join(partes))
                tokens.add(" X ".join(partes))
                tokens.add(" x ".join(partes))

                if len(partes) == 2:
                    a, b = partes
                    tokens.add(f"{a}X{b}")
                    tokens.add(f"{a}X {b}")
                    tokens.add(f"{a} X{b}")
                    tokens.add(f"{a} X {b}")
                    tokens.add(f"{a}x{b}")
                    tokens.add(f"{a}x {b}")
                    tokens.add(f"{a} x{b}")
                    tokens.add(f"{a} x {b}")
            else:
                tokens.add(v)

        return list(tokens)

    elif campo == "Diametro":
        if "/" in v:
            tokens.add(v.replace(" ", ""))
            tokens.add(v)
        else:
            match = re.match(r"(\d+(?:[.,]\d+)?)(.*)", v)
            if match:
                numero = match.group(1)
                unidade = match.group(2).strip()

                for n in normalizar_numero_tokens(numero):
                    tokens.add(f"{n}{unidade}")
                    if unidade:
                        tokens.add(f"{n} {unidade}")

    else:
        tokens.add(v)

    return list(tokens)


def remover_tokens(texto: str, tokens: list[str]) -> str:
    if not isinstance(texto, str):
        return texto

    resultado = texto

    for token in sorted(set(tokens), key=len, reverse=True):
        if not token:
            continue
        padrao = rf"\b{re.escape(token)}\b"
        resultado = re.sub(padrao, " ", resultado, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", resultado).strip()


def aplicar_nomes(df: pd.DataFrame, col_descricao="Descricao_Limpa", col_dominio="Dominio"):
    df = df.copy()

    nome_base = []
    nome_variacao = []

    for _, row in df.iterrows():
        descricao = str(row.get(col_descricao, "")).strip()
        dominio = str(row.get(col_dominio, "")).strip().upper()

        campos_variacao = CAMPOS_VARIACAO_POR_DOMINIO.get(dominio, [])

        partes_variacao = []
        tokens_remover = []

        for col in campos_variacao:
            valor = row.get(col)

            if valor is None or (isinstance(valor, float) and pd.isna(valor)):
                continue

            v_str = str(valor).strip()
            if not v_str or v_str.lower() == "nan":
                continue

            partes_variacao.append(v_str)
            tokens_remover.extend(gerar_tokens_equivalentes(v_str, col))

        base = remover_tokens(descricao, tokens_remover)

        nome_base.append(base)
        nome_variacao.append(" ".join(partes_variacao).strip())

    df["Nome_Produto_Base"] = nome_base
    df["Nome_Variacao"] = nome_variacao

    return df
