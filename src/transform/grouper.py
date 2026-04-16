import re
from typing import Dict, List, Tuple

import pandas as pd

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx"
ARQUIVO_SAIDA = "produtos_variacoes_separadas_v2.xlsx"
ABA_ENTRADA = "processados"
COLUNA_NOME_BASE = "nome_base"
COLUNA_VARIACAO = "variacao"

# =========================================================
# DICIONÁRIOS
# =========================================================

ABREVIACOES = {
    r"\bPTO\b": "PRETO",
    r"\bPTA\b": "PRETA",
    r"\bBRC\b": "BRANCO",
    r"\bBRCA\b": "BRANCA",
    r"\bAZ\b": "AZUL",
    r"\bVM\b": "VERMELHO",
    r"\bVD\b": "VERDE",
    r"\bAM\b": "AMARELO",
    r"\bTRANSP\b": "TRANSPARENTE",
    r"\bMED\b": "MEDIO",
    r"\bMÉD\b": "MEDIO",
    r"\bPEQ\b": "PEQUENO",
    r"\bGRD\b": "GRANDE",
    r"\bALUM\b": "ALUMINIO",
    r"\bGALV\b": "GALVANIZADO",
    r"\bCROM\b": "CROMADO",
    r"\bINOX\b": "INOX",
}

CORES = {
    "PRETO",
    "PRETA",
    "BRANCO",
    "BRANCA",
    "AZUL",
    "VERDE",
    "VERMELHO",
    "VERMELHA",
    "AMARELO",
    "AMARELA",
    "TRANSPARENTE",
    "ROSA",
    "ROXO",
    "ROXA",
    "LARANJA",
    "CINZA",
    "MARROM",
    "BEGE",
    "PRATA",
    "DOURADO",
    "DOURADA",
}

TAMANHOS = {
    "PP",
    "P",
    "M",
    "G",
    "GG",
    "XG",
    "XGG",
    "PEQUENO",
    "PEQUENA",
    "MEDIO",
    "MEDIA",
    "GRANDE",
}

ACABAMENTOS = {
    "CROMADO",
    "CROMADA",
    "GALVANIZADO",
    "GALVANIZADA",
    "POLIDO",
    "POLIDA",
    "FOSCO",
    "FOSCA",
    "BRILHANTE",
    "ACETINADO",
    "ACETINADA",
    "ESMALTADO",
    "ESMALTADA",
}

MATERIAIS = {
    "PVC",
    "METAL",
    "ALUMINIO",
    "INOX",
    "LATAO",
    "LATÃO",
    "NYLON",
    "PLASTICO",
    "PLÁSTICO",
    "ACO",
    "AÇO",
    "COBRE",
    "BORRACHA",
    "MADEIRA",
    "VIDRO",
}

TIPOS_COMPOSTOS = {
    "SDS PLUS",
    "SDS MAX",
    "AUTO ATARRAXANTE",
    "ROSCA GROSSA",
    "ROSCA FINA",
    "PONTA PHILLIPS",
    "PONTA FENDA",
    "PONTA TORX",
    "DUPLA FACE",
    "ALTA PRESSAO",
    "ALTA PRESSÃO",
    "USO INTERNO",
    "USO EXTERNO",
    "LUZ BRANCA",
    "LUZ AMARELA",
    "LUZ FRIA",
    "LUZ QUENTE",
}

MODELOS_COMPOSTOS_REGEX = [
    r"\bMODELO\s+[A-Z0-9\-\/]+\b",
    r"\bMOD\s+[A-Z0-9\-\/]+\b",
    r"\bLINHA\s+[A-Z0-9\-\/]+\b",
]

# =========================================================
# REGEX MELHORADOS
# =========================================================

# captura:
# 10X160
# 10,0X160
# 10,0 X 160
# 10 X 16
# 10X20X30
REGEX_MEDIDA_COMPOSTA = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*[Xx]\s*\d+(?:[.,]\d+)?(?:\s*[Xx]\s*\d+(?:[.,]\d+)?)?\b"
)

# captura 200MM / 200 MM / 1,5 M / 3 POL / 3 POLEGADAS
REGEX_MEDIDA_SIMPLES = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:MM|CM|M|POL|POLEGADA|POLEGADAS)\b")

REGEX_FRACAO = re.compile(r"\b\d+/\d+\b")

REGEX_VOLTAGEM = re.compile(r"\b(?:110V|127V|220V|BIVOLT|12V|24V)\b")
REGEX_CAPACIDADE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:ML|L|LT|G|KG)\b")

# modelo simples mais conservador
REGEX_MODELO_SIMPLES = re.compile(r"\b[A-Z]{1,6}\-?\d{1,6}[A-Z0-9\-]*\b")

# =========================================================
# CONTEXTO POR NOME_BASE
# =========================================================

