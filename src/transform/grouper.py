import os
import json
import time
import shutil
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx"
ARQUIVO_SAIDA = "produtos_variacoes_shopee_api.xlsx"
ABA_ENTRADA = "Sheet1"

COLUNA_NOME_BASE = "nome_base"
COLUNA_VARIACAO = "variacao"

MODELO = "gpt-4.1-mini"
TAMANHO_LOTE = 10
PAUSA_ENTRE_LOTES = 1.0

# 1 = testa 1 lote / None = processa tudo
MAX_LOTES = None

# Se True, reprocessa somente linhas com outra_variacao preenchida
REPROCESSAR_OUTRA_VARIACAO = False

# Prefixo do grupo
PREFIXO_GRUPO = "G"

# =========================================================
# CLIENTE OPENAI
# =========================================================

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Defina a variável OPENAI_API_KEY antes de rodar o script.")

client = OpenAI(api_key=api_key)

# =========================================================
# PROMPT
# =========================================================

INSTRUCOES = """
Você é um classificador de variações de catálogo de produtos no padrão Shopee.

Receberá uma lista JSON. Cada item terá:
- id_linha
- nome_base
- variacao

Sua tarefa é analisar a variacao usando o contexto do nome_base.

Objetivo:
A Shopee aceita no máximo 2 variações por produto.
Portanto, você deve:
1. extrair corretamente os atributos técnicos da variacao;
2. escolher no máximo 2 eixos principais de variação no padrão Shopee.

Retorne, para cada item:
- cor
- tamanho
- medida
- voltagem
- capacidade
- peso
- amperagem
- potencia_watts
- lumens
- temperatura_cor
- granulacao
- formato
- modelo
- tipo
- material
- acabamento
- outra_variacao
- variacao_1_nome
- variacao_1_valor
- variacao_2_nome
- variacao_2_valor
- status_extracao
- motivo_extracao

Regras obrigatórias:
1. Use o nome_base como contexto para interpretar a variacao.
2. Não invente informação.
3. Se a variacao contiver medida técnica, coloque em medida.
4. Se a variacao contiver cor, coloque em cor.
5. Se a variacao contiver tamanho, coloque em tamanho.
6. Se a variacao contiver voltagem, coloque em voltagem.
7. Se a variacao contiver capacidade, coloque em capacidade.
8. Se a variacao contiver peso, coloque em peso.
9. Se a variacao contiver amperagem, coloque em amperagem.
10. Se a variacao contiver potência em watts, coloque em potencia_watts.
11. Se a variacao contiver fluxo luminoso, coloque em lumens.
12. Se a variacao contiver temperatura de cor, coloque em temperatura_cor.
13. Se a variacao contiver granulacao, coloque em granulacao.
14. Se a variacao contiver formato, coloque em formato.
15. Se a variacao contiver material, coloque em material.
16. Se a variacao contiver acabamento, coloque em acabamento.
17. Se a variacao contiver padrão técnico do produto, classifique em tipo.
18. Padrões de tomada, módulos, espelhos e placas devem ir em tipo, por exemplo:
   - 2P+T 10A
   - 2P + T 10A
   - 2P+T 20A
   - 1 MODULO
   - 2 MODULOS
   - DISTRIBUICAO
   - 2 INTERRUPTOR
   - FURO
   - CEGA
   - CEGA REDONDO
19. Se a variacao contiver um código ou nome de linha/modelo, classifique em modelo.
20. O que não couber claramente nas categorias principais deve ir para outra_variacao.
21. Depois de extrair todos os atributos, escolha no máximo 2 variações principais para Shopee:
   - variacao_1_nome
   - variacao_1_valor
   - variacao_2_nome
   - variacao_2_valor
22. Se houver apenas 1 atributo relevante, preencha apenas variacao_1.
23. Se não houver variação, deixe variacao_1 e variacao_2 vazias.
24. Se houver mais de 2 atributos, escolha os 2 mais importantes comercialmente para diferenciar o produto.
25. Critério de prioridade padrão para escolher as 2 variações principais:
   1. voltagem
   2. medida
   3. tamanho
   4. cor
   5. capacidade
   6. peso
   7. amperagem
   8. potencia_watts
   9. temperatura_cor
   10. modelo
   11. tipo
   12. acabamento
   13. material
   14. lumens
   15. granulacao
   16. formato
26. Preserve exatamente o id_linha recebido.
27. Retorne um item para cada item de entrada.
28. Responda apenas no schema fornecido.
29. Use nomes amigáveis para variacao_1_nome e variacao_2_nome, como:
   Cor, Tamanho, Medida, Voltagem, Capacidade, Peso, Amperagem,
   Potência, Lumens, Temperatura de Cor, Granulação, Formato,
   Modelo, Tipo, Material, Acabamento.
"""

