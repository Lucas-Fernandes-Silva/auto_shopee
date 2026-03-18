import re

import pandas as pd

# =========================
# 1) Campos por domínio (1 só fonte)
# =========================
CAMPOS_POR_DOMINIO = {
    "ELETRICA": [
        "Polos",
        "Amperagem",
        "Cor",
        "Medida",
        "Diametro",
        "Comprimento_Venda",
        "Capacidade_Centrinho",
        "Formato",
        "Potencia_W",
        "Temperatura_Cor",
        "Tipo_Lampada",
    ],
    "TOMADAS": [
        "Tipo_Tomada",
        "Amperagem",
        "Polos",
        "Diametro",
        "Comprimento_Venda",
        "Cor",
        "Secao_Cabo",
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
    "HIDRAULICA": ["Medida", "Cor", "Volume", "Diametro", "Peso_Venda", "Comprimento_Venda"],
}

# Se um domínio não estiver configurado, você ainda pode gerar com fallback:
CAMPOS_FALLBACK = ["Medida", "Cor", "Diametro", "Comprimento_Venda"]

# =========================
# 2) Formatação de variação (opcional)
# =========================
FORMATACAO_VARIACOES = {
    "Amperagem": lambda v: v if str(v).upper().endswith("A") else f"{v}A",
    "Potencia_W": lambda v: v if str(v).upper().endswith("W") else f"{v}W",
    "Temperatura_Cor": lambda v: v if str(v).upper().endswith("K") else f"{v}K",
    "Medida": lambda v: str(v),
    "Cor": lambda v: str(v),
    "Diametro": lambda v: str(v),
}


# =========================
# 3) Helpers
# =========================
def normalizar_texto_base(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _safe_remove(texto: str, token: str) -> str:
    if not token:
        return texto

    # normaliza separador de multiplicação no token
    token = token.replace("×", "X")

    # boundary "segura" (não remove dentro de palavra)
    # inclui / e " no conjunto pra token com fração e aspas
    padrao = rf'(?<![A-Z0-9/"]){re.escape(token)}(?![A-Z0-9/"])'
    return re.sub(padrao, " ", texto, flags=re.IGNORECASE)


def _fmt(v: object) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return s


# =========================
# 4) Tokens equivalentes por campo
# =========================
def gerar_tokens_equivalentes(campo: str, valor: object) -> list[str]:
    v_raw = _fmt(valor)
    if not v_raw:
        return []

    campo = str(campo)

    # Normalizações gerais
    v = v_raw.strip()
    v_up = v.upper().replace("×", "X")

    tokens = set()

    # ---------- Medida (AxB, AxBxC, frações) ----------
    if campo == "Medida":
        base = v_up

        # variantes de separador e espaços
        def expand_sep(s: str):
            outs = set()
            for sep in ["X", "x", "×"]:
                s2 = s.replace("X", sep)
                outs.add(s2)
                outs.add(s2.replace(sep, f" {sep} "))
            return outs

        # decimal: ponto/vírgula
        base_dot = base.replace(",", ".")
        base_comma = base.replace(".", ",")

        # remove aspas (às vezes o texto não tem aspas)
        base_no_quotes = base.replace('"', "")

        candidates = {base, base_dot, base_comma, base_no_quotes}

        # Se tem fração e não tem aspas, cria com aspas em cada parte: 3/4X1/2 -> 3/4"X1/2"
        if "/" in base_no_quotes:
            parts = base_no_quotes.split("X")
            if len(parts) in (2, 3):
                with_quotes = "X".join([p + '"' for p in parts])
                candidates.add(with_quotes)
                candidates.add(with_quotes.replace("X", "x"))

        # Unidade “só no final” (catálogo): 0,11X0,70CM
        # Quando a medida vem como 0.11CMX0.70CM, gerar também 0.11X0.70CM
        for unidade in ["CM", "MM", "M"]:
            if unidade in base and "X" in base:
                # remove unidade de todas as partes e deixa só no final
                compact = base.replace(unidade, "")
                candidates.add(compact + unidade)

                compact_dot = base_dot.replace(unidade, "")
                candidates.add(compact_dot + unidade)

                compact_comma = base_comma.replace(unidade, "")
                candidates.add(compact_comma + unidade)

        # gera separadores e espaços
        for c in candidates:
            for e in expand_sep(c):
                tokens.add(e)

        # também gera versão sem espaços
        for t in list(tokens):
            tokens.add(re.sub(r"\s+", "", t))

        return list(tokens)

    # ---------- Comprimento_Venda / Diametro ----------
    if campo in ("Comprimento_Venda", "Diametro"):
        base = v_up
        base_dot = base.replace(",", ".")
        base_comma = base.replace(".", ",")

        # com e sem espaço da unidade
        def unit_space_variants(s: str):
            # 50MM -> 50 MM
            return {s, re.sub(r"(\d)([A-Z])", r"\1 \2", s)}

        for b in {base, base_dot, base_comma}:
            tokens |= unit_space_variants(b)

        return list(tokens)

    # ---------- Amperagem / Potência / Temperatura ----------
    if campo in ("Amperagem", "Potencia_W", "Temperatura_Cor"):
        base = v_up
        # garante unidade nas variantes
        suffix = "A" if campo == "Amperagem" else ("W" if campo == "Potencia_W" else "K")
        if not base.endswith(suffix):
            base2 = base + suffix
        else:
            base2 = base

        tokens.add(base)
        tokens.add(base2)
        tokens.add(base2.replace(suffix, f" {suffix}"))
        return list(tokens)

    # ---------- Polos, Cor, Tipo etc ----------
    # padrão simples: remove exatamente como veio + versão upper
    tokens.add(v)
    tokens.add(v_up)
    return list(tokens)


# =========================
# 5) Gerador Nome Base
# =========================
def gerar_nome_base(row: pd.Series, dominio: str, campos_remover: list[str]) -> str:
    texto = _fmt(row.get("Descricao_Limpa"))
    texto = normalizar_texto_base(texto)
    if not texto:
        return ""

    tokens_para_remover = []

    for campo in campos_remover:
        valor = row.get(campo)
        if valor is None or str(valor).strip() == "":
            continue

        tokens_para_remover.extend(gerar_tokens_equivalentes(campo, valor))

    # remove maiores primeiro (evita sobrar pedaços)
    tokens_para_remover = sorted(set(tokens_para_remover), key=len, reverse=True)

    for token in tokens_para_remover:
        texto = _safe_remove(texto, token)

    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


# =========================
# 6) Gerador Nome Variação
# =========================
def gerar_nome_variacao(row: pd.Series, campos_variacao: list[str]) -> str:
    parts = []
    for campo in campos_variacao:
        valor = row.get(campo)

        # evita None / NaN / "nan"
        if valor is None:
            continue

        s = str(valor).strip()
        if s == "" or s.lower() == "nan":
            continue

        fmt = FORMATACAO_VARIACOES.get(campo)
        if fmt:
            try:
                s = fmt(s)
            except Exception:
                pass

        s = str(s).strip()
        if s and s.lower() != "nan":
            parts.append(s)

    return " ".join(parts).strip()


# =========================
# 7) Aplicar no DF (multi-domínio)
# =========================
def aplicar_nomes(df: pd.DataFrame) -> pd.DataFrame:
    def _campos(dominio: str) -> list[str]:
        return CAMPOS_POR_DOMINIO.get(dominio, CAMPOS_FALLBACK)

    def _process(row: pd.Series) -> pd.Series:
        dominio = _fmt(row.get("Dominio")).upper()
        campos = _campos(dominio)

        nome_base = gerar_nome_base(row, dominio, campos)
        nome_var = gerar_nome_variacao(row, campos)

        return pd.Series(
            {
                "Nome_Produto_Base": nome_base,
                "Nome_Variacao": nome_var,
            }
        )

    nomes = df.apply(_process, axis=1)
    return pd.concat([df, nomes], axis=1)


# # =========================
# # 8) Execução (exemplo)
# # =========================
# if __name__ == "__main__":
#     # Ajuste os paths conforme seu projeto
#     in_path = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Classificados.xlsx"
#     out_path = "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos_Com_Nomes.xlsx"

#     df = pd.read_excel(in_path, dtype=str)
#     # print(df.columns.tolist())
#     # df_out = aplicar_nomes(df)
#     row = df.iloc[3026]  # escolha uma das lampadas de cima
#     print("Descricao_Limpa =>", repr(row.get("Descricao_Limpa")))
#     print("Nome_Variacao =>", gerar_nome_variacao(row, CAMPOS_POR_DOMINIO["ELETRICA"]))
#     print("Nome_Base =>", gerar_nome_base(row, "ELETRICA", CAMPOS_POR_DOMINIO["ELETRICA"]))
#     for campo in CAMPOS_POR_DOMINIO["ELETRICA"]:
#         print(campo, "=>", repr(row.get(campo)))

#     # df_out.to_excel(out_path, index=False)
#     print(f"Arquivo gerado: {out_path}")