BASES_TECNICAS = {
    "BROCA",
    "SERRA",
    "DISCO",
    "PARAFUSO",
    "BUCHA",
    "ABRACADEIRA",
    "CABO",
    "TORNEIRA",
    "CHAVE",
    "FITA",
    "LAMPADA",
    "LAMPADA",
    "PLUG",
}

BASES_QUE_USAM_TIPO = {"BROCA", "DISCO", "SERRA", "PARAFUSO", "CHAVE", "FITA", "LAMPADA"}


def nome_base_tokens(nome_base: str) -> set:
    return set(limpar_texto(nome_base).split())


# =========================================================
# FUNÇÕES BÁSICAS
# =========================================================


def normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def limpar_texto(texto: str) -> str:
    texto = str(texto or "").upper().strip()
    texto = texto.replace("Á", "A").replace("À", "A").replace("Ã", "A").replace("Â", "A")
    texto = texto.replace("É", "E").replace("Ê", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O").replace("Õ", "O").replace("Ô", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("Ç", "C")

    for padrao, repl in ABREVIACOES.items():
        texto = re.sub(padrao, repl, texto, flags=re.IGNORECASE)

    texto = re.sub(r"[;,|_=*#~`]+", " ", texto)
    texto = normalizar_espacos(texto)
    return texto


def normalizar_medida(valor: str) -> str:
    valor = valor.upper()
    valor = re.sub(r"\s*[Xx]\s*", "X", valor)
    valor = re.sub(r"\s+", " ", valor)
    return valor.strip()


def extrair_regex(texto: str, pattern: re.Pattern) -> Tuple[List[str], str]:
    encontrados = []
    restante = texto

    matches = list(pattern.finditer(restante))
    for m in matches:
        v = normalizar_medida(m.group(0))
        if v not in encontrados:
            encontrados.append(v)

    restante = pattern.sub(" ", restante)
    restante = normalizar_espacos(restante)
    return encontrados, restante


def extrair_compostos(texto: str, compostos: set) -> Tuple[List[str], str]:
    encontrados = []
    restante = texto

    for termo in sorted(compostos, key=len, reverse=True):
        padrao = r"\b" + re.escape(termo) + r"\b"
        if re.search(padrao, restante, flags=re.IGNORECASE):
            encontrados.append(termo.upper())
            restante = re.sub(padrao, " ", restante, flags=re.IGNORECASE)

    restante = normalizar_espacos(restante)
    return encontrados, restante


def extrair_modelos_compostos(texto: str) -> Tuple[List[str], str]:
    encontrados = []
    restante = texto

    for regex in MODELOS_COMPOSTOS_REGEX:
        matches = list(re.finditer(regex, restante, flags=re.IGNORECASE))
        for m in matches:
            valor = normalizar_espacos(m.group(0).upper())
            if valor not in encontrados:
                encontrados.append(valor)
        restante = re.sub(regex, " ", restante, flags=re.IGNORECASE)

    restante = normalizar_espacos(restante)
    return encontrados, restante


# =========================================================
# EXTRAÇÃO
# =========================================================


def extrair_atributos_variacao(nome_base: str, variacao: str) -> Dict[str, str]:
    base_ctx = nome_base_tokens(nome_base)
    texto = limpar_texto(variacao)

    resultado = {
        "cor": "",
        "tamanho": "",
        "medida": "",
        "voltagem": "",
        "capacidade": "",
        "modelo": "",
        "tipo": "",
        "material": "",
        "acabamento": "",
        "outra_variacao": "",
        "status_extracao": "",
    }

    if not texto:
        resultado["status_extracao"] = "sem_variacao"
        return resultado

    # 1) tipo composto
    tipos_compostos, texto = extrair_compostos(texto, TIPOS_COMPOSTOS)

    # 2) modelo composto
    modelos_compostos, texto = extrair_modelos_compostos(texto)

    # 3) medidas antes da tokenização
    medidas1, texto = extrair_regex(texto, REGEX_MEDIDA_COMPOSTA)
    medidas2, texto = extrair_regex(texto, REGEX_MEDIDA_SIMPLES)
    fracoes, texto = extrair_regex(texto, REGEX_FRACAO)

    # 4) voltagem e capacidade
    voltagens, texto = extrair_regex(texto, REGEX_VOLTAGEM)
    capacidades, texto = extrair_regex(texto, REGEX_CAPACIDADE)

    medidas = []
    for grupo in (medidas1, medidas2, fracoes):
        for item in grupo:
            if item not in medidas:
                medidas.append(item)

    # 5) tokenização do restante
    tokens = texto.split()
    sobras = []

    for token in tokens:
        tok = token.upper()

        if tok in CORES and not resultado["cor"]:
            resultado["cor"] = tok
            continue

        if tok in TAMANHOS and not resultado["tamanho"]:
            resultado["tamanho"] = tok
            continue

        if tok in ACABAMENTOS and not resultado["acabamento"]:
            resultado["acabamento"] = tok
            continue

        if tok in MATERIAIS and not resultado["material"]:
            resultado["material"] = tok
            continue

        # modelo simples só quando realmente parece código/modelo
        if REGEX_MODELO_SIMPLES.fullmatch(tok):
            # evita jogar coisas técnicas comuns em modelo
            if tok not in CORES and tok not in TAMANHOS and tok not in MATERIAIS:
                # se contexto sugere item técnico, prefira tipo/modelo conforme base
                if "MODELO" in base_ctx:
                    resultado["modelo"] = f"{resultado['modelo']} {tok}".strip()
                else:
                    sobras.append(tok)
                continue

        sobras.append(tok)

    # 6) consolidação principal
    if medidas:
        resultado["medida"] = " ".join(medidas)

    if voltagens:
        resultado["voltagem"] = " ".join(voltagens)

    if capacidades:
        resultado["capacidade"] = " ".join(capacidades)

    if modelos_compostos:
        resultado["modelo"] = f"{resultado['modelo']} {' '.join(modelos_compostos)}".strip()

    if tipos_compostos:
        resultado["tipo"] = " ".join(tipos_compostos)

    # 7) usar contexto do nome_base para decidir sobras
    sobra_txt = " ".join(sobras).strip()

    if sobra_txt:
        palavras_base = nome_base_tokens(nome_base)

        # se já achou medida e a sobra for curta, pode ser tipo
        if resultado["medida"] and not resultado["tipo"] and len(sobra_txt.split()) <= 3:
            if any(p in palavras_base for p in BASES_QUE_USAM_TIPO):
                resultado["tipo"] = sobra_txt
            else:
                resultado["outra_variacao"] = sobra_txt

        # se não há medida e sobra parece código/modelo
        elif REGEX_MODELO_SIMPLES.fullmatch(sobra_txt.replace(" ", "")) and not resultado["modelo"]:
            resultado["modelo"] = sobra_txt

        # se o contexto for técnico e a sobra for curta, tende a ser tipo
        elif (
            not resultado["tipo"]
            and len(sobra_txt.split()) <= 3
            and any(p in palavras_base for p in BASES_QUE_USAM_TIPO)
        ):
            resultado["tipo"] = sobra_txt

        else:
            resultado["outra_variacao"] = sobra_txt

    # 8) limpeza final para evitar duplicidade
    for chave in ["tipo", "modelo", "material", "acabamento", "cor", "tamanho", "medida"]:
        resultado[chave] = normalizar_espacos(resultado[chave])

    # 9) status
    campos_preenchidos = sum(
        1
        for k, v in resultado.items()
        if k not in {"outra_variacao", "status_extracao"} and str(v).strip()
    )

    if resultado["outra_variacao"]:
        resultado["status_extracao"] = "revisar"
    elif campos_preenchidos > 0:
        resultado["status_extracao"] = "ok"
    else:
        resultado["status_extracao"] = "nao_classificado"

    return resultado


# =========================================================
# PROCESSAMENTO DA PLANILHA
# =========================================================

COLUNAS_NOVAS = [
    "cor",
    "tamanho",
    "medida",
    "voltagem",
    "capacidade",
    "modelo",
    "tipo",
    "material",
    "acabamento",
    "outra_variacao",
    "status_extracao",
]


def ler_planilha(caminho: str, aba: str) -> pd.DataFrame:
    try:
        return pd.read_excel(caminho, sheet_name=aba)
    except Exception:
        return pd.read_excel(caminho)


def processar_planilha() -> None:
    df = ler_planilha(ARQUIVO_ENTRADA, ABA_ENTRADA)

    if COLUNA_VARIACAO not in df.columns:
        raise ValueError(
            f"A coluna '{COLUNA_VARIACAO}' não foi encontrada. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    if COLUNA_NOME_BASE not in df.columns:
        raise ValueError(
            f"A coluna '{COLUNA_NOME_BASE}' não foi encontrada. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    resultados = [
        extrair_atributos_variacao(
            nome_base=row.get(COLUNA_NOME_BASE, ""), variacao=row.get(COLUNA_VARIACAO, "")
        )
        for _, row in df.fillna("").iterrows()
    ]

    resultado_df = pd.DataFrame(resultados)

    for col in COLUNAS_NOVAS:
        if col not in resultado_df.columns:
            resultado_df[col] = ""

    final_df = pd.concat([df, resultado_df[COLUNAS_NOVAS]], axis=1)

    with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl", mode="w") as writer:
        final_df.to_excel(writer, index=False, sheet_name="processados")
        final_df[final_df["status_extracao"] == "revisar"].to_excel(
            writer, index=False, sheet_name="revisar_variacoes"
        )
        final_df[final_df["status_extracao"] == "nao_classificado"].to_excel(
            writer, index=False, sheet_name="nao_classificados"
        )

    print(f"Arquivo salvo com sucesso em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    processar_planilha()
