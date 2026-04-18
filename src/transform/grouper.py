import json
import os
import time
from typing import Any, Dict, List

import pandas as pd
from openai import OpenAI

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/outputs/download.xlsx"
ARQUIVO_SAIDA = "produtos_variacoes_api.xlsx"
ABA_ENTRADA = "Sheet1"

COLUNA_NOME_BASE = "nome_base"
COLUNA_VARIACAO = "variacao"

MODELO = "gpt-4.1-mini"  # você pode trocar depois
TAMANHO_LOTE = 10
PAUSA_ENTRE_LOTES = 1.0

# para testar só 1 lote
MAX_LOTES = None  # depois troque para None

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
Você é um classificador de variações de catálogo de produtos.

Receberá uma lista JSON. Cada item terá:
- id_linha
- nome_base
- variacao

Sua tarefa é analisar a variacao usando o contexto do nome_base e devolver,
para cada item, os atributos separados nos campos corretos.

Se outra_variacao não estiver vazia, tente redistribuir corretamente os termos nas categorias antes de manter em outra_variacao.

Preencha estes campos:
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
21. status_extracao deve ser:
   - "ok" quando a classificação estiver clara
   - "revisar" quando houver ambiguidade relevante
   - "sem_variacao" quando variacao estiver vazia
22. Preserve exatamente o id_linha recebido.
23. Retorne um item para cada item de entrada.
24. Responda apenas no schema fornecido.

Exemplos:
nome_base: BROCA VIDEA SDS PLUS IRWIN
variacao: 10,0 X 16
=> medida: 10,0X16

nome_base: ABRACADEIRA NYLON
variacao: 200MM PRETA
=> medida: 200MM
=> cor: PRETA

nome_base: TORNEIRA METAL
variacao: 1/2 CROMADA
=> medida: 1/2
=> acabamento: CROMADA

nome_base: TOMADA
variacao: 2P+T 10A
=> tipo: 2P+T 10A

nome_base: PLACA TOMADA
variacao: 2 MODULOS CEGA REDONDO
=> tipo: 2 MODULOS CEGA REDONDO

nome_base: LAMPADA LED
variacao: 9W 6500K 806LM
=> potencia_watts: 9W
=> temperatura_cor: 6500K
=> lumens: 806LM

nome_base: DISCO LIXA
variacao: GRAO 120 REDONDO
=> granulacao: 120
=> formato: REDONDO

nome_base: CIMENTO
variacao: 5KG
=> peso: 5KG
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
# COLUNAS DE RESULTADO
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
    "status_extracao",
    "motivo_extracao",
    "modo_classificacao_variacao",
]

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def garantir_colunas(df: pd.DataFrame) -> pd.DataFrame:
    for col in COLUNAS_RESULTADO:
        if col not in df.columns:
            df[col] = None
    return df

def linha_processada(row: pd.Series) -> bool:
    valor = row.get("modo_classificacao_variacao")
    return pd.notna(valor) and str(valor).strip() != ""

def salvar_checkpoint(df: pd.DataFrame) -> None:
    with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        if "status_extracao" in df.columns:
            df[df["status_extracao"] == "revisar"].to_excel(
                writer,
                index=False,
                sheet_name="revisar_variacoes"
            )
            df[df["status_extracao"] == "sem_variacao"].to_excel(
                writer,
                index=False,
                sheet_name="sem_variacao"
            )



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
        df.at[idx, "status_extracao"] = "revisar" if variacao else "sem_variacao"
        df.at[idx, "motivo_extracao"] = f"Erro no lote: {erro}"
        df.at[idx, "modo_classificacao_variacao"] = "erro_lote"

# =========================================================
# CHAMADA DA API
# =========================================================

def enviar_lote_api(lote: List[Dict[str, Any]]) -> Dict[str, Any]:
    response = client.responses.create(
        model=MODELO,
        instructions=INSTRUCOES,
        input=f"Itens para classificar:\n{json.dumps(lote, ensure_ascii=False)}",
        text={
            "format": {
                "type": "json_schema",
                "name": "classificacao_variacoes",
                "schema": SCHEMA,
                "strict": True
            }
        }
    )
    return json.loads(response.output_text)

# =========================================================
# PROCESSAMENTO PRINCIPAL
# =========================================================

def processar_planilha() -> None:
    caminho_base = ARQUIVO_SAIDA if os.path.exists(ARQUIVO_SAIDA) else ARQUIVO_ENTRADA

    if not os.path.exists(caminho_base):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_base}")

    if caminho_base == ARQUIVO_SAIDA:
        df = pd.read_excel(caminho_base, sheet_name="Sheet1")
    else:
        try:
            df = pd.read_excel(caminho_base, sheet_name=ABA_ENTRADA)
        except Exception:
            df = pd.read_excel(caminho_base)

    if COLUNA_NOME_BASE not in df.columns:
        raise ValueError(
            f"Coluna '{COLUNA_NOME_BASE}' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    if COLUNA_VARIACAO not in df.columns:
        raise ValueError(
            f"Coluna '{COLUNA_VARIACAO}' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    df = garantir_colunas(df)
    REPROCESSAR_OUTRA_VARIACAO = True

    if REPROCESSAR_OUTRA_VARIACAO:
        for i in range(len(df)):
            outra = str(df.at[i, "outra_variacao"]).strip() if pd.notna(df.at[i, "outra_variacao"]) else ""

            if outra:
                df.at[i, "modo_classificacao_variacao"] = None
    lotes = montar_lotes_pendentes(df)
    if MAX_LOTES is not None:
        lotes = lotes[:MAX_LOTES]

    total_lotes = len(lotes)

    if total_lotes == 0:
        print("Nenhum lote pendente. Tudo já foi classificado.")
        salvar_checkpoint(df)
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
                df.at[idx, "status_extracao"] = item["status_extracao"]
                df.at[idx, "motivo_extracao"] = item["motivo_extracao"]
                df.at[idx, "modo_classificacao_variacao"] = "api_lote"

                print(
                    f"[linha {idx}] "
                    f"VAR='{df.at[idx, COLUNA_VARIACAO]}' -> "
                    f"tipo='{item['tipo']}' | medida='{item['medida']}' | "
                    f"potencia='{item['potencia_watts']}' | lumens='{item['lumens']}'"
                )

            salvar_checkpoint(df)
            print(f"Lote {n_lote} salvo com sucesso em {ARQUIVO_SAIDA}.")
            time.sleep(PAUSA_ENTRE_LOTES)

        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            print(f"Erro no lote {n_lote}: {erro}")
            preencher_fallback(df, indices, erro)
            salvar_checkpoint(df)
            print(f"Lote {n_lote} salvo como revisão manual.")

    print(f"\nConcluído. Arquivo salvo em: {ARQUIVO_SAIDA}")

# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    processar_planilha()
