import re
import time
import unicodedata
from difflib import SequenceMatcher

import pandas as pd
from openai import OpenAI

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/notebooks/produtos_tratados.xlsx"
ARQUIVO_SAIDA = "produtos_pais_similares.xlsx"

COLUNA_CODIGO = "Código"
COLUNA_DESCRICAO = "Descrição"
OPENAI_API_KEY = ""
# Coluna que identifica produto pai
# Exemplo:
# Produto pai -> codigo pai vazio
# Produto filho -> possui codigo pai
COLUNA_CODIGO_PAI = "Código Pai"

MODELO = "gpt-4.1-mini"

# Similaridade mínima local
SIMILARIDADE_MINIMA = 0.90

# Quantidade de pares enviados por lote
TAMANHO_LOTE = 80

# =========================================================
# OPENAI
# =========================================================

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# NORMALIZAÇÃO
# =========================================================


def remover_acentos(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return texto.encode("ASCII", "ignore").decode("utf-8")


def normalizar_texto(texto):
    """
    Normalização genérica e abrangente.
    """

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    # Remove acentos
    texto = remover_acentos(texto)

    # Remove caracteres especiais
    texto = re.sub(r"[^\w\s]", " ", texto)

    # Remove múltiplos espaços
    texto = re.sub(r"\s+", " ", texto).strip()

    # Remove palavras pouco relevantes
    stopwords = {
        "DE",
        "DA",
        "DO",
        "DAS",
        "DOS",
        "COM",
        "PARA",
        "POR",
        "EM",
        "A",
        "O",
        "AS",
        "OS",
        "UM",
        "UMA",
        "UN",
        "UNI",
    }

    palavras = texto.split()

    palavras_filtradas = []

    for palavra in palavras:
        # Remove letras repetidas exageradas
        palavra = re.sub(r"(.)\1{2,}", r"\1", palavra)

        # Remove espaços
        palavra = palavra.strip()

        if palavra not in stopwords:
            palavras_filtradas.append(palavra)

    # Ordena palavras
    # ajuda:
    # CAIXA AGUA
    # AGUA CAIXA
    palavras_filtradas.sort()

    texto_final = " ".join(palavras_filtradas)

    return texto_final


# =========================================================
# SIMILARIDADE
# =========================================================


def similaridade(a, b):
    return SequenceMatcher(None, a, b).ratio()


# =========================================================
# OPENAI
# =========================================================


def analisar_lote_openai(lote_texto):
    prompt = f"""
Você é especialista em catalogação de produtos.

Analise os produtos abaixo e encontre itens que provavelmente representam o MESMO PRODUTO BASE.

Considere:
- erros de digitação
- singular/plural
- acentos
- caracteres especiais
- palavras invertidas
- abreviações
- marcas escritas diferente
- palavras irrelevantes
- descrições duplicadas
- pequenas diferenças de escrita

Exemplos:
CAIXA DAGUA
CAIXA D'AGUA
CAIXA DE AGUA

REBITE ALUMINIO NEWFIX
REBITE ALUMINIO REPUXO NEW FIX

PARAFUSO SEXTAVADO
PARAFUSO CAB SEXT

Retorne SOMENTE JSON válido no formato:

[
  {{
    "grupo": 1,
    "motivo": "descrições muito parecidas",
    "produtos": [
      {{
        "codigo": "123",
        "descricao": "ABC"
      }},
      {{
        "codigo": "456",
        "descricao": "DEF"
      }}
    ]
  }}
]

Produtos:
{lote_texto}
"""

    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[
            {
                "role": "system",
                "content": "Você é especialista em agrupamento de catálogo.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    return resposta.choices[0].message.content


# =========================================================
# LEITURA
# =========================================================

print("Lendo planilha...")

if ARQUIVO_ENTRADA.lower().endswith(".csv"):
    df = pd.read_csv(ARQUIVO_ENTRADA, dtype=str)
else:
    df = pd.read_excel(ARQUIVO_ENTRADA, dtype=str)

df = df.fillna("")

# =========================================================
# FILTRAR SOMENTE PRODUTOS PAI
# =========================================================

print("Filtrando produtos pai...")

df_pais = df[(df[COLUNA_CODIGO_PAI].astype(str).str.strip() == "")].copy()

print(f"Produtos pai encontrados: {len(df_pais)}")

# =========================================================
# NORMALIZAÇÃO
# =========================================================

print("Normalizando descrições...")

df_pais["descricao_normalizada"] = df_pais[COLUNA_DESCRICAO].apply(normalizar_texto)

# =========================================================
# PRÉ-AGRUPAMENTO
# =========================================================

print("Buscando candidatos similares...")

pares = []

descricoes = df_pais["descricao_normalizada"].tolist()

for i in range(len(df_pais)):
    desc1 = descricoes[i]

    for j in range(i + 1, len(df_pais)):
        desc2 = descricoes[j]

        score = similaridade(desc1, desc2)

        # filtro inicial
        if score >= SIMILARIDADE_MINIMA:
            pares.append(
                {
                    "codigo_1": df_pais.iloc[i][COLUNA_CODIGO],
                    "descricao_1": df_pais.iloc[i][COLUNA_DESCRICAO],
                    "normalizada_1": desc1,
                    "codigo_2": df_pais.iloc[j][COLUNA_CODIGO],
                    "descricao_2": df_pais.iloc[j][COLUNA_DESCRICAO],
                    "normalizada_2": desc2,
                    "similaridade": round(score, 4),
                }
            )

print(f"Pares candidatos encontrados: {len(pares)}")

df_pares = pd.DataFrame(pares)

# =========================================================
# LOTES OPENAI
# =========================================================

resultado_openai = []

if len(df_pares) > 0:
    lotes = [df_pares.iloc[i : i + TAMANHO_LOTE] for i in range(0, len(df_pares), TAMANHO_LOTE)]

    print(f"Lotes para OpenAI: {len(lotes)}")

    for idx, lote_df in enumerate(lotes, start=1):
        print(f"Processando lote {idx}/{len(lotes)}")

        texto_lote = ""

        codigos_adicionados = set()

        for _, row in lote_df.iterrows():
            if row["codigo_1"] not in codigos_adicionados:
                texto_lote += f"""
CODIGO: {row['codigo_1']}
DESCRICAO: {row['descricao_1']}
"""

                codigos_adicionados.add(row["codigo_1"])

            if row["codigo_2"] not in codigos_adicionados:
                texto_lote += f"""
CODIGO: {row['codigo_2']}
DESCRICAO: {row['descricao_2']}
"""

                codigos_adicionados.add(row["codigo_2"])

        try:
            resposta = analisar_lote_openai(texto_lote)

            resultado_openai.append(
                {
                    "lote": idx,
                    "resultado": resposta,
                }
            )

            print("OK")

        except Exception as e:
            print(f"Erro no lote {idx}: {e}")

        time.sleep(1)

# =========================================================
# EXPORTAÇÃO
# =========================================================

print("Exportando resultado...")

with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
    df_pais.to_excel(
        writer,
        sheet_name="Produtos_Pai",
        index=False,
    )

    if len(df_pares) > 0:
        df_pares.to_excel(
            writer,
            sheet_name="Candidatos",
            index=False,
        )

    if len(resultado_openai) > 0:
        pd.DataFrame(resultado_openai).to_excel(
            writer,
            sheet_name="Analise_OpenAI",
            index=False,
        )

print()
print("===================================")
print("FINALIZADO")
print("===================================")
print(f"Arquivo salvo: {ARQUIVO_SAIDA}")
