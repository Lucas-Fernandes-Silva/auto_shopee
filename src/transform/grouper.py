import re
import pandas as pd
from typing import Dict, List, Tuple

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/outputs/final_urls_cloudinary.xlsx"
ARQUIVO_SAIDA = "produtos_variacoes_separadas.xlsx"
ABA_ENTRADA = "processados"   # se não existir, tenta a primeira aba
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
    "PRETO", "PRETA", "BRANCO", "BRANCA", "AZUL", "VERDE",
    "VERMELHO", "VERMELHA", "AMARELO", "AMARELA", "TRANSPARENTE",
    "ROSA", "ROXO", "ROXA", "LARANJA", "CINZA", "MARROM", "BEGE",
    "PRATA", "DOURADO", "DOURADA"
}

TAMANHOS = {
    "PP", "P", "M", "G", "GG", "XG", "XGG",
    "PEQUENO", "PEQUENA", "MEDIO", "MEDIA", "GRANDE"
}

ACABAMENTOS = {
    "CROMADO", "CROMADA", "GALVANIZADO", "GALVANIZADA",
    "POLIDO", "POLIDA", "FOSCO", "FOSCA", "BRILHANTE",
    "ACETINADO", "ACETINADA", "ESMALTADO", "ESMALTADA"
}

MATERIAIS = {
    "PVC", "METAL", "ALUMINIO", "INOX", "LATAO", "LATÃO",
    "NYLON", "PLASTICO", "PLÁSTICO", "ACO", "AÇO",
    "COBRE", "BORRACHA", "MADEIRA", "VIDRO"
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
    r"\bTIPO\s+[A-Z0-9\-\/]+\b",
]

# =========================================================
# REGEX
# =========================================================

REGEX_MEDIDAS = [
    r"\b\d+(?:[.,]\d+)?X\d+(?:[.,]\d+)?(?:X\d+(?:[.,]\d+)?)?\b",     # 10X160 / 10,0X160 / 10X20X30
    r"\b\d+(?:[.,]\d+)?\s?(?:MM|CM|M)\b",                           # 200MM
    r"\b\d+/\d+\b",                                                 # 1/2
    r"\b\d+(?:[.,]\d+)?\s?POL\b",                                   # 3 POL
    r"\b\d+(?:[.,]\d+)?\s?POLEGADAS?\b",
]

REGEX_VOLTAGEM = [
    r"\b110V\b", r"\b127V\b", r"\b220V\b", r"\bBIVOLT\b", r"\b12V\b", r"\b24V\b"
]

REGEX_CAPACIDADE = [
    r"\b\d+(?:[.,]\d+)?\s?(?:ML|L|LT|G|KG)\b"
]

# padrões para classificar como modelo se não entrou em outras classes
REGEX_MODELO = [
    r"\b[A-Z]{1,5}\-?\d{1,5}[A-Z]?\b",      # ex: T50, GSB13, ABC-200
    r"\b\d{3,5}[A-Z]{1,4}\b",               # ex: 2000W? cuidado, depois filtramos
]

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
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def extrair_multiplos_por_regex(texto: str, regex_list: List[str]) -> Tuple[List[str], str]:
    encontrados: List[str] = []
    restante = texto

    for regex in regex_list:
        matches = list(re.finditer(regex, restante, flags=re.IGNORECASE))
        for m in matches:
            valor = normalizar_espacos(m.group(0).upper())
            if valor not in encontrados:
                encontrados.append(valor)

        restante = re.sub(regex, " ", restante, flags=re.IGNORECASE)

    restante = normalizar_espacos(restante)
    return encontrados, restante

def extrair_compostos(texto: str, compostos: set) -> Tuple[List[str], str]:
    encontrados = []
    restante = texto

    # ordenar por tamanho desc para casar primeiro os maiores
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
# EXTRAÇÃO POR TOKENS
# =========================================================

def extrair_atributos_variacao(variacao: str) -> Dict[str, str]:
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

    # 1) compostos de tipo
    tipos_compostos, texto = extrair_compostos(texto, TIPOS_COMPOSTOS)

    # 2) modelos compostos
    modelos_compostos, texto = extrair_modelos_compostos(texto)

    # 3) regex de medida, voltagem, capacidade
    medidas, texto = extrair_multiplos_por_regex(texto, REGEX_MEDIDAS)
    voltagens, texto = extrair_multiplos_por_regex(texto, REGEX_VOLTAGEM)
    capacidades, texto = extrair_multiplos_por_regex(texto, REGEX_CAPACIDADE)

    # 4) tokenização do restante
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

        # modelo simples
        if any(re.fullmatch(rx, tok) for rx in REGEX_MODELO):
            # evita jogar medida/capacidade errada em modelo
            if not re.fullmatch(r"\d+(?:[.,]\d+)?(?:ML|L|LT|G|KG|V|W|A|MM|CM|M)", tok):
                resultado["modelo"] = f"{resultado['modelo']} {tok}".strip()
                continue

        sobras.append(tok)

    # 5) consolidação
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

    # 6) regras finais para sobras
    sobra_txt = " ".join(sobras).strip()

    # se não houve tipo e a sobra for curta/textual, joga em tipo
    if sobra_txt:
        if not resultado["tipo"] and len(sobra_txt.split()) <= 3:
            resultado["tipo"] = sobra_txt
        else:
            resultado["outra_variacao"] = sobra_txt

    # 7) status
    campos_preenchidos = sum(
        1 for k, v in resultado.items()
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

    resultados = df[COLUNA_VARIACAO].fillna("").apply(extrair_atributos_variacao)
    resultado_df = pd.DataFrame(list(resultados))

    # garante ordem das colunas
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

# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    processar_planilha()
