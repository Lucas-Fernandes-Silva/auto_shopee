import json
import os
import shutil
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI

# =========================================================
# CONFIGURAÇÕES
# =========================================================

ARQUIVO_ENTRADA = "/home/lucas-silva/auto_shopee/planilhas/input/produtos_revisados.xlsx"
ARQUIVO_SAIDA = "produtos_com_embalagem.xlsx"
ABA_ENTRADA = "processados"

MODELO = "gpt-4.1-mini"
TAMANHO_LOTE = 10
PAUSA_ENTRE_LOTES = 1.0

# 1 = testa só 1 lote / None = processa tudo
MAX_LOTES = None

COLUNAS_CONTEXTO = [
    "produto",
    "descricao_original",
    "descricao_limpa",
    "nome_base",
    "variacao",
    "variacao_1_nome",
    "variacao_1_valor",
    "variacao_2_nome",
    "variacao_2_valor",
    "categoria",
]

COLUNAS_EMBALAGEM = ["Largura", "Altura", "Comprimento", "Peso"]

# =========================================================
# CLIENTE OPENAI
# =========================================================

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Defina OPENAI_API_KEY antes de rodar o script.")

client = OpenAI(api_key=api_key)

# =========================================================
# PROMPT
# =========================================================

INSTRUCOES = """
Você é um estimador de dimensões de embalagem para produtos de e-commerce.

Receberá uma lista JSON com produtos. Cada item pode conter:
- id_linha
- produto
- descricao_original
- descricao_limpa
- nome_base
- variacao
- variacao_1_nome
- variacao_1_valor
- variacao_2_nome
- variacao_2_valor
- categoria

Sua tarefa:
Inferir dimensões aproximadas da embalagem individual do produto em centímetros e peso em kg.

Campos de saída:
- id_linha
- largura_cm
- altura_cm
- comprimento_cm
- peso_kg
- status_embalagem
- confianca_embalagem
- motivo_embalagem

Regras:
1. Retorne medidas da embalagem pronta para envio, não apenas do produto cru.
2. Use valores realistas e conservadores para marketplace.
3. Sempre use centímetros para largura, altura e comprimento.
4. Sempre use kg para peso.
5. Não use texto nas medidas, apenas número.
6. Se o produto for fino, mesmo assim considere proteção/embalagem mínima.
7. Se houver peso explícito na variação, use como base e acrescente pequena margem de embalagem.
8. Se houver dimensão explícita na variação, use como base e acrescente folga de embalagem.
9. Se não houver informação suficiente, estime pela categoria e nome_base.
10. Se a inferência for incerta, marque status_embalagem como "revisar".
11. Preserve exatamente o id_linha recebido.
12. Retorne um item para cada item de entrada.
13. Responda apenas no schema.

Referências gerais:
- Itens pequenos como fita, tomada, plug, broca pequena: embalagem pequena.
- Itens longos como cabos, barras, mangueiras, ferramentas longas: comprimento maior.
- Itens pesados como cimento, argamassa, tinta, ferramentas grandes: peso maior.
- Produtos frágeis devem ter folga maior na embalagem.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "itens": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id_linha": {"type": "integer"},
                    "largura_cm": {"type": "number"},
                    "altura_cm": {"type": "number"},
                    "comprimento_cm": {"type": "number"},
                    "peso_kg": {"type": "number"},
                    "status_embalagem": {"type": "string", "enum": ["ok", "revisar"]},
                    "confianca_embalagem": {"type": "number"},
                    "motivo_embalagem": {"type": "string"},
                },
                "required": [
                    "id_linha",
                    "largura_cm",
                    "altura_cm",
                    "comprimento_cm",
                    "peso_kg",
                    "status_embalagem",
                    "confianca_embalagem",
                    "motivo_embalagem",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["itens"],
    "additionalProperties": False,
}

# =========================================================
# LEITURA / SALVAMENTO
# =========================================================


def arquivo_ok(caminho: str) -> bool:
    return os.path.exists(caminho) and os.path.getsize(caminho) > 0


def ler_excel_seguro(caminho: str, aba_preferida: Optional[str] = None) -> pd.DataFrame:
    xls = pd.ExcelFile(caminho, engine="openpyxl")
    abas = xls.sheet_names

    if aba_preferida and aba_preferida in abas:
        return pd.read_excel(caminho, sheet_name=aba_preferida, engine="openpyxl")

    return pd.read_excel(caminho, sheet_name=abas[0], engine="openpyxl")


def salvar_checkpoint_seguro(df: pd.DataFrame) -> None:
    temp = ARQUIVO_SAIDA + ".tmp.xlsx"
    backup = ARQUIVO_SAIDA + ".bak"

    with pd.ExcelWriter(temp, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False, sheet_name="processados")
        df[df["status_embalagem"] == "revisar"].to_excel(
            writer, index=False, sheet_name="revisar_embalagem"
        )

    if os.path.exists(ARQUIVO_SAIDA):
        shutil.copy2(ARQUIVO_SAIDA, backup)

    os.replace(temp, ARQUIVO_SAIDA)


# =========================================================
# AUXILIARES
# =========================================================


def garantir_colunas(df: pd.DataFrame) -> pd.DataFrame:
    for col in COLUNAS_EMBALAGEM:
        if col not in df.columns:
            df[col] = None

    extras = [
        "status_embalagem",
        "confianca_embalagem",
        "motivo_embalagem",
        "modo_embalagem",
    ]

    for col in extras:
        if col not in df.columns:
            df[col] = None

    return df


def vazio(valor) -> bool:
    if pd.isna(valor):
        return True
    return str(valor).strip() == ""


def precisa_processar(row: pd.Series) -> bool:
    # Só processa se alguma das 4 colunas estiver vazia
    faltando_dimensao = any(vazio(row.get(col)) for col in COLUNAS_EMBALAGEM)

    # Se já processou e não falta nada, pula
    if not faltando_dimensao:
        return False

    return True


def montar_lotes_pendentes(df: pd.DataFrame) -> List[List[int]]:
    pendentes = [i for i in range(len(df)) if precisa_processar(df.iloc[i])]
    return [pendentes[i : i + TAMANHO_LOTE] for i in range(0, len(pendentes), TAMANHO_LOTE)]


def montar_item_contexto(df: pd.DataFrame, idx: int) -> Dict[str, Any]:
    item = {"id_linha": int(idx)}

    for col in COLUNAS_CONTEXTO:
        if col in df.columns and pd.notna(df.at[idx, col]):
            item[col] = str(df.at[idx, col]).strip()  # type: ignore

    # valores existentes, caso tenha alguns preenchidos
    item["largura_atual"] = "" if vazio(df.at[idx, "Largura"]) else str(df.at[idx, "Largura"])  # type: ignore
    item["altura_atual"] = "" if vazio(df.at[idx, "Altura"]) else str(df.at[idx, "Altura"])  # type: ignore
    item["comprimento_atual"] = (  # type: ignore
        "" if vazio(df.at[idx, "Comprimento"]) else str(df.at[idx, "Comprimento"])
    )
    item["peso_atual"] = "" if vazio(df.at[idx, "Peso"]) else str(df.at[idx, "Peso"])  # type: ignore

    return item


def preencher_fallback(df: pd.DataFrame, indices: List[int], erro: str) -> None:
    for idx in indices:
        df.at[idx, "status_embalagem"] = "revisar"
        df.at[idx, "confianca_embalagem"] = 0
        df.at[idx, "motivo_embalagem"] = f"Erro no lote: {erro}"
        df.at[idx, "modo_embalagem"] = "erro_lote"


# =========================================================
# API
# =========================================================


def enviar_lote_api(lote: List[Dict[str, Any]]) -> Dict[str, Any]:
    response = client.responses.create(
        model=MODELO,
        instructions=INSTRUCOES,
        input=f"Produtos para inferir embalagem:\n{json.dumps(lote, ensure_ascii=False)}",
        text={
            "format": {
                "type": "json_schema",
                "name": "inferir_embalagem_produtos",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)


# =========================================================
# PROCESSAMENTO
# =========================================================


def carregar_base() -> pd.DataFrame:
    if arquivo_ok(ARQUIVO_SAIDA):
        return ler_excel_seguro(ARQUIVO_SAIDA, "processados")

    return ler_excel_seguro(ARQUIVO_ENTRADA, ABA_ENTRADA)


def processar_planilha() -> None:
    df = carregar_base()
    df = garantir_colunas(df)

    lotes = montar_lotes_pendentes(df)

    if MAX_LOTES is not None:
        lotes = lotes[:MAX_LOTES]

    total_lotes = len(lotes)

    if total_lotes == 0:
        print("Nenhuma linha pendente. Largura, Altura, Comprimento e Peso já estão preenchidos.")
        salvar_checkpoint_seguro(df)
        return

    for n_lote, indices in enumerate(lotes, start=1):
        lote = [montar_item_contexto(df, idx) for idx in indices]

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

                # Preenche somente o que estiver vazio
                if vazio(df.at[idx, "Largura"]):
                    df.at[idx, "Largura"] = item["largura_cm"]

                if vazio(df.at[idx, "Altura"]):
                    df.at[idx, "Altura"] = item["altura_cm"]

                if vazio(df.at[idx, "Comprimento"]):
                    df.at[idx, "Comprimento"] = item["comprimento_cm"]

                if vazio(df.at[idx, "Peso"]):
                    df.at[idx, "Peso"] = item["peso_kg"]

                df.at[idx, "status_embalagem"] = item["status_embalagem"]
                df.at[idx, "confianca_embalagem"] = item["confianca_embalagem"]
                df.at[idx, "motivo_embalagem"] = item["motivo_embalagem"]
                df.at[idx, "modo_embalagem"] = "api_lote"

                print(
                    f"[linha {idx}] "
                    f"{df.at[idx, 'Largura']}x{df.at[idx, 'Altura']}x{df.at[idx, 'Comprimento']} cm | "
                    f"{df.at[idx, 'Peso']} kg | {item['status_embalagem']}"
                )

            salvar_checkpoint_seguro(df)
            print(f"Lote {n_lote} salvo em {ARQUIVO_SAIDA}.")
            time.sleep(PAUSA_ENTRE_LOTES)

        except KeyboardInterrupt:
            print("\nInterrompido manualmente. Salvando progresso...")
            salvar_checkpoint_seguro(df)
            print("Progresso salvo.")
            raise

        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            print(f"Erro no lote {n_lote}: {erro}")
            preencher_fallback(df, indices, erro)
            salvar_checkpoint_seguro(df)

    print(f"\nConcluído. Arquivo salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    processar_planilha()