# =========================================================
# SCHEMA
# =========================================================

SCHEMA = {
    "type": "object",
    "properties": {
        "itens": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id_linha": {"type": "integer"},
                    "cor": {"type": "string"},
                    "tamanho": {"type": "string"},
                    "medida": {"type": "string"},
                    "voltagem": {"type": "string"},
                    "capacidade": {"type": "string"},
                    "peso": {"type": "string"},
                    "amperagem": {"type": "string"},
                    "potencia_watts": {"type": "string"},
                    "lumens": {"type": "string"},
                    "temperatura_cor": {"type": "string"},
                    "granulacao": {"type": "string"},
                    "formato": {"type": "string"},
                    "modelo": {"type": "string"},
                    "tipo": {"type": "string"},
                    "material": {"type": "string"},
                    "acabamento": {"type": "string"},
                    "outra_variacao": {"type": "string"},
                    "variacao_1_nome": {"type": "string"},
                    "variacao_1_valor": {"type": "string"},
                    "variacao_2_nome": {"type": "string"},
                    "variacao_2_valor": {"type": "string"},
                    "status_extracao": {
                        "type": "string",
                        "enum": ["ok", "revisar", "sem_variacao"]
                    },
                    "motivo_extracao": {"type": "string"}
                },
                "required": [
                    "id_linha",
                    "cor",
                    "tamanho",
                    "medida",
                    "voltagem",
                    "capacidade",
                    "peso",
                    "amperagem",
                    "potencia_watts",
                    "lumens",
                    "temperatura_cor",
                    "granulacao",
                    "formato",
                    "modelo",
                    "tipo",
                    "material",
                    "acabamento",
                    "outra_variacao",
                    "variacao_1_nome",
                    "variacao_1_valor",
                    "variacao_2_nome",
                    "variacao_2_valor",
                    "status_extracao",
                    "motivo_extracao"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": ["itens"],
    "additionalProperties": False
}

# =========================================================
# COLUNAS
# =========================================================

COLUNAS_RESULTADO = [
    "cor",
    "tamanho",
    "medida",
    "voltagem",
    "capacidade",
    "peso",
    "amperagem",
    "potencia_watts",
    "lumens",
    "temperatura_cor",
    "granulacao",
    "formato",
    "modelo",
    "tipo",
    "material",
    "acabamento",
    "outra_variacao",
    "variacao_1_nome",
    "variacao_1_valor",
    "variacao_2_nome",
    "variacao_2_valor",
    "status_extracao",
    "motivo_extracao",
    "modo_classificacao_variacao",
    "grupo_id",
    "tipo_grupo",
]

# =========================================================
# LEITURA SEGURA
# =========================================================

def arquivo_existe_e_nao_vazio(caminho: str) -> bool:
    return os.path.exists(caminho) and os.path.getsize(caminho) > 0

def ler_excel_seguro(caminho: str, aba_preferida: Optional[str] = None) -> pd.DataFrame:
    if not arquivo_existe_e_nao_vazio(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado ou vazio: {caminho}")

    try:
        xls = pd.ExcelFile(caminho, engine="openpyxl")
    except Exception as e:
        raise RuntimeError(
            f"Não foi possível abrir o arquivo Excel '{caminho}'. "
            f"Provável arquivo corrompido ou formato inválido. Erro: {e}"
        )

    abas = xls.sheet_names
    if not abas:
        raise RuntimeError(f"O arquivo '{caminho}' não possui abas legíveis.")

    if aba_preferida and aba_preferida in abas:
        return pd.read_excel(caminho, sheet_name=aba_preferida, engine="openpyxl")

    return pd.read_excel(caminho, sheet_name=abas[0], engine="openpyxl")

# =========================================================
# SALVAMENTO SEGURO
# =========================================================

def salvar_checkpoint_seguro(df: pd.DataFrame) -> None:
    arquivo_temp = ARQUIVO_SAIDA + ".tmp.xlsx"
    arquivo_backup = ARQUIVO_SAIDA + ".bak"

    with pd.ExcelWriter(arquivo_temp, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        if "status_extracao" in df.columns:
            df[df["status_extracao"] == "revisar"].to_excel(
                writer, index=False, sheet_name="revisar_variacoes"
            )
            df[df["status_extracao"] == "sem_variacao"].to_excel(
                writer, index=False, sheet_name="sem_variacao"
            )

    if os.path.exists(ARQUIVO_SAIDA):
        shutil.copy2(ARQUIVO_SAIDA, arquivo_backup)

    os.replace(arquivo_temp, ARQUIVO_SAIDA)

# =========================================================
# AUXILIARES
# =========================================================

def garantir_colunas(df: pd.DataFrame) -> pd.DataFrame:
    for col in COLUNAS_RESULTADO:
        if col not in df.columns:
            df[col] = None
    return df

def linha_processada(row: pd.Series) -> bool:
    valor = row.get("modo_classificacao_variacao")
    return pd.notna(valor) and str(valor).strip() != ""

def limpar_flag_reprocessamento(df: pd.DataFrame) -> pd.DataFrame:
    if not REPROCESSAR_OUTRA_VARIACAO:
        return df

    if "outra_variacao" not in df.columns:
        return df

    for i in range(len(df)):
        outra = str(df.at[i, "outra_variacao"]).strip() if pd.notna(df.at[i, "outra_variacao"]) else ""
        if outra:
            df.at[i, "modo_classificacao_variacao"] = None

    return df

def montar_lotes_pendentes(df: pd.DataFrame) -> List[List[int]]:
    pendentes = [i for i in range(len(df)) if not linha_processada(df.iloc[i])]
    return [pendentes[i:i + TAMANHO_LOTE] for i in range(0, len(pendentes), TAMANHO_LOTE)]

def preencher_fallback(df: pd.DataFrame, indices: List[int], erro: str) -> None:
    for idx in indices:
        variacao = ""
        if pd.notna(df.at[idx, COLUNA_VARIACAO]):
            variacao = str(df.at[idx, COLUNA_VARIACAO]).strip()

        df.at[idx, "cor"] = ""
        df.at[idx, "tamanho"] = ""
        df.at[idx, "medida"] = ""
        df.at[idx, "voltagem"] = ""
        df.at[idx, "capacidade"] = ""
        df.at[idx, "peso"] = ""
        df.at[idx, "amperagem"] = ""
        df.at[idx, "potencia_watts"] = ""
        df.at[idx, "lumens"] = ""
        df.at[idx, "temperatura_cor"] = ""
        df.at[idx, "granulacao"] = ""
        df.at[idx, "formato"] = ""
        df.at[idx, "modelo"] = ""
        df.at[idx, "tipo"] = ""
        df.at[idx, "material"] = ""
        df.at[idx, "acabamento"] = ""
        df.at[idx, "outra_variacao"] = variacao
        df.at[idx, "variacao_1_nome"] = ""
        df.at[idx, "variacao_1_valor"] = ""
        df.at[idx, "variacao_2_nome"] = ""
        df.at[idx, "variacao_2_valor"] = ""
        df.at[idx, "status_extracao"] = "revisar" if variacao else "sem_variacao"
        df.at[idx, "motivo_extracao"] = f"Erro no lote: {erro}"
        df.at[idx, "modo_classificacao_variacao"] = "erro_lote"

# =========================================================
# AGRUPAMENTO
# =========================================================

def chave_ordenacao_grupo(row: pd.Series) -> tuple:
    v1 = str(row.get("variacao_1_valor") or "").strip()
    v2 = str(row.get("variacao_2_valor") or "").strip()
    var = str(row.get(COLUNA_VARIACAO) or "").strip()
    return (v1, v2, var)

def gerar_grupos(df: pd.DataFrame) -> pd.DataFrame:
    df["grupo_id"] = None
    df["tipo_grupo"] = None

    if COLUNA_NOME_BASE not in df.columns:
        return df

    base_series = df[COLUNA_NOME_BASE].fillna("").astype(str).str.strip()

    nomes_base_unicos = sorted([nb for nb in base_series.unique() if nb])

    mapa_grupo: Dict[str, str] = {}
    for i, nome_base in enumerate(nomes_base_unicos, start=1):
        mapa_grupo[nome_base] = f"{PREFIXO_GRUPO}{i:05d}"

    for nome_base, grupo_df in df.groupby(COLUNA_NOME_BASE, dropna=False, sort=False):
        nome_base_limpo = str(nome_base).strip() if pd.notna(nome_base) else ""

        if not nome_base_limpo:
            for idx in grupo_df.index:
                df.at[idx, "grupo_id"] = ""
                df.at[idx, "tipo_grupo"] = "unico"
            continue

        grupo_id = mapa_grupo[nome_base_limpo]
        indices = list(grupo_df.index)

        if len(indices) == 1:
            idx = indices[0]
            df.at[idx, "grupo_id"] = grupo_id
            df.at[idx, "tipo_grupo"] = "unico"
            continue

        ordenado = grupo_df.sort_values(
            by=[],
            key=None
        )

        indices_ordenados = sorted(indices, key=lambda idx: chave_ordenacao_grupo(df.loc[idx]))

        for pos, idx in enumerate(indices_ordenados):
            df.at[idx, "grupo_id"] = grupo_id
            df.at[idx, "tipo_grupo"] = "pai" if pos == 0 else "filho"

    return df

# =========================================================
# API
# =========================================================

def enviar_lote_api(lote: List[Dict[str, Any]]) -> Dict[str, Any]:
    response = client.responses.create(
        model=MODELO,
        instructions=INSTRUCOES,
        input=f"Itens para classificar:\n{json.dumps(lote, ensure_ascii=False)}",
        text={
            "format": {
                "type": "json_schema",
                "name": "classificacao_variacoes_shopee",
                "schema": SCHEMA,
                "strict": True
            }
        }
    )
    return json.loads(response.output_text)

# =========================================================
# PROCESSAMENTO
# =========================================================

def carregar_base() -> pd.DataFrame:
    if arquivo_existe_e_nao_vazio(ARQUIVO_SAIDA):
        return ler_excel_seguro(ARQUIVO_SAIDA, "Sheet1")

    return ler_excel_seguro(ARQUIVO_ENTRADA, ABA_ENTRADA)

def validar_colunas(df: pd.DataFrame) -> None:
    if COLUNA_NOME_BASE not in df.columns:
        raise ValueError(
            f"Coluna '{COLUNA_NOME_BASE}' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    if COLUNA_VARIACAO not in df.columns:
        raise ValueError(
            f"Coluna '{COLUNA_VARIACAO}' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

def processar_planilha() -> None:
    df = carregar_base()
    validar_colunas(df)

    df = garantir_colunas(df)
    df = limpar_flag_reprocessamento(df)

    lotes = montar_lotes_pendentes(df)
    if MAX_LOTES is not None:
        lotes = lotes[:MAX_LOTES]

    total_lotes = len(lotes)

    if total_lotes == 0:
        print("Nenhum lote pendente. Tudo já foi classificado.")
        df = gerar_grupos(df)
        salvar_checkpoint_seguro(df)
        return

    for n_lote, indices in enumerate(lotes, start=1):
        lote = []

        for idx in indices:
            nome_base = ""
            variacao = ""

            if pd.notna(df.at[idx, COLUNA_NOME_BASE]):
                nome_base = str(df.at[idx, COLUNA_NOME_BASE]).strip()

            if pd.notna(df.at[idx, COLUNA_VARIACAO]):
                variacao = str(df.at[idx, COLUNA_VARIACAO]).strip()

            lote.append({
                "id_linha": int(idx),
                "nome_base": nome_base,
                "variacao": variacao
            })

        print(f"\n=== LOTE {n_lote}/{total_lotes} ===")
        print(f"Linhas: {indices}")

        try:
            resposta = enviar_lote_api(lote)
            itens = resposta.get("itens", [])

            recebidos = {item["id_linha"]: item for item in itens}
            faltando = [idx for idx in indices if idx not in recebidos]

            if faltando:
                raise ValueError(f"Resposta incompleta. IDs faltando: {faltando}")

            for idx in indices:
                item = recebidos[idx]

                df.at[idx, "cor"] = item["cor"]
                df.at[idx, "tamanho"] = item["tamanho"]
                df.at[idx, "medida"] = item["medida"]
                df.at[idx, "voltagem"] = item["voltagem"]
                df.at[idx, "capacidade"] = item["capacidade"]
                df.at[idx, "peso"] = item["peso"]
                df.at[idx, "amperagem"] = item["amperagem"]
                df.at[idx, "potencia_watts"] = item["potencia_watts"]
                df.at[idx, "lumens"] = item["lumens"]
                df.at[idx, "temperatura_cor"] = item["temperatura_cor"]
                df.at[idx, "granulacao"] = item["granulacao"]
                df.at[idx, "formato"] = item["formato"]
                df.at[idx, "modelo"] = item["modelo"]
                df.at[idx, "tipo"] = item["tipo"]
                df.at[idx, "material"] = item["material"]
                df.at[idx, "acabamento"] = item["acabamento"]
                df.at[idx, "outra_variacao"] = item["outra_variacao"]
                df.at[idx, "variacao_1_nome"] = item["variacao_1_nome"]
                df.at[idx, "variacao_1_valor"] = item["variacao_1_valor"]
                df.at[idx, "variacao_2_nome"] = item["variacao_2_nome"]
                df.at[idx, "variacao_2_valor"] = item["variacao_2_valor"]
                df.at[idx, "status_extracao"] = item["status_extracao"]
                df.at[idx, "motivo_extracao"] = item["motivo_extracao"]
                df.at[idx, "modo_classificacao_variacao"] = "api_lote"

                print(
                    f"[linha {idx}] "
                    f"V1='{item['variacao_1_nome']}: {item['variacao_1_valor']}' | "
                    f"V2='{item['variacao_2_nome']}: {item['variacao_2_valor']}'"
                )

            df = gerar_grupos(df)
            salvar_checkpoint_seguro(df)
            print(f"Lote {n_lote} salvo com sucesso em {ARQUIVO_SAIDA}.")
            time.sleep(PAUSA_ENTRE_LOTES)

        except KeyboardInterrupt:
            print("\nInterrompido manualmente. Salvando progresso...")
            df = gerar_grupos(df)
            salvar_checkpoint_seguro(df)
            print("Progresso salvo.")
            raise

        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            print(f"Erro no lote {n_lote}: {erro}")
            preencher_fallback(df, indices, erro)
            df = gerar_grupos(df)
            salvar_checkpoint_seguro(df)
            print(f"Lote {n_lote} salvo como revisão manual.")

    print(f"\nConcluído. Arquivo salvo em: {ARQUIVO_SAIDA}")

# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    processar_planilha()
