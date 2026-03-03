import re

import pandas as pd

COLUNAS_ATRIBUTOS_POR_DOMINIO = {
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
    ],
    "HIDRAULICA": [
        "Medida",
        "Cor",
    ],
}

COLUNAS_REMOVE_TEXTO = COLUNAS_ATRIBUTOS_POR_DOMINIO
COLUNAS_VARIACAO_POR_DOMINIO = COLUNAS_ATRIBUTOS_POR_DOMINIO

FORMATACAO_VARIACOES = {
    "Amperagem": lambda v: f"{_amp_to_int_str(v)}A",
    "Polos": lambda v: str(v),
    "Cor": lambda v: str(v),
    "Formato": lambda v: str(v),
    "Potencia_W": lambda v: str(v),
    "Temperatura_Cor": lambda v: str(v),
    "Tipo_Lampada": lambda v: str(v),
    "Diametro": lambda v: str(v),
    "Comprimento_Venda": lambda v: str(v),
    "Formato_Caixa": lambda v: str(v),
    "Capacidade_Centrinho": lambda v: str(v),
}


def _amp_to_int_str(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""

    s = str(valor).strip().replace(",", ".")
    if not s:
        return ""

    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return s
    except ValueError:
        # se vier "10A" por algum motivo
        s = s.upper().replace("A", "").strip()
        try:
            f = float(s)
            if f.is_integer():
                return str(int(f))
            return s
        except ValueError:
            return s


def _normalizar_numero_tokens(valor) -> set[str]:
    s = str(valor).strip()
    if not s:
        return set()

    s_up = s.upper().replace(",", ".")
    tokens = {s_up, s_up.replace(".", ",")}

    try:
        f = float(s_up)
        if f.is_integer():
            n = str(int(f))
            tokens.add(n)
            tokens.add(n + ".0")
            tokens.add(n + ",0")
    except ValueError:
        pass

    return tokens


def gerar_tokens_equivalentes(valor, campo):
    tokens = []

    v_raw = str(valor).strip()
    if not v_raw:
        return []

    v = v_raw.upper().replace(",", ".")
    v_sem_aspas = v.replace('"', "")

    if campo == "Amperagem":
        for n in _normalizar_numero_tokens(valor):
            n_up = n.upper()
            tokens.extend(
                [
                    n_up,
                    f"{n_up}A",
                    f"{n_up} A",
                ]
            )

        base_int = _amp_to_int_str(valor)
        if base_int:
            tokens.extend([base_int, f"{base_int}A", f"{base_int} A"])

    elif campo == "Polos":
        tokens.append(v)
        if v == "1P":
            tokens.append("UNIPOLAR")
        elif v == "2P":
            tokens.append("BIPOLAR")
        elif v == "3P":
            tokens.append("TRIPOLAR")

    elif campo == "Comprimento_Venda":
        s = v.replace("METROS", "").replace("METRO", "").replace("MT", "").replace("M", "").strip()
        if s:
            for n in _normalizar_numero_tokens(s):
                n_up = n.upper()
                tokens.extend(
                    [
                        f"{n_up}M",
                        f"{n_up} M",
                        f"{n_up}MT",
                        f"{n_up} MT",
                        f"{n_up}METRO",
                        f"{n_up} METRO",
                        f"{n_up}METROS",
                        f"{n_up} METROS",
                    ]
                )

    elif campo == "Diametro":
        if "/" in v_sem_aspas:
            tokens.extend(
                [
                    v_sem_aspas,
                    f'{v_sem_aspas}"',
                    v,
                ]
            )
        for n in _normalizar_numero_tokens(v_sem_aspas.replace("MM", "").strip()):
            n_up = n.upper()
            tokens.extend([f"{n_up}MM", f"{n_up} MM"])

        if "X" in v_sem_aspas:
            tokens.extend(
                [v_sem_aspas, v_sem_aspas.replace("X", "x"), v_sem_aspas.replace("X", "x") + "MM"]
            )

    elif campo == "Formato_Caixa":
        tokens.extend(
            [
                v,
                v.replace("X", "x"),
                v.replace("x", "X"),
            ]
        )

    elif campo == "Capacidade_Centrinho":
        tokens.append(v)
        if "/" in v_sem_aspas:
            tokens.extend([v_sem_aspas, f'{v_sem_aspas}"'])

    elif campo == "Potencia_W":
        for n in _normalizar_numero_tokens(v_sem_aspas.replace("W", "").strip()):
            n_up = n.upper()
            tokens.extend([f"{n_up}W", f"{n_up} W"])

    else:
        tokens.append(v)

    tokens = list({t for t in tokens if t and t != "NAN" and t != "NONE"})
    return tokens


def gerar_nome_variacao(row, campos_variacao, formatacao_map):
    partes = []

    for campo in campos_variacao:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None or str(valor).strip() == "":
            continue

        formatter = formatacao_map.get(campo, lambda v: str(v))
        try:
            partes.append(str(formatter(valor)).strip())
        except Exception:
            partes.append(str(valor).strip())

    return re.sub(r"\s{2,}", " ", " ".join(partes)).strip()


def gerar_nome_base(row, colunas_remove):
    desc = row.get("Descricao_Limpa")
    if not isinstance(desc, str) or not desc.strip():
        return None

    texto = desc.upper()

    for campo in colunas_remove:
        valor = row.get(campo)

        if pd.isna(valor) or valor is None or str(valor).strip() == "":
            continue

        tokens = gerar_tokens_equivalentes(valor, campo)

        for token in tokens:
            texto = re.sub(
                rf"(?<![A-Z0-9/]){re.escape(token)}(?![A-Z0-9/])",
                "",
                texto,
                flags=re.IGNORECASE,
            )

    # limpeza final
    texto = re.sub(r"\s{2,}", " ", texto).strip(" -_/")
    return texto if texto else None


# =========================
# EXECUÇÃO
# =========================
df_eletrica = pd.read_excel(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados_Por_Dominio.xlsx",
    dtype=str,
)

dominio = "HIDRAULICA"
campos_remove = COLUNAS_REMOVE_TEXTO[dominio]
campos_variacao = COLUNAS_VARIACAO_POR_DOMINIO[dominio]

df_eletrica["Nome_Produto_Base"] = df_eletrica.apply(
    lambda row: gerar_nome_base(row, campos_remove), axis=1
)

df_eletrica["Nome_Variacao"] = df_eletrica.apply(
    lambda row: gerar_nome_variacao(row, campos_variacao, FORMATACAO_VARIACOES), axis=1
)

df_eletrica.to_excel("NomeEletrica.xlsx", index=False)
